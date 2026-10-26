from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import logging
import random

import uuid

from database import (
    init_db,
    get_all_servers,
    get_server_by_id,
    update_server,
    create_run,
    set_run_status,
    save_run_results,
    get_run,
    get_latest_run,
)
from schemas import Server, ServerUpdate, SimulationRequest
from simulation import run_simulation
from policies import get_policy, PolicyUnavailable

logger = logging.getLogger("dctwin")

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

def new_run_id() -> str:
    return f"RUN-{uuid.uuid4().hex[:10].upper()}"


def run_engine(policy: str, params: Dict[str, Any], progress_cb=None) -> Dict[str, Any]:
    return run_simulation(
        get_all_servers(), get_policy(policy),
        num_tasks=params["num_tasks"], seed=params["seed"], sleep_enabled=params["sleep_enabled"],
        sla_slack=params["sla_slack"], arrival_rate=params["arrival_rate"], progress_cb=progress_cb)


def ensure_policy_available(policy: str):
    try:
        get_policy(policy)
    except PolicyUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


def execute_run(run_id: str, policy: str, params: Dict[str, Any], update_servers: bool = True):
    try:
        set_run_status(run_id, "running", progress=0.0)
        result = run_engine(
            policy, params, progress_cb=lambda p: set_run_status(run_id, "running", progress=round(p, 3)))
        save_run_results(run_id, result, update_servers=update_servers)
    except Exception as exc:
        logger.exception("simulation run %s failed", run_id)
        set_run_status(run_id, "failed", error=f"{type(exc).__name__}: {exc}")


@app.post("/api/simulations", status_code=status.HTTP_202_ACCEPTED)
def start_simulation(req: SimulationRequest, background_tasks: BackgroundTasks):
    ensure_policy_available(req.policy)
    params = req.model_dump(exclude={"policy"})
    run_id = new_run_id()
    create_run(run_id, req.policy, params)
    background_tasks.add_task(execute_run, run_id, req.policy, params)
    return {"run_id": run_id, "status": "queued"}


@app.get("/api/simulations/latest")
def get_latest_sim():
    latest = get_latest_run()
    if not latest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No finished simulation runs yet. POST /api/simulations first.")
    return latest


@app.get("/api/simulations/{run_id}")
def get_simulation_details(run_id: str):
    sim = get_run(run_id, details=False)
    if sim and sim["status"] == "done":
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
