# DC-Twin: Data Center Digital Twin for Energy-Aware Workload Optimization

A 16-server data center simulator. Synthetic, seeded workloads are scheduled by **Min-Min**, a
**power-aware** best-fit heuristic, or a **DQN** agent; the backend measures energy, completion
time, CPU utilization and SLA violations, stores every run in SQLite, and the React dashboard
shows the results. Every number on screen is measured by the simulator. Nothing is hardcoded.

## Running the application

The app has two processes: the **backend** (FastAPI on port 8000) and the **frontend** (Vite dev
server on port 5173). The frontend calls `http://localhost:8000`, so the backend must use port 8000.

### 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.12 or newer (tested on 3.14) | `python --version` |
| Node.js | 20.19+ or 22.12+ (required by Vite 8) | `node --version` |
| npm | comes with Node | `npm --version` |
| Git | any | `git --version` |

No GPU, database server or Docker is needed. SQLite ships with Python.

### 2. Get the code

```bash
git clone <repo-url> twin-scale
cd twin-scale
git checkout sprint-3        # until it is merged into main
```

### 3. Backend setup (one time)

Open a terminal in `twin-scale/backend`.

**Windows (PowerShell or cmd):**
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-dev.txt
```

**Windows (Git Bash):** same commands, but activate with `source .venv/Scripts/activate`.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-dev.txt
```

Install torch first, from the CPU index. Otherwise pip may download the much larger CUDA build.
`requirements.txt` holds the runtime packages (fastapi, uvicorn, pydantic, numpy, torch), and
`requirements-dev.txt` adds pytest and httpx for the tests.

Check the install (prints the test summary, about 20 s):
```bash
pytest -q
```

### 4. Start the backend

With the virtual environment active, in `twin-scale/backend`:

```bash
uvicorn main:app --reload --port 8000
```

You should see `Application startup complete.` Then check:
- http://localhost:8000/api/health: `{"status":"healthy","server_count":16,...}`
- http://localhost:8000/docs: interactive API documentation (Swagger UI)

On the first start, `backend/servers.db` is created and filled with the 16 servers. The file is
not tracked in git.

`--reload` restarts the server when a backend file changes, and any run in progress at that
moment is marked `failed`. Leave out `--reload` if you are not editing backend code.

### 5. Frontend setup and start

Open a **second** terminal in `twin-scale/frontend`:

```bash
npm ci          # one time: installs exact versions from package-lock.json
npm run dev
```

Open http://localhost:5173. The navbar should show **FastAPI: Live**. If it shows
**Backend offline**, the backend is not running on port 8000.

### 6. First walkthrough

1. **CPU Dashboard**: pick a scheduler (Min-Min, Power-aware or DQN) and press **Run Simulation**.
   A progress bar appears; when the run is done the 4×4 grid shows each server's result.
   Servers that slept for most of the run show a dashed border and a moon icon.
2. Click a CPU chip to inspect it (the others fade to 20%). **Toggle** in the side panel puts that
   server to sleep or wakes it.
3. **Compare Results**: press **Run comparison**. All three schedulers run on the same 10 held-out
   seeds (a few seconds), and you get four bar charts with ±std error bars and a summary table.
4. Back on the dashboard, the **Energy Saved** card now shows DQN's measured saving vs Min-Min.
   Click it for the per-server breakdown and the SLA cost of the saving.

### 7. Production build of the frontend (optional)

```bash
cd frontend
npm run build      # output in frontend/dist
npm run preview    # serves the build on http://localhost:4173
```

The backend still has to run on port 8000.

### 8. Useful commands

| Task | Command (from `backend/`, venv active) |
|---|---|
| Run backend tests | `pytest -q` |
| Held-out evaluation table | `python train_dqn.py --eval` |
| Retrain the DQN | `python train_dqn.py` (about 9 min) |
| Reset all data | stop the backend, delete `servers.db`, start again |
| Reset only the 16 servers | `curl -X POST localhost:8000/api/servers/reset` |
| Lint the frontend | `npm run lint` (from `frontend/`) |

### 9. Configuration (environment variables)

| Variable | Default | Effect |
|---|---|---|
| `DCTWIN_DB_PATH` | `backend/servers.db` | SQLite file to use (the tests point this at a temporary file) |
| `DCTWIN_DQN_WEIGHTS` | `backend/models/dqn.pt` | DQN weights the API loads |
| `DCTWIN_SLA_SLACK` | `1.5` | Default SLA deadline slack (requests can override it) |

Set them before starting the backend, e.g. PowerShell `$env:DCTWIN_SLA_SLACK = "2.0"`,
bash `export DCTWIN_SLA_SLACK=2.0`.

### 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Navbar says **Backend offline** / "Backend unreachable" banner | Start the backend on port 8000 and press the refresh button on the dashboard. |
| `Address already in use` / port 8000 busy | Stop the other process on 8000. The frontend expects 8000, so don't pick another port. |
| `ModuleNotFoundError: torch` (or fastapi) | Activate the venv (`.venv\Scripts\activate`) before `uvicorn` / `pytest`. |
| `pip install torch` finds no version | Use Python 3.12-3.14 64-bit; check `python -c "import struct; print(struct.calcsize('P')*8)"` prints 64. |
| DQN option is greyed out, "Train first" | `backend/models/dqn.pt` is missing or was trained for another configuration. Run `python train_dqn.py`. |
| `npm ci` or `npm run dev` fails with an engine/version error | Upgrade Node to 20.19+ or 22.12+. |
| A run stays at "running" | The backend restarted mid-run. Restart it once more (unfinished runs become `failed`) and run again. |
| Old or odd data after pulling new code | Stop the backend and delete `backend/servers.db`. An older schema version is also dropped automatically on start. |

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
| POST | `/api/servers/reset` | Restore the 16 servers to their initial state (runs are kept) |
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
