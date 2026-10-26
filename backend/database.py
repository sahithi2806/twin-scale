import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "servers.db")

INITIAL_16_SERVERS = [
    {
        "server_id": "SRV-01",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 84.5,
        "status": "active",
        "rack_id": "RACK-A1",
        "temperature_c": 58.2,
        "power_draw_w": 410.0,
        "active_workloads": 19
    },
    {
        "server_id": "SRV-02",
        "capacity": "128 vCPU / 512 GB RAM",
        "current_utilization": 92.1,
        "status": "active",
        "rack_id": "RACK-A1",
        "temperature_c": 64.7,
        "power_draw_w": 485.5,
        "active_workloads": 31
    },
    {
        "server_id": "SRV-03",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 61.3,
        "status": "active",
        "rack_id": "RACK-A2",
        "temperature_c": 49.8,
        "power_draw_w": 330.0,
        "active_workloads": 14
    },
    {
        "server_id": "SRV-04",
        "capacity": "32 vCPU / 128 GB RAM",
        "current_utilization": 0.0,
        "status": "idle",
        "rack_id": "RACK-A2",
        "temperature_c": 33.1,
        "power_draw_w": 75.0,
        "active_workloads": 0
    },
    {
        "server_id": "SRV-05",
        "capacity": "96 vCPU / 384 GB RAM",
        "current_utilization": 77.8,
        "status": "active",
        "rack_id": "RACK-B1",
        "temperature_c": 56.4,
        "power_draw_w": 380.0,
        "active_workloads": 22
    },
    {
        "server_id": "SRV-06",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 43.2,
        "status": "active",
        "rack_id": "RACK-B1",
        "temperature_c": 44.0,
        "power_draw_w": 280.0,
        "active_workloads": 9
    },
    {
        "server_id": "SRV-07",
        "capacity": "128 vCPU / 512 GB RAM",
        "current_utilization": 89.0,
        "status": "active",
        "rack_id": "RACK-B2",
        "temperature_c": 62.9,
        "power_draw_w": 465.0,
        "active_workloads": 28
    },
    {
        "server_id": "SRV-08",
        "capacity": "32 vCPU / 128 GB RAM",
        "current_utilization": 0.0,
        "status": "idle",
        "rack_id": "RACK-B2",
        "temperature_c": 32.5,
        "power_draw_w": 70.0,
        "active_workloads": 0
    },
    {
        "server_id": "SRV-09",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 71.4,
        "status": "active",
        "rack_id": "RACK-C1",
        "temperature_c": 53.6,
        "power_draw_w": 360.0,
        "active_workloads": 17
    },
    {
        "server_id": "SRV-10",
        "capacity": "96 vCPU / 384 GB RAM",
        "current_utilization": 82.6,
        "status": "active",
        "rack_id": "RACK-C1",
        "temperature_c": 59.1,
        "power_draw_w": 420.0,
        "active_workloads": 24
    },
    {
        "server_id": "SRV-11",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 0.0,
        "status": "idle",
        "rack_id": "RACK-C2",
        "temperature_c": 34.0,
        "power_draw_w": 80.0,
        "active_workloads": 0
    },
    {
        "server_id": "SRV-12",
        "capacity": "128 vCPU / 512 GB RAM",
        "current_utilization": 95.3,
        "status": "active",
        "rack_id": "RACK-C2",
        "temperature_c": 67.2,
        "power_draw_w": 498.0,
        "active_workloads": 35
    },
    {
        "server_id": "SRV-13",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 68.7,
        "status": "active",
        "rack_id": "RACK-D1",
        "temperature_c": 51.5,
        "power_draw_w": 345.0,
        "active_workloads": 16
    },
    {
        "server_id": "SRV-14",
        "capacity": "32 vCPU / 128 GB RAM",
        "current_utilization": 0.0,
        "status": "idle",
        "rack_id": "RACK-D1",
        "temperature_c": 31.8,
        "power_draw_w": 68.0,
        "active_workloads": 0
    },
    {
        "server_id": "SRV-15",
        "capacity": "96 vCPU / 384 GB RAM",
        "current_utilization": 79.9,
        "status": "active",
        "rack_id": "RACK-D2",
        "temperature_c": 57.8,
        "power_draw_w": 395.0,
        "active_workloads": 21
    },
    {
        "server_id": "SRV-16",
        "capacity": "64 vCPU / 256 GB RAM",
        "current_utilization": 54.1,
        "status": "active",
        "rack_id": "RACK-D2",
        "temperature_c": 47.3,
        "power_draw_w": 310.0,
        "active_workloads": 13
    }
]

SCHEMA_VERSION = 2
RUN_STATUSES = ("queued", "running", "done", "failed")


