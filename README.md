# Data Center Digital Twin & Simulation Engine

A high-fidelity full-stack Digital Twin application for data center operations. Monitors **16 virtual server CPUs** in real time with thermal analytics, capacity tracking, synthetic workload generation, **Min-Min scheduling**, and automated energy optimization.

---

## 🏛️ System Architecture

```text
data-center-twin/
├── backend/
│   ├── main.py                     # FastAPI app with POST /api/simulations, telemetry & reset
│   ├── simulation.py               # VirtualServer model, WorkloadGenerator, MinMinScheduler, SimulationEngine
│   ├── database.py                 # SQLite schema (servers, simulations, step_metrics, server_stats) & atomic transactions
│   ├── models.py                   # Pydantic schemas (SimulationRequest, SimulationResponse, Server, Telemetry)
│   ├── requirements.txt            # Python dependencies (fastapi, uvicorn, pydantic, httpx)
│   └── servers.db                  # SQLite database storing server states & simulation history
├── frontend/
│   ├── index.html                  # HTML template with Inter & JetBrains Mono fonts
│   ├── package.json                # React 19, Vite, Tailwind CSS v4, Lucide icons
│   ├── vite.config.js              # Vite build configuration
│   ├── postcss.config.js           # PostCSS configuration for Tailwind v4
│   └── src/
│       ├── main.jsx                # React application entry point
│       ├── App.jsx                 # React Router setup (/ and /dashboard)
│       ├── index.css               # Clean light techy theme, chip socket pins & glassmorphic panels
│       ├── services/
│       │   └── api.js              # API client (fetchServers, runSimulation, toggleStatus, etc.)
│       ├── components/
│       │   ├── Navbar.jsx                  # Header with live FastAPI status badge & energy shortcut
│       │   ├── CpuChip.jsx                 # CPU component with 100% vs 20% opacity isolation logic
│       │   ├── ServerDetailPanel.jsx       # Real-time metrics panel, flags, & Active/Idle toggle
│       │   ├── SimulationControlPanel.jsx  # Task slider, seed input, & 'Start Simulation' button
│       │   ├── EnergySavingsModal.jsx      # Modal breakdown of kWh saved, cost, and PUE
│       │   └── StatsBar.jsx                # Prominent clickable 'Energy Saved' card & KPIs
│       └── pages/
│           ├── LandingPage.jsx             # Digital Twin overview & 'Go to CPU Dashboard' button
│           └── DashboardPage.jsx           # 4×4 interactive CPU grid & dynamic simulation visualization
└── README.md
```

---

## ⚡ Sprint 2 Core Simulation Engine

### 1. Database Schema (SQLite)
- `simulations`: Records each run (`run_id`, `policy`, `parameters`, `total_tasks`, `makespan`, `total_energy_kwh`, `baseline_energy_kwh`, `energy_saved_kwh`, `created_at`).
- `step_metrics`: Discrete time-series intervals (`step`, `timestamp`, `server_id`, `utilization`, `energy`).
- `server_stats`: Aggregated node statistics (`server_id`, `avg_utilization`, `energy_consumed`, `total_tasks_assigned`, `flags`).
- `servers`: Maintained with the latest simulation state (`current_utilization`, `status`, `temperature_c`, `power_draw_w`, `active_workloads`).
- **Transaction Guarantee**: All tables are written within a **single atomic SQLite transaction** using Python's `with conn:` context manager.

### 2. Virtual Server Model & Power Model
- **VirtualServer Class**: Tracks core count (32 to 128 vCPUs), MIPS processing speed, dynamic task queue, and ready time.
- **Linear Power Model**:
  $$P(u) = P_{\text{idle}} + (P_{\text{max}} - P_{\text{idle}}) \times \frac{u}{100}$$
  Nodes in standby sleep mode consume reduced base power (~50–85W), while loaded nodes scale up to 220–490W.
- **Thermal Response**:
  $$T(u) = 28^\circ\text{C} + \frac{u}{100} \times 36^\circ\text{C}$$

### 3. Workload Generator
- Generates synthetic computational tasks with multi-modal requirements:
  - 25% small batch / web requests
  - 55% standard enterprise microservices
  - 20% heavy analytical / AI compute jobs
- Uses a **fixed random seed** (`seed=42` by default) to ensure deterministic, fair comparisons across runs.

### 4. Baseline Scheduler: Min-Min Algorithm
1. Computes expected completion time $CT(T_i, S_j) = \text{ready\_time}[S_j] + \frac{\text{workload}}{\text{speed}}$ for each unmapped task $T_i$ on every server $S_j$.
2. Identifies the server that minimizes completion time for each task: $S^*(T_i) = \arg\min_j CT(T_i, S_j)$.
3. Selects the task with the overall minimum completion time: $T^* = \arg\min_{T_i} CT(T_i, S^*(T_i))$.
4. Assigns $T^*$ to $S^*(T^*)$, updates the server's ready time, and repeats until all tasks are scheduled.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/simulations` | Executes Min-Min simulation with configurable tasks & seed, persists in SQLite transaction, and returns results |
| `GET` | `/api/simulations/latest` | Returns the most recent completed simulation run |
| `GET` | `/api/simulations/{run_id}` | Retrieves full simulation run details, server stats, and step metrics |
| `GET` | `/api/servers` | Returns telemetry for all 16 virtual servers |
| `GET` | `/api/servers/{server_id}` | Retrieves specific virtual server metrics |
| `POST` | `/api/servers/{server_id}/toggle-status` | Toggles node state between `active` and `idle` |
| `GET` | `/api/energy-savings` | Returns breakdown of energy saved, cost savings ($), carbon offset, and PUE |
| `POST` | `/api/servers/reset` | Resets all 16 servers to the default baseline |
| `GET` | `/api/health` | Health check probe and active database status |

---

## 🚀 Quick Start Guide

### 1. Start FastAPI Backend Server
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```
- API Endpoint: `http://localhost:8000/api/servers`
- Interactive Swagger UI: `http://localhost:8000/docs`

### 2. Start React + Vite Frontend
```bash
cd frontend
npm run dev
```
- Application URL: `http://localhost:5173`

---

## 🖥️ Frontend UI Features & Logic

1. **Simulation Control Panel**:
   - Set task count (slider or quick presets: 50, 100, 200, 400 tasks).
   - Configure random seed (with one-click "Randomize" generator).
   - "Start Simulation" button with animated execution spinner.
2. **Dynamic Data Binding**:
   - On completion of `POST /api/simulations`, the 4×4 CPU grid immediately updates to show final node utilization, status, and temperatures.
3. **Opacity Focus Isolation**:
   - Clicking a CPU isolates that server at **100% opacity**, while all other 15 CPUs become dimmed to **20% opacity**.
4. **Detailed Server Telemetry**:
   - Displays mapped tasks, average utilization, energy consumed (kWh), and scheduler flags (`OPTIMAL_LOAD`, `HOTSPOT_HIGH_LOAD`, `IDLE_CONSOLIDATED`).
5. **Real-time 'Energy Saved' Metrics**:
   - Top card updates directly with the simulation run's energy savings and cost reduction compared to an unmanaged baseline.
