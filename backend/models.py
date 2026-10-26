from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ServerBase(BaseModel):
    server_id: str = Field(..., description="Unique server identifier e.g. SRV-01")
    capacity: str = Field(..., description="Hardware specification e.g. 64 vCPU / 256GB")
    current_utilization: float = Field(..., ge=0.0, le=100.0, description="CPU utilization percentage")
    status: str = Field(..., description="Server operational state: 'active' or 'idle'")
    rack_id: Optional[str] = "RACK-01"
    temperature_c: Optional[float] = 42.5
    power_draw_w: Optional[float] = 320.0
    active_workloads: Optional[int] = 12
    avg_utilization: Optional[float] = None
    energy_consumed_kwh: Optional[float] = None
    flags: Optional[str] = None

class Server(ServerBase):
    id: Optional[int] = None

class ServerUpdate(BaseModel):
    status: Optional[str] = None
    current_utilization: Optional[float] = None
    active_workloads: Optional[int] = None

# --- Simulation Engine Models ---

class SimulationRequest(BaseModel):
    num_tasks: int = Field(default=100, ge=10, le=2000, description="Number of tasks to generate and schedule")
    policy: str = Field(default="min-min", description="Scheduling policy e.g. 'min-min'")
    seed: int = Field(default=42, description="Random seed for reproducible workload generation")
    num_steps: int = Field(default=15, ge=5, le=50, description="Number of discrete telemetry sampling steps")