def db_path() -> str:
    return os.environ.get("DCTWIN_DB_PATH", DEFAULT_DB_PATH)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT UNIQUE NOT NULL,
    capacity TEXT NOT NULL,
    rack_id TEXT NOT NULL,
    current_utilization REAL NOT NULL,
    status TEXT NOT NULL,
    power_state TEXT NOT NULL DEFAULT 'on',
    temperature_c REAL NOT NULL,
    power_draw_w REAL NOT NULL,
    active_workloads INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS simulations (
    run_id TEXT PRIMARY KEY,
    policy TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'done', 'failed')),
    progress REAL NOT NULL DEFAULT 0,
    error TEXT,
    seed INTEGER NOT NULL,
    num_tasks INTEGER NOT NULL,
    sleep_enabled INTEGER NOT NULL DEFAULT 1,
    sla_slack REAL NOT NULL,
    parameters TEXT NOT NULL,
    comparison_id TEXT,
    makespan REAL,
    total_energy_kwh REAL,
    avg_utilization REAL,
    sla_violations INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_simulations_comparison ON simulations (comparison_id);

CREATE TABLE IF NOT EXISTS step_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES simulations (run_id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    server_id TEXT NOT NULL,
    utilization REAL NOT NULL,
    energy_kwh REAL NOT NULL,
    power_state TEXT NOT NULL,
    queue_len INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_step_metrics_run ON step_metrics (run_id);

CREATE TABLE IF NOT EXISTS server_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES simulations (run_id) ON DELETE CASCADE,
    server_id TEXT NOT NULL,
    avg_utilization REAL NOT NULL,
    energy_kwh REAL NOT NULL,
    tasks_assigned INTEGER NOT NULL,
    sleep_fraction REAL NOT NULL,
    idle_fraction REAL NOT NULL,
    overload_fraction REAL NOT NULL,
    flags TEXT,
    UNIQUE (run_id, server_id)
);
CREATE INDEX IF NOT EXISTS idx_server_stats_run ON server_stats (run_id);
"""


def init_db(force_reseed: bool = False):
    conn = get_db_connection()
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < SCHEMA_VERSION:
            # Pre-Sprint-3 runs were scored against a fabricated baseline; drop rather than migrate.
            with conn:
                for table in ("step_metrics", "server_stats", "simulations", "servers"):
                    conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.executescript(SCHEMA)
        with conn:
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            # shortcut: assumes one API process; with several workers, move runs to a shared job queue.
            conn.execute("""UPDATE simulations SET status = 'failed', error = 'Server restarted before the run finished',
                            finished_at = CURRENT_TIMESTAMP WHERE status IN ('queued', 'running')""")
            count = conn.execute("SELECT COUNT(*) FROM servers").fetchone()[0]
            if count == 0 or force_reseed:
                conn.execute("DELETE FROM servers")
                conn.executemany(
                    """INSERT INTO servers
                       (server_id, capacity, rack_id, current_utilization, status, power_state,
                        temperature_c, power_draw_w, active_workloads)
                       VALUES (?, ?, ?, ?, ?, 'on', ?, ?, ?)""",
                    [(s["server_id"], s["capacity"], s["rack_id"], s["current_utilization"], s["status"],
                      s["temperature_c"], s["power_draw_w"], s["active_workloads"])
                     for s in INITIAL_16_SERVERS],
                )
    finally:
        conn.close()


def create_run(run_id: str, policy: str, params: Dict[str, Any], comparison_id: Optional[str] = None):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """INSERT INTO simulations
                   (run_id, policy, status, seed, num_tasks, sleep_enabled, sla_slack, parameters, comparison_id)
                   VALUES (?, ?, 'queued', ?, ?, ?, ?, ?, ?)""",
                (run_id, policy, params["seed"], params["num_tasks"], int(params["sleep_enabled"]),
                 params["sla_slack"], json.dumps(params), comparison_id),
            )
    finally:
        conn.close()


def set_run_status(run_id: str, status: str, progress: Optional[float] = None, error: Optional[str] = None):
    if status not in RUN_STATUSES:
        raise ValueError(f"invalid status {status!r}")
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """UPDATE simulations
                   SET status = ?, progress = COALESCE(?, progress), error = COALESCE(?, error),
                       finished_at = CASE WHEN ? IN ('done', 'failed') THEN CURRENT_TIMESTAMP ELSE finished_at END
                   WHERE run_id = ?""",
                (status, progress, error, status, run_id),
            )
    finally:
        conn.close()


def save_run_results(run_id: str, result: Dict[str, Any], update_servers: bool = True):
    """Writes the run summary, server_stats, step_metrics and (optionally) the servers snapshot in one transaction."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                """UPDATE simulations
                   SET status = 'done', progress = 1.0, makespan = ?, total_energy_kwh = ?,
                       avg_utilization = ?, sla_violations = ?, finished_at = CURRENT_TIMESTAMP
                   WHERE run_id = ?""",
                (result["makespan"], result["total_energy_kwh"], result["avg_utilization"],
                 result["sla_violations"], run_id),
            )
            conn.executemany(
                """INSERT INTO server_stats
                   (run_id, server_id, avg_utilization, energy_kwh, tasks_assigned,
                    sleep_fraction, idle_fraction, overload_fraction, flags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(run_id, s["server_id"], s["avg_utilization"], s["energy_kwh"], s["tasks_assigned"],
                  s["sleep_fraction"], s["idle_fraction"], s["overload_fraction"], s.get("flags", ""))
                 for s in result["server_stats"]],
            )
            conn.executemany(
                """INSERT INTO step_metrics
                   (run_id, step, timestamp, server_id, utilization, energy_kwh, power_state, queue_len)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [(run_id, m["step"], m["timestamp"], m["server_id"], m["utilization"], m["energy_kwh"],
                  m["power_state"], m["queue_len"])
                 for m in result["step_metrics"]],
            )
            if update_servers:
                conn.executemany(
                    """UPDATE servers
                       SET current_utilization = ?, status = ?, power_state = ?, temperature_c = ?,
                           power_draw_w = ?, active_workloads = ?
                       WHERE server_id = ?""",
                    [(s["current_utilization"], s["status"], s["power_state"], s["temperature_c"],
                      s["power_draw_w"], s["active_workloads"], s["server_id"])
                     for s in result["servers"]],
                )
    finally:
        conn.close()


def _row_to_run(conn: sqlite3.Connection, row: sqlite3.Row, details: bool) -> Dict[str, Any]:
    run = dict(row)
    run["parameters"] = json.loads(run["parameters"])
    run["sleep_enabled"] = bool(run["sleep_enabled"])
    if details:
        run["server_stats"] = [dict(r) for r in conn.execute(
            "SELECT * FROM server_stats WHERE run_id = ? ORDER BY server_id", (run["run_id"],))]
        run["step_metrics"] = [dict(r) for r in conn.execute(
            "SELECT * FROM step_metrics WHERE run_id = ? ORDER BY step, server_id", (run["run_id"],))]
    return run


def get_run(run_id: str, details: bool = True) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM simulations WHERE run_id = ?", (run_id,)).fetchone()
        return _row_to_run(conn, row, details) if row else None
    finally:
        conn.close()


def get_latest_run(details: bool = True) -> Optional[Dict[str, Any]]:
    """Latest finished single run; runs that belong to a comparison are excluded."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            """SELECT * FROM simulations WHERE status = 'done' AND comparison_id IS NULL
               ORDER BY finished_at DESC, rowid DESC LIMIT 1""").fetchone()
        return _row_to_run(conn, row, details) if row else None
    finally:
        conn.close()


def delete_run(run_id: str):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("DELETE FROM simulations WHERE run_id = ?", (run_id,))
    finally:
        conn.close()


def get_all_servers() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM servers ORDER BY id ASC")]
    finally:
        conn.close()


def get_server_by_id(server_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM servers WHERE server_id = ?", (server_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_server(server_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    allowed = ["status", "power_state", "current_utilization", "active_workloads", "temperature_c", "power_draw_w"]
    fields = [(k, v) for k, v in updates.items() if v is not None and k in allowed]
    if fields:
        conn = get_db_connection()
        try:
            with conn:
                conn.execute(
                    f"UPDATE servers SET {', '.join(f'{k} = ?' for k, _ in fields)} WHERE server_id = ?",
                    (*[v for _, v in fields], server_id),
                )
        finally:
            conn.close()
    return get_server_by_id(server_id)


def get_comparison_runs(comparison_id: str) -> List[Dict[str, Any]]:
    """Finished runs of one comparison, with server_stats (step_metrics omitted: not needed for aggregates)."""
    conn = get_db_connection()
    try:
        runs = []
        for row in conn.execute(
                "SELECT * FROM simulations WHERE comparison_id = ? AND status = 'done' ORDER BY rowid",
                (comparison_id,)):
            run = _row_to_run(conn, row, details=False)
            run["server_stats"] = [dict(r) for r in conn.execute(
                "SELECT * FROM server_stats WHERE run_id = ? ORDER BY server_id", (run["run_id"],))]
            runs.append(run)
        return runs
    finally:
        conn.close()


def latest_comparison_id() -> Optional[str]:
    conn = get_db_connection()
    try:
        row = conn.execute("""SELECT comparison_id FROM simulations WHERE comparison_id IS NOT NULL
                              AND status = 'done' ORDER BY rowid DESC LIMIT 1""").fetchone()
        return row[0] if row else None
    finally:
        conn.close()
