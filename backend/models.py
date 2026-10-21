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

class EnergySavingsItem(BaseModel):
    category: str
    amount_kwh: float
    saved_usd: float
    description: str

class EnergySavingsReport(BaseModel):
    total_energy_saved_kwh: float
    total_cost_saved_usd: float
    carbon_reduction_kg: float
    pue_ratio: float
    idle_servers_consolidated: int
    cooling_efficiency_boost_pct: float
    breakdown: List[EnergySavingsItem]

# --- Simulation Engine Models ---

class SimulationRequest(BaseModel):
    num_tasks: int = Field(default=100, ge=10, le=2000, description="Number of tasks to generate and schedule")
    policy: str = Field(default="min-min", description="Scheduling policy e.g. 'min-min'")
    seed: int = Field(default=42, description="Random seed for reproducible workload generation")
    num_steps: int = Field(default=15, ge=5, le=50, description="Number of discrete telemetry sampling steps")

class ServerStatModel(BaseModel):
    server_id: str
    avg_utilization: float
    energy_consumed: float
    total_tasks_assigned: int
    flags: Optional[str] = ""

class StepMetricModel(BaseModel):
    step: int
    timestamp: float
    server_id: str
    utilization: float
    energy: float

class SimulationResponse(BaseModel):
    run_id: str
    policy: str
    parameters: Dict[str, Any]
    total_tasks: int
    makespan_seconds: float
    total_energy_kwh: float
    baseline_energy_kwh: float
    energy_saved_kwh: float
    energy_saved_pct: float
    cost_saved_usd: float
    carbon_reduction_kg: float
    pue_ratio: float
    sla_violations_count: Optional[int] = 0
    servers: List[Dict[str, Any]]
    server_stats: List[ServerStatModel]
    step_metrics: List[StepMetricModel]
    analytics: Optional[Dict[str, Any]] = None

class BenchmarkComparisonRequest(BaseModel):
    num_tasks: int = Field(default=100, ge=10, le=1000)
    seed: int = Field(default=42)
    num_steps: int = Field(default=15, ge=5, le=50)
