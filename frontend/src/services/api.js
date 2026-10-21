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
  cooling_efficiency_boost_pct: 26.4,
  breakdown: [
    {
      category: "Idle Core Consolidation (Min-Min)",
      amount_kwh: 2187.2,
      saved_usd: 306.21,
      description: "Consolidated workloads leaving idle nodes in low-power standby"
    },
    {
      category: "Dynamic Thermal Cooling Adjustment",
      amount_kwh: 1555.4,
      saved_usd: 217.75,
      description: "AI-driven fan curve and CRAC chiller optimization"
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

/**
 * Triggers POST /api/simulations to run the Min-Min simulation engine
 */
export async function runSimulation({ num_tasks = 100, policy = 'min-min', seed = 42, num_steps = 15 }) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/simulations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        num_tasks: Number(num_tasks),
        policy,
        seed: Number(seed),
        num_steps: Number(num_steps)
      })
    });
    if (!res.ok) {
      throw new Error(`Simulation request failed: HTTP ${res.status}`);
    }
    const data = await res.json();
    return { data, isBackendConnected: true };
  } catch (err) {
    console.warn("Backend simulation API offline, running synthetic client fallback:", err);
    
    // Client-side fallback simulation to ensure UI continues to function gracefully
    const simId = `SIM-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
    const makespan = Math.round(80 + (num_tasks * 0.45));
    const totalEnergy = Number((0.0035 * num_tasks).toFixed(4));
    const baselineEnergy = Number((totalEnergy * 1.48).toFixed(4));
    const energySaved = Number((baselineEnergy - totalEnergy).toFixed(4));

    const simulatedServers = FALLBACK_16_SERVERS.map((srv, idx) => {
      const isIdleNode = idx % 4 === 3 && num_tasks < 250;
      const util = isIdleNode ? 0.0 : Math.min(95.0, Math.round(35 + (idx * 3.8 + (seed % 17)) % 52));
      const activeWorkloads = isIdleNode ? 0 : Math.round(num_tasks / 12 + (idx % 3));
      return {
        ...srv,
        current_utilization: util,
        status: isIdleNode ? 'idle' : 'active',
        active_workloads: activeWorkloads,
        temperature_c: isIdleNode ? 32.0 : Math.round(30 + (util * 0.35)),
        power_draw_w: isIdleNode ? 70.0 : Math.round(80 + (util * 3.4)),
        avg_utilization: util,
        energy_consumed_kwh: Number((totalEnergy / 14).toFixed(4)),
        flags: isIdleNode ? 'IDLE_CONSOLIDATED' : util > 80 ? 'HOTSPOT_HIGH_LOAD' : 'OPTIMAL_LOAD'
      };
    });

    const fallbackResponse = {
      run_id: simId,
      policy: policy,
      parameters: { num_tasks, seed, num_steps },
      total_tasks: num_tasks,
      makespan_seconds: makespan,
      total_energy_kwh: totalEnergy,
      baseline_energy_kwh: baselineEnergy,
      energy_saved_kwh: energySaved,
      energy_saved_pct: 32.4,
      cost_saved_usd: Number((energySaved * 0.14).toFixed(2)),
      carbon_reduction_kg: Number((energySaved * 0.42).toFixed(2)),
      pue_ratio: 1.15,
      servers: simulatedServers,
      server_stats: simulatedServers.map(s => ({
        server_id: s.server_id,
        avg_utilization: s.current_utilization,
        energy_consumed: s.energy_consumed_kwh || 0.02,
        total_tasks_assigned: s.active_workloads || 0,
        flags: s.flags || ''
      })),
      step_metrics: []
    };

    return { data: fallbackResponse, isBackendConnected: false };
  }
}

export async function fetchLatestSimulation() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/simulations/latest`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    return null;
  }
}

/**
 * Retrieves comparative analysis between Min-Min and DQN
 */
export async function fetchComparison(params = {}) {
  try {
    const query = new URLSearchParams();
    if (params.min_min_run_id) query.append('min_min_run_id', params.min_min_run_id);
    if (params.dqn_run_id) query.append('dqn_run_id', params.dqn_run_id);
    const qs = query.toString() ? `?${query.toString()}` : '';

    const res = await fetch(`${API_BASE_URL}/api/compare${qs}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend compare endpoint error, generating local comparison:", err);
    return null;
  }
}

/**
 * Runs a head-to-head benchmark comparing Min-Min and DQN on the exact same task set
 */
export async function runComparativeBenchmark({ num_tasks = 100, seed = 42 }) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/compare/benchmark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_tasks: Number(num_tasks), seed: Number(seed), num_steps: 15 })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Could not run benchmark on backend:", err);
    return null;
  }
}

