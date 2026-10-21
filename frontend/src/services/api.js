const API_BASE_URL = 'http://localhost:8000';

export const FALLBACK_16_SERVERS = [
  {
    id: 1,
    server_id: "SRV-01",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 84.5,
    status: "active",
    rack_id: "RACK-A1",
    temperature_c: 58.2,
    power_draw_w: 410.0,
    active_workloads: 19
  },
  {
    id: 2,
    server_id: "SRV-02",
    capacity: "128 vCPU / 512 GB RAM",
    current_utilization: 92.1,
    status: "active",
    rack_id: "RACK-A1",
    temperature_c: 64.7,
    power_draw_w: 485.5,
    active_workloads: 31
  },
  {
    id: 3,
    server_id: "SRV-03",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 61.3,
    status: "active",
    rack_id: "RACK-A2",
    temperature_c: 49.8,
    power_draw_w: 330.0,
    active_workloads: 14
  },
  {
    id: 4,
    server_id: "SRV-04",
    capacity: "32 vCPU / 128 GB RAM",
    current_utilization: 0.0,
    status: "idle",
    rack_id: "RACK-A2",
    temperature_c: 33.1,
    power_draw_w: 75.0,
    active_workloads: 0
  },
  {
    id: 5,
    server_id: "SRV-05",
    capacity: "96 vCPU / 384 GB RAM",
    current_utilization: 77.8,
    status: "active",
    rack_id: "RACK-B1",
    temperature_c: 56.4,
    power_draw_w: 380.0,
    active_workloads: 22
  },
  {
    id: 6,
    server_id: "SRV-06",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 43.2,
    status: "active",
    rack_id: "RACK-B1",
    temperature_c: 44.0,
    power_draw_w: 280.0,
    active_workloads: 9
  },
  {
    id: 7,
    server_id: "SRV-07",
    capacity: "128 vCPU / 512 GB RAM",
    current_utilization: 89.0,
    status: "active",
    rack_id: "RACK-B2",
    temperature_c: 62.9,
    power_draw_w: 465.0,
    active_workloads: 28
  },
  {
    id: 8,
    server_id: "SRV-08",
    capacity: "32 vCPU / 128 GB RAM",
    current_utilization: 0.0,
    status: "idle",
    rack_id: "RACK-B2",
    temperature_c: 32.5,
    power_draw_w: 70.0,
    active_workloads: 0
  },
  {
    id: 9,
    server_id: "SRV-09",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 71.4,
    status: "active",
    rack_id: "RACK-C1",
    temperature_c: 53.6,
    power_draw_w: 360.0,
    active_workloads: 17
  },
  {
    id: 10,
    server_id: "SRV-10",
    capacity: "96 vCPU / 384 GB RAM",
    current_utilization: 82.6,
    status: "active",
    rack_id: "RACK-C1",
    temperature_c: 59.1,
    power_draw_w: 420.0,
    active_workloads: 24
  },
  {
    id: 11,
    server_id: "SRV-11",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 0.0,
    status: "idle",
    rack_id: "RACK-C2",
    temperature_c: 34.0,
    power_draw_w: 80.0,
    active_workloads: 0
  },
  {
    id: 12,
    server_id: "SRV-12",
    capacity: "128 vCPU / 512 GB RAM",
    current_utilization: 95.3,
    status: "active",
    rack_id: "RACK-C2",
    temperature_c: 67.2,
    power_draw_w: 498.0,
    active_workloads: 35
  },
  {
    id: 13,
    server_id: "SRV-13",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 68.7,
    status: "active",
    rack_id: "RACK-D1",
    temperature_c: 51.5,
    power_draw_w: 345.0,
    active_workloads: 16
  },
  {
    id: 14,
    server_id: "SRV-14",
    capacity: "32 vCPU / 128 GB RAM",
    current_utilization: 0.0,
    status: "idle",
    rack_id: "RACK-D1",
    temperature_c: 31.8,
    power_draw_w: 68.0,
    active_workloads: 0
  },
  {
    id: 15,
    server_id: "SRV-15",
    capacity: "96 vCPU / 384 GB RAM",
    current_utilization: 79.9,
    status: "active",
    rack_id: "RACK-D2",
    temperature_c: 57.8,
    power_draw_w: 395.0,
    active_workloads: 21
  },
  {
    id: 16,
    server_id: "SRV-16",
    capacity: "64 vCPU / 256 GB RAM",
    current_utilization: 54.1,
    status: "active",
    rack_id: "RACK-D2",
    temperature_c: 47.3,
    power_draw_w: 310.0,
    active_workloads: 13
  }
];

export const FALLBACK_ENERGY_SAVINGS = {
  total_energy_saved_kwh: 4860.5,
  total_cost_saved_usd: 680.47,
  carbon_reduction_kg: 2041.4,
  pue_ratio: 1.15,
  idle_servers_consolidated: 4,
  cooling_efficiency_boost_pct: 24.8,
  breakdown: [
    {
      category: "Idle Core Consolidation",
      amount_kwh: 2041.4,
      saved_usd: 285.8,
      description: "Migrating workloads from 4 low-load nodes into power-managed sleep state"
    },
    {
      category: "Dynamic Thermal Cooling Adjustment",
      amount_kwh: 1701.2,
      saved_usd: 238.16,
      description: "AI-driven fan curve and CRAC chiller optimization using digital twin thermal map"
    },
    {
      category: "Peak Shaving & Workload Balancing",
      amount_kwh: 1117.9,
      saved_usd: 156.51,
      description: "Flattening temperature hotspots to maintain silicon at optimal operating efficiency"
    }
  ]
};

export async function fetchServers() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);
    const res = await fetch(`${API_BASE_URL}/api/servers`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return { data, isBackendConnected: true };
  } catch (err) {
    console.warn("Backend offline or unreachable, using local fallback state:", err.message);
    return { data: FALLBACK_16_SERVERS, isBackendConnected: false };
  }
}

export async function fetchEnergySavings() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);
    const res = await fetch(`${API_BASE_URL}/api/energy-savings`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return { data, isBackendConnected: true };
  } catch (err) {
    return { data: FALLBACK_ENERGY_SAVINGS, isBackendConnected: false };
  }
}

export async function toggleServerStatus(serverId) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/servers/${serverId}/toggle-status`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Could not reach backend to toggle status:", err);
    return null;
  }
}
