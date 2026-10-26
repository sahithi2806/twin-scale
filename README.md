# DC-Twin: Data Center Digital Twin for Energy-Aware Workload Optimization

A 16-server data center simulator. Synthetic, seeded workloads are scheduled by **Min-Min**, a
**power-aware** best-fit heuristic, or a **DQN** agent; the backend measures energy, completion
time, CPU utilization and SLA violations, stores every run in SQLite, and the React dashboard
shows the results. Every number on screen is measured by the simulator. Nothing is hardcoded.

## Setup

Requirements: Python 3.12+ (tested on 3.14), Node 20+.

```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU build first
pip install -r requirements-dev.txt                                  # runtime deps + pytest/httpx
uvicorn main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm ci
npm run dev                       # http://localhost:5173
```

`backend/servers.db` is created on first start and is not tracked in git. Delete it to start over.
`pytest` runs the backend tests (from `backend/`).

## Train the DQN

Trained weights are committed in `backend/models/dqn.pt`, so the DQN works out of the box.
To retrain (about 9 minutes on one CPU core):

```bash
cd backend
python train_dqn.py                # 6 epochs over training seeds 0-99
python train_dqn.py --epochs 2     # quicker
python train_dqn.py --eval         # held-out table for every policy (no training)
```

- Writes `models/dqn.pt` and the reward curve `models/dqn_rewards.csv`
  (`episode, epoch, seed, epsilon, reward, energy_kwh, sla_violations, overload, mean_loss`).
- After each epoch the greedy policy is scored on validation seeds 100-104, and the best epoch
  is saved, not the last one. DQN training is unstable and later epochs can be much worse.
- The API **only loads** these weights. If the file is missing, or was trained for a different
  engine configuration (fleet, power model, state encoding, reward weights), requests for `dqn`
  return **503** with the reason, and `/api/compare` skips DQN. The API never trains.

Seed sets never overlap: training 0-99, validation 100-104, evaluation 1000+ (enforced in code).

## Run comparisons

From the UI: **Compare Results** in the navbar, then *Run comparison*.

From the API:

```bash
curl -X POST localhost:8000/api/compare -H "content-type: application/json" \
     -d '{"n_seeds": 10, "num_tasks": 200, "sleep_enabled": true}'
curl localhost:8000/api/compare/latest
```

Every available policy runs on the same held-out seeds (default 10, starting at 1000). The
response gives mean ± std for energy (kWh), completion time (s), average CPU utilization (%) and
SLA violations, plus savings as a percentage of Min-Min, per-server energy, idle/overloaded
server counts, and DQN's saving vs Min-Min with its SLA cost.

### Results (seeds 1000-1009, 200 tasks, 3 tasks/s, slack 1.5)

| Sleep | Policy | Energy (kWh) | Completion (s) | CPU util. (%) | SLA violations | Energy vs Min-Min |
|---|---|---|---|---|---|---|
| on | Min-Min | 0.0430 ± 0.0021 | 97.7 ± 5.9 | 9.4 ± 0.7 | 0.0 ± 0.0 | baseline |
| on | Power-aware | 0.0274 ± 0.0014 | 97.7 ± 5.9 | 30.3 ± 3.2 | 0.2 ± 0.4 | −36.1% |
| on | DQN | 0.0269 ± 0.0016 | 99.3 ± 6.4 | 21.2 ± 1.7 | 7.9 ± 2.0 | −37.4% |
| off | Min-Min | 0.0447 ± 0.0022 | 97.7 ± 5.9 | 8.9 ± 0.6 | 0.0 ± 0.0 | baseline |
| off | Power-aware | 0.0475 ± 0.0024 | 97.7 ± 5.9 | 8.9 ± 0.6 | 0.0 ± 0.0 | +6.3% |
| off | DQN | 0.0498 ± 0.0027 | 109.1 ± 6.9 | 7.9 ± 0.4 | 49.0 ± 24.5 | +11.5% |

What this shows:
- **The savings come from sleep.** With sleep off, power is linear in busy cores, so moving work
  between servers cannot save energy, and neither alternative beats Min-Min.
- **Power-aware is the stronger energy-aware policy.** It gets almost all of DQN's saving with
  almost no SLA misses.
- **DQN trades deadlines for energy** (about 8 late tasks out of 200). It was trained with sleep
  on and does badly outside that setting.

## Definitions

