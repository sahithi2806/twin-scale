# Data Center Digital Twin

A high-fidelity full-stack Digital Twin application for data center operations, monitoring **16 virtual server CPUs** in real time with thermal analytics, capacity tracking, and automated idle energy consolidation.

---

## 🏛️ System Architecture

```text
data-center-twin/
├── backend/
│   ├── main.py              # FastAPI application with CORS & REST endpoints
│   ├── database.py          # SQLite connection, schema init & 16-server seeding
│   ├── models.py            # Pydantic data schemas for telemetry & savings
│   ├── requirements.txt     # Python dependencies (fastapi, uvicorn, pydantic, httpx)
│   └── servers.db           # SQLite database storing the 16 virtual servers
├── frontend/
│   ├── index.html           # HTML template with Inter & JetBrains Mono fonts
│   ├── package.json         # React 19, Vite, Tailwind CSS v4, Lucide icons
│   ├── vite.config.js       # Vite build & dev server configuration
│   ├── postcss.config.js    # Tailwind PostCSS configuration
│   └── src/
│       ├── main.jsx         # React application entry point
│       ├── App.jsx          # React Router setup (/ and /dashboard)
│       ├── index.css        # Techy light theme, chip pins & glassmorphic styling
│       ├── services/
│       │   └── api.js       # API client with graceful fallback dataset
│       ├── components/
│       │   ├── Navbar.jsx               # Navigation bar & backend status badge
│       │   ├── CpuChip.jsx              # CPU component with 100% vs 20% opacity logic
│       │   ├── ServerDetailPanel.jsx    # Metric telemetry panel & state toggle
│       │   ├── EnergySavingsModal.jsx   # Breakdown modal for energy & cost savings
│       │   └── StatsBar.jsx             # Prominent clickable Energy Saved card & KPIs
│       └── pages/
│           ├── LandingPage.jsx          # Digital Twin overview & prominent CTA
│           └── DashboardPage.jsx        # 4×4 interactive CPU grid & telemetry
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Node.js** v18+ (tested on v22)
- **Python** 3.10+ (tested on 3.12)

---

### 2. Backend Setup (FastAPI + SQLite)

Open a terminal in the root directory:

```bash
cd backend

# Install dependencies
python -m pip install -r requirements.txt

# Start the FastAPI server (runs on http://localhost:8000)
python -m uvicorn main:app --reload --port 8000
```

The SQLite database (`servers.db`) will automatically initialize and populate 16 virtual server records on startup.

**Interactive API Documentation**:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 3. Frontend Setup (React + Vite + Tailwind CSS)

Open a second terminal in the root directory:

```bash
cd frontend

# Install dependencies (already prepared)
npm install

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

Visit **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🔌 API Endpoints (FastAPI)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/servers` | Returns list of all 16 virtual servers with `server_id`, `capacity`, `current_utilization`, `status`, `rack_id`, `temperature_c`, and `power_draw_w` |
| `GET` | `/api/servers/{server_id}` | Returns real-time telemetry for a specific server node |
| `POST` | `/api/servers/{server_id}/toggle-status` | Toggles node state between `active` and `idle`, adjusting utilization and power draw |
| `PATCH` | `/api/servers/{server_id}` | Updates specific telemetry attributes (utilization, active workloads, status) |
| `GET` | `/api/energy-savings` | Returns breakdown of energy conserved (kWh), cost savings ($), carbon offset (kg CO₂), and PUE ratio (1.15) |
| `POST` | `/api/servers/reset` | Resets all 16 servers back to default baseline |
| `GET` | `/api/health` | Health check probe |

### Example Server Payload:
```json
{
  "id": 1,
  "server_id": "SRV-01",
  "capacity": "64 vCPU / 256 GB RAM",
  "current_utilization": 84.5,
  "status": "active",
  "rack_id": "RACK-A1",
  "temperature_c": 58.2,
  "power_draw_w": 410.0,
  "active_workloads": 19
}
```

---

## 🖥️ Frontend UI Features & Logic

1. **Clean, Light 'Techy' Theme**:
   - Palette: Clean crisp whites (`#ffffff`), subtle grays (`#f8fafc`, `#f1f5f9`), soft blue (`#0284c7`, `#38bdf8`), and soft green/emerald accents (`#10b981`, `#059669`).
   - Circuit-inspired grid pattern, metallic CPU heat spreaders, and gold/silver perimeter socket pins.

2. **React Router Architecture**:
   - `/`: **Landing Page** with digital twin system overview, mini visualizer preview, and prominent **"Go to CPU Dashboard"** button.
   - `/dashboard`: **Interactive CPU Utilization Page**.

3. **CPU Utilization Page Logic**:
   - **4×4 Grid Layout**: 16 realistic CPU chips organized across 4 data center racks (Rack A through D).
   - **Utilization Gauges**: Radial SVG meters and percentage metrics on every CPU shape.
   - **Focus & Opacity Isolation**:
     - Clicking a CPU keeps the selected CPU at **100% opacity** (with subtle zoom and highlight ring).
     - **All other CPUs automatically drop to 20% opacity (80% transparent)**.
     - Clicking again or clicking "View All Servers" restores all 16 CPUs to 100% opacity.
   - **Detailed Telemetry Panel**:
     - Displays server ID, hardware capacity, thermal sensor reading, power wattage, active container workloads, and a **"Power On / Consolidate"** button that updates the SQLite backend.
   - **Clickable 'Energy Saved' Card**:
     - Positioned prominently at the top of the dashboard.
     - Clicking opens a detailed breakdown modal displaying monthly kWh saved, utility dollar savings, carbon offset, and PUE comparison (1.15 vs 1.58 industry average).
   - **Live Simulation Toggle**: Real-time minute-by-minute fluctuation simulator.
