from pydantic import BaseModel, Field
from typing import Optional, List

class ServerBase(BaseModel):
    server_id: str = Field(..., description="Unique server identifier e.g. SRV-01")
    capacity: str = Field(..., description="Hardware specification e.g. 64 vCPU / 256GB")
    current_utilization: float = Field(..., ge=0.0, le=100.0, description="CPU utilization percentage")
    status: str = Field(..., description="Server operational state: 'active' or 'idle'")
    rack_id: Optional[str] = "RACK-01"
    temperature_c: Optional[float] = 42.5
    power_draw_w: Optional[float] = 320.0
    active_workloads: Optional[int] = 12

class Server(ServerBase):
    id: int

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
