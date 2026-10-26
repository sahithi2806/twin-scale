from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

from config import SLA_DEADLINE_SLACK, DEFAULT_ARRIVAL_RATE
from evaluation import EVAL_SEED_START

class ServerBase(BaseModel):
    server_id: str = Field(..., description="Unique server identifier e.g. SRV-01")
    capacity: str = Field(..., description="Hardware specification e.g. 64 vCPU / 256GB")
    current_utilization: float = Field(..., ge=0.0, le=100.0, description="CPU utilization percentage")
    status: str = Field(..., description="Server operational state: 'active' or 'idle'")
    rack_id: Optional[str] = "RACK-01"
    temperature_c: Optional[float] = 42.5
    power_draw_w: Optional[float] = 320.0
    active_workloads: Optional[int] = 12
    power_state: str = Field("on", description="'on' or 'sleep' (from the latest single run, or a manual toggle)")

class Server(ServerBase):
    id: Optional[int] = None

class ServerUpdate(BaseModel):
    status: Optional[str] = None
    current_utilization: Optional[float] = None
    active_workloads: Optional[int] = None

# --- Simulation Engine Models ---

PolicyName = Literal["min-min", "power-aware", "dqn"]


class WorkloadParams(BaseModel):
    num_tasks: int = Field(default=200, ge=10, le=2000, description="Number of synthetic tasks")
    sleep_enabled: bool = Field(default=True, description="Allow idle servers to enter the sleep state")
    sla_slack: float = Field(default=SLA_DEADLINE_SLACK, ge=1.0, le=10.0,
                             description="Deadline = arrival + sla_slack * ideal execution time")
    arrival_rate: float = Field(default=DEFAULT_ARRIVAL_RATE, gt=0.0, le=10.0,
                                description="Poisson arrival rate, tasks per second")


class SimulationRequest(WorkloadParams):
    policy: PolicyName = Field(default="min-min", description="Scheduling policy")
    seed: int = Field(default=42, ge=0, description="Workload seed; same seed and policy give identical metrics")


class CompareRequest(WorkloadParams):
    n_seeds: int = Field(default=10, ge=2, le=50, description="Number of held-out seeds per policy")
    seed_start: int = Field(default=EVAL_SEED_START, ge=EVAL_SEED_START,
                            description="First seed; seeds below 1000 are reserved for DQN training")
