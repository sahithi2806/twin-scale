import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "servers.db")

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

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(force_reseed: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Servers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT UNIQUE NOT NULL,
            capacity TEXT NOT NULL,
            current_utilization REAL NOT NULL,
            status TEXT NOT NULL,
            rack_id TEXT NOT NULL,
            temperature_c REAL NOT NULL,
            power_draw_w REAL NOT NULL,
            active_workloads INTEGER NOT NULL
        )
    """)

    # 2. Simulations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            run_id TEXT PRIMARY KEY,
            policy TEXT NOT NULL,
            parameters TEXT NOT NULL,
            total_tasks INTEGER NOT NULL,
            makespan REAL NOT NULL,
            total_energy_kwh REAL NOT NULL,
            baseline_energy_kwh REAL NOT NULL,
            energy_saved_kwh REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Step metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS step_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            step INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            server_id TEXT NOT NULL,
            utilization REAL NOT NULL,
            energy REAL NOT NULL,
            FOREIGN KEY (run_id) REFERENCES simulations (run_id) ON DELETE CASCADE
        )
    """)

    # 4. Server stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            server_id TEXT NOT NULL,
            avg_utilization REAL NOT NULL,
            energy_consumed REAL NOT NULL,
            total_tasks_assigned INTEGER NOT NULL,
            flags TEXT,
            FOREIGN KEY (run_id) REFERENCES simulations (run_id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # Check row count for servers
    cursor.execute("SELECT COUNT(*) FROM servers")
    count = cursor.fetchone()[0]

    if count == 0 or force_reseed:
        if force_reseed:
            cursor.execute("DELETE FROM servers")
            conn.commit()
            
        for srv in INITIAL_16_SERVERS:
            cursor.execute("""
                INSERT OR REPLACE INTO servers 
                (server_id, capacity, current_utilization, status, rack_id, temperature_c, power_draw_w, active_workloads)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                srv["server_id"],
                srv["capacity"],
                srv["current_utilization"],
                srv["status"],
                srv["rack_id"],
                srv["temperature_c"],
                srv["power_draw_w"],
                srv["active_workloads"]
            ))
        conn.commit()
    conn.close()

def save_simulation_results(sim: Dict[str, Any]):
    """
    Stores all simulation results (simulations, server_stats, step_metrics)
    and updates server states inside a single atomic SQLite transaction.
    """
    conn = get_db_connection()
    try:
        with conn:  # Enforces a single atomic transaction
            cursor = conn.cursor()

            # 1. Store run record in simulations table
            cursor.execute("""
                INSERT INTO simulations 
                (run_id, policy, parameters, total_tasks, makespan, total_energy_kwh, baseline_energy_kwh, energy_saved_kwh)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim["run_id"],
                sim["policy"],
                json.dumps(sim["parameters"]),
                sim["total_tasks"],
                sim["makespan_seconds"],
                sim["total_energy_kwh"],
                sim["baseline_energy_kwh"],
                sim["energy_saved_kwh"]
            ))

            # 2. Store aggregated server statistics
            for ss in sim["server_stats"]:
                cursor.execute("""
                    INSERT INTO server_stats 
                    (run_id, server_id, avg_utilization, energy_consumed, total_tasks_assigned, flags)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sim["run_id"],
                    ss["server_id"],
                    ss["avg_utilization"],
                    ss["energy_consumed"],
                    ss["total_tasks_assigned"],
                    ss.get("flags", "")
                ))

            # 3. Store step metrics time-series
            for sm in sim["step_metrics"]:
                cursor.execute("""
                    INSERT INTO step_metrics 
                    (run_id, step, timestamp, server_id, utilization, energy)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sim["run_id"],
                    sm["step"],
                    sm["timestamp"],
                    sm["server_id"],
                    sm["utilization"],
                    sm["energy"]
                ))

            # 4. Synchronize virtual servers table with the latest simulation state
            for srv in sim["servers"]:
                cursor.execute("""
                    UPDATE servers
                    SET current_utilization = ?, status = ?, temperature_c = ?, power_draw_w = ?, active_workloads = ?
                    WHERE server_id = ?
                """, (
                    srv["current_utilization"],
                    srv["status"],
                    srv["temperature_c"],
                    srv["power_draw_w"],
                    srv["active_workloads"],
                    srv["server_id"]
                ))
    finally:
        conn.close()

def get_latest_simulation() -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulations ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    sim = dict(row)
    sim["parameters"] = json.loads(sim["parameters"])
    
    # Fetch server_stats
    cursor.execute("SELECT * FROM server_stats WHERE run_id = ?", (sim["run_id"],))
    sim["server_stats"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return sim

def get_latest_simulation_by_policy(policy: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulations WHERE LOWER(policy) = LOWER(?) ORDER BY created_at DESC LIMIT 1", (policy,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    sim = dict(row)
    sim["parameters"] = json.loads(sim["parameters"])
    
    cursor.execute("SELECT * FROM server_stats WHERE run_id = ?", (sim["run_id"],))
    sim["server_stats"] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM step_metrics WHERE run_id = ? ORDER BY step ASC", (sim["run_id"],))
    sim["step_metrics"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return sim

def get_simulation_by_id(run_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM simulations WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    sim = dict(row)
    sim["parameters"] = json.loads(sim["parameters"])
    
    cursor.execute("SELECT * FROM server_stats WHERE run_id = ?", (run_id,))
    sim["server_stats"] = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM step_metrics WHERE run_id = ? ORDER BY step ASC", (run_id,))
    sim["step_metrics"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return sim

def get_all_servers() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM servers ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_server_by_id(server_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM servers WHERE server_id = ? OR id = ?", (server_id, server_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_server(server_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for k, v in updates.items():
        if v is not None and k in ["status", "current_utilization", "active_workloads", "temperature_c", "power_draw_w"]:
            fields.append(f"{k} = ?")
            values.append(v)
            
    if not fields:
        conn.close()
        return get_server_by_id(server_id)

    values.append(server_id)
    query = f"UPDATE servers SET {', '.join(fields)} WHERE server_id = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()
    return get_server_by_id(server_id)