**SLA violation** (`backend/config.py`, used everywhere):
`deadline = arrival_time + sla_slack × ideal_exec_time`, where
`ideal_exec_time = workload_MI / (vCPUs × 2500 MIPS)`. A task violates its SLA when it finishes
after its deadline. `sla_slack` defaults to 1.5 (env `DCTWIN_SLA_SLACK`) and can be set per
request (1.0-10.0).

**Execution model** (same for every policy): a server runs tasks concurrently while their
vCPUs fit in its cores. Further tasks wait in that server's FIFO queue. Time advances in 1 s ticks.

**Power model** (W), utilization `u` = busy cores / total cores:

| State | Power |
|---|---|
| on | `P = P_idle + (P_max − P_idle) × u` |
| waking | `P_idle`, for `WAKE_DELAY_S` = 5 s before work can start |
| sleep | `P_SLEEP_W` = 8 W |

| Cores | P_idle | P_max |
|---|---|---|
| 32 | 50 | 220 |
| 64 | 72 | 335 |
| 96 | 88 | 410 |
| 128 | 105 | 490 |

With sleep enabled, a server with no work for `IDLE_TIMEOUT_S` = 10 s goes to sleep. Sending a
task to a sleeping server wakes it. With sleep disabled, servers never sleep. Energy is IT energy
only (no PUE multiplier) and is integrated every tick.

**CPU utilization** in comparisons is busy core-seconds / awake core-seconds: how full the
servers that are powered on are.

**Server flags** (analytics, read from SQLite): *idle* if asleep or awake without work for more
than 80% of the run; *overloaded* if above 85% utilization for more than 20% of the run.

## Schedulers

- **Min-Min**: each tick, among newly arrived tasks, repeatedly place the (task, server) pair with
  the earliest estimated completion; ties go to the least-loaded server (spreads load).
- **Power-aware**: place on an awake server that can start the task now under 85% utilization,
  preferring busy servers, the tightest fit, then the lowest P_max per core; otherwise the
  earliest-finishing awake server if it meets the deadline; otherwise wake the most efficient
  sleeping server.
- **DQN**: MLP 50 → 128 → 128 → 16 (PyTorch, CPU), replay buffer, target network, Double-DQN
  target, ε-greedy. State: per-server utilization, power state and queue length, plus the next
  task's vCPU demand and time to deadline. Action: the server for the next task. Reward:
  `−(Wh used) − 2 × SLA violations − 1 × overload above 85%`. A violation is charged at dispatch:
  start times are fully determined then, which `tests/test_env.py` checks.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Status and latest run |
| GET | `/api/servers`, `/api/servers/{id}` | Server fleet (snapshot of the latest single run) |
| POST | `/api/servers/{id}/toggle-status` | Manually put a server to sleep or wake it |
| GET | `/api/policies` | Which schedulers can run (DQN needs weights) |
| POST | `/api/simulations` | Start a run; returns `202 {run_id, status: "queued"}` immediately |
| GET | `/api/simulations/{id}` | Status (`queued`/`running`/`done`/`failed`), progress; results and analytics when done |
| GET | `/api/simulations/latest` | Latest finished single run |
| POST | `/api/compare` | Run every policy on the same held-out seeds |
| GET | `/api/compare/latest` | Latest comparison, rebuilt from SQLite |

Runs execute as FastAPI BackgroundTasks in the API process. A restart marks unfinished runs as
`failed`. Running several API workers would need a shared job queue.

## Storage

SQLite tables `servers`, `simulations`, `step_metrics`, `server_stats`. `step_metrics` and
`server_stats` reference `simulations.run_id` (foreign keys enforced, cascade on delete). Each
run's results are written in one transaction. Runs that belong to a comparison carry its
`comparison_id`.

## Layout

```text
backend/
  main.py            FastAPI app
  config.py          SLA definition, power model, engine and reward constants
  simulation.py      Workload generator, servers, time-stepped DataCenter engine
  policies.py        Min-Min, power-aware, load-only DQN policy
  rl/env.py          Gym-style environment over the same engine
  rl/dqn_agent.py    PyTorch DQN
  train_dqn.py       Offline training and --eval
  evaluation.py      Held-out seeds, mean ± std, savings vs Min-Min
  analytics.py       Server flags and comparison summaries from SQLite
  database.py        Schema and queries
  schemas.py         Request/response models
  models/            Trained weights and reward log
  tests/             pytest suite
frontend/src/
  pages/             LandingPage, DashboardPage (4×4 CPU grid), ComparePage
  components/        CpuChip, StatsBar, EnergySavingsModal, SimulationControlPanel, ...
  services/api.js    API client
```
