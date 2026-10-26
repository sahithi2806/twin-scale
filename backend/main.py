from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import random

import uuid

from database import (
    init_db,
    get_all_servers,
    get_server_by_id,
    update_server,
    create_run,
    save_run_results,
    get_run,
    get_latest_run,
)
from models import Server, ServerUpdate, SimulationRequest
from simulation import SimulationEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database (servers, simulations, step_metrics, server_stats)
    init_db()
    yield

app = FastAPI(
    title="Data Center Digital Twin API & AI Simulation Engine",
    description="Real-time virtual server telemetry, Min-Min & DQN schedulers, and comparative analytics",
    version="3.0.0",
    lifespan=lifespan
)

# Enable CORS for Vite frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "Data Center Digital Twin API & Simulation Engine",
        "version": "3.0.0",
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "servers": "/api/servers",
            "simulations": "POST /api/simulations",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
def health_check():
    servers = get_all_servers()
    latest = get_latest_run(details=False)
    return {
        "status": "healthy",
        "server_count": len(servers),
        "database": "sqlite",
        "latest_simulation_run": latest["run_id"] if latest else None
    }

# --- Virtual Server Telemetry Endpoints ---

@app.get("/api/servers", response_model=List[Server])
def get_servers():
    """
    Returns telemetry for the 16 virtual servers.
    Each server contains server_id, capacity, current_utilization (%), and status (active/idle).
    """
    servers = get_all_servers()
    return servers

@app.get("/api/servers/{server_id}", response_model=Server)
def get_single_server(server_id: str):
    """
    Retrieve telemetry and operational metrics for a specific virtual server.
    """
    server = get_server_by_id(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found"
        )
    return server

@app.patch("/api/servers/{server_id}", response_model=Server)
def update_server_telemetry(server_id: str, payload: ServerUpdate):
    """
    Update server operational status or utilization.
    """
    server = get_server_by_id(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found"
        )
    
    update_data = payload.model_dump(exclude_unset=True)
    
    if update_data.get("status") == "idle":
        update_data["current_utilization"] = 0.0
        update_data["active_workloads"] = 0
        update_data["temperature_c"] = round(random.uniform(31.0, 34.0), 1)
        update_data["power_draw_w"] = round(random.uniform(65.0, 80.0), 1)
    elif update_data.get("status") == "active" and server["status"] == "idle":
        update_data["current_utilization"] = round(random.uniform(45.0, 75.0), 1)
        update_data["active_workloads"] = random.randint(8, 20)
        update_data["temperature_c"] = round(random.uniform(48.0, 58.0), 1)
        update_data["power_draw_w"] = round(random.uniform(310.0, 390.0), 1)

    updated = update_server(server_id, update_data)
    return updated

@app.post("/api/servers/{server_id}/toggle-status", response_model=Server)
def toggle_server_status(server_id: str):
    """
    Convenience endpoint to toggle a server between active and idle.
    """
    server = get_server_by_id(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found"
        )
    
    new_status = "idle" if server["status"] == "active" else "active"
    update_payload = ServerUpdate(status=new_status)
    return update_server_telemetry(server_id, update_payload)

# --- Simulation Engine Endpoints ---

def _legacy_to_result(sim: Dict[str, Any]) -> Dict[str, Any]:
    stats = [{
        "server_id": s["server_id"],
        "avg_utilization": s["avg_utilization"],
        "energy_kwh": s["energy_consumed"],
        "tasks_assigned": s["total_tasks_assigned"],
        "sleep_fraction": 0.0,
        "idle_fraction": 0.0,
        "overload_fraction": 0.0,
        "flags": s.get("flags", ""),
    } for s in sim["server_stats"]]
    steps = [{**m, "energy_kwh": m["energy"], "power_state": "on", "queue_len": 0} for m in sim["step_metrics"]]
    servers = [{**s, "power_state": "on"} for s in sim["servers"]]
    return {
        "makespan": sim["makespan_seconds"],
        "total_energy_kwh": sim["total_energy_kwh"],
        "avg_utilization": round(sum(s["avg_utilization"] for s in stats) / max(1, len(stats)), 2),
        "sla_violations": sim["sla_violations_count"],
        "server_stats": stats,
        "step_metrics": steps,
        "servers": servers,
    }


@app.post("/api/simulations")
def run_simulation(req: SimulationRequest):
    raw_servers = get_all_servers()
    params = {"num_tasks": req.num_tasks, "seed": req.seed, "num_steps": req.num_steps,
              "sleep_enabled": True, "sla_slack": 1.4}
    run_id = f"RUN-{uuid.uuid4().hex[:10].upper()}"
    create_run(run_id, req.policy, params)
    sim = SimulationEngine(raw_servers).run_simulation(
        num_tasks=req.num_tasks, policy=req.policy, seed=req.seed, num_steps=req.num_steps)
    save_run_results(run_id, _legacy_to_result(sim))
    return get_run(run_id)


@app.get("/api/simulations/latest")
def get_latest_sim():
    latest = get_latest_run()
    if not latest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No finished simulation runs yet. POST /api/simulations first.")
    return latest


@app.get("/api/simulations/{run_id}")
def get_simulation_details(run_id: str):
    sim = get_run(run_id)
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Simulation run '{run_id}' not found.")
    return sim


@app.post("/api/servers/reset")
def reset_servers():
    """
    Resets all 16 servers to the default initial mock dataset.
    """
    init_db(force_reseed=True)
    return {"message": "All 16 servers reset to initial digital twin state"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
