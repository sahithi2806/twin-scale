const API_BASE_URL = 'http://localhost:8000';

export async function fetchServers() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2500);
    const res = await fetch(`${API_BASE_URL}/api/servers`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return { data: await res.json(), isBackendConnected: true };
  } catch (err) {
    throw new Error(err.name === 'AbortError' ? 'request timed out' : err.message);
  }
}

export async function toggleServerStatus(serverId) {
  const res = await fetch(`${API_BASE_URL}/api/servers/${encodeURIComponent(serverId)}/toggle-status`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

async function readError(res) {
  try {
    const body = await res.json();
    return typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body);
  } catch {
    return `HTTP ${res.status}`;
  }
}

export async function startSimulation(params) {
  const res = await fetch(`${API_BASE_URL}/api/simulations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function getSimulation(runId) {
  const res = await fetch(`${API_BASE_URL}/api/simulations/${encodeURIComponent(runId)}`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function runSimulation(params, onProgress = () => {}) {
  const { run_id } = await startSimulation(params);
  onProgress({ run_id, status: 'queued', progress: 0 });
  for (;;) {
    const run = await getSimulation(run_id);
    onProgress(run);
    if (run.status === 'done') return run;
    if (run.status === 'failed') throw new Error(run.error || 'Simulation failed');
    await sleep(500);
  }
}

export async function fetchPolicies() {
  const res = await fetch(`${API_BASE_URL}/api/policies`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchLatestSimulation() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/simulations/latest`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function runComparison(params) {
  const res = await fetch(`${API_BASE_URL}/api/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchLatestComparison() {
  const res = await fetch(`${API_BASE_URL}/api/compare/latest`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
