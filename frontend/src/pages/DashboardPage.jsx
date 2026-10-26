import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  fetchServers,
  toggleServerStatus,
  runSimulation,
  fetchPolicies,
  fetchLatestSimulation,
  fetchLatestComparison
} from '../services/api';

import StatsBar from '../components/StatsBar';
import CpuChip from '../components/CpuChip';
import ServerDetailPanel from '../components/ServerDetailPanel';
import EnergySavingsModal from '../components/EnergySavingsModal';
import SimulationControlPanel from '../components/SimulationControlPanel';

import { RefreshCw, Grid3X3, CheckCircle2, WifiOff } from 'lucide-react';

export default function DashboardPage() {
  const [servers, setServers] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [backendError, setBackendError] = useState(null);
  const [latestSim, setLatestSim] = useState(null);
  const [selectedServerId, setSelectedServerId] = useState(null);
  const [isEnergyModalOpen, setIsEnergyModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'active' | 'idle'
  const [simNotification, setSimNotification] = useState(null);
  const [simProgress, setSimProgress] = useState(null);
  const [simError, setSimError] = useState(null);
  const [policyStatus, setPolicyStatus] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setBackendError(null);
    fetchPolicies().then(setPolicyStatus).catch(() => setPolicyStatus(null));
    try {
      const [serversRes, latestSimRes, latestComparison] = await Promise.all([
        fetchServers(),
        fetchLatestSimulation(),
        fetchLatestComparison()
      ]);
      setServers(serversRes.data);
      setLatestSim(latestSimRes);
      setComparison(latestComparison);
    } catch (err) {
      setServers([]);
      setBackendError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunSimulation = async (params) => {
    setIsSimulating(true);
    setSimNotification(null);
    setSimError(null);
    setSimProgress({ status: 'queued', progress: 0 });
    try {
      const run = await runSimulation(params, (r) => setSimProgress({ status: r.status, progress: r.progress ?? 0 }));
      setLatestSim(run);
      const serversRes = await fetchServers();
      setServers(serversRes.data);
      setSimNotification({
        run_id: run.run_id,
        policy: run.policy,
        tasks: run.num_tasks,
        makespan: run.makespan,
        energy_kwh: run.total_energy_kwh,
        sla_violations: run.sla_violations
      });
      setTimeout(() => setSimNotification(null), 7000);
    } catch (err) {
      setSimError(err.message);
    } finally {
      setIsSimulating(false);
      setSimProgress(null);
    }
  };

  // Handle CPU chip click: isolate selected CPU (100% opacity) while others dim to 20%
  const handleCpuClick = (server) => {
    if (selectedServerId === server.server_id) {
      setSelectedServerId(null);
    } else {
      setSelectedServerId(server.server_id);
    }
  };

  const handleClearSelection = () => {
    setSelectedServerId(null);
  };

  // Toggle server active/idle status (syncs with SQLite backend!)
  const handleToggleServerStatus = async (serverId) => {
    setIsUpdating(true);
    try {
      const updated = await toggleServerStatus(serverId);
      setServers((prev) => prev.map((s) => (s.server_id === serverId ? updated : s)));
    } catch (err) {
      setSimError(`Could not toggle ${serverId}: ${err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const selectedServer = servers.find((s) => s.server_id === selectedServerId);

  const displayedServers = servers.filter((s) => {
    if (statusFilter === 'active') return s.status.toLowerCase() === 'active';
    if (statusFilter === 'idle') return s.status.toLowerCase() === 'idle';
    return true;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

      {/* 1. TOP STATS BAR WITH PROMINENT CLICKABLE 'ENERGY SAVED' CARD */}
      <StatsBar
        servers={servers}
        comparison={comparison}
        latestSim={latestSim}
        onOpenEnergyModal={() => setIsEnergyModalOpen(true)}
      />

      {/* 2. SIMULATION SUCCESS BANNER (Triggered on simulation completion) */}
      {simNotification && (
        <div className="mb-6 p-4 bg-gradient-to-r from-emerald-50 via-teal-50 to-sky-50 border border-emerald-200/90 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs animate-fadeIn">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-emerald-950 text-xs sm:text-sm">
                  {simNotification.policy === 'dqn' ? 'DQN RL Agent' : 'Min-Min'} Simulation Complete ({simNotification.run_id})
                </span>
                <span className="text-[10px] font-mono bg-emerald-200/70 text-emerald-900 px-2 py-0.5 rounded-full font-semibold">
                  Energy: {simNotification.energy_kwh} kWh
                </span>
                <span className="text-[10px] font-mono bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full font-semibold">
                  SLA Violations: {simNotification.sla_violations}
                </span>
              </div>
              <p className="text-xs text-emerald-800 font-mono mt-0.5">
                {simNotification.tasks} tasks mapped • Makespan: {simNotification.makespan}s • 4×4 CPU grid updated dynamically
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <Link to="/compare" className="text-xs text-indigo-700 hover:text-indigo-900 underline font-semibold font-mono">
              Compare schedulers →
            </Link>
            <button
              onClick={() => setSimNotification(null)}
              className="text-xs text-emerald-700 hover:text-emerald-900 underline font-semibold cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {backendError && (
        <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 font-mono flex items-center gap-2">
          <WifiOff className="w-4 h-4 shrink-0" />
          <span>Backend unreachable ({backendError}). Start it with `uvicorn main:app` in backend/ and press refresh.</span>
        </div>
      )}

      {simError && (
        <div className="mb-6 p-3 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-800 font-mono flex items-center justify-between gap-3">
          <span>Simulation failed: {simError}</span>
          <button onClick={() => setSimError(null)} className="underline font-semibold cursor-pointer">Dismiss</button>
        </div>
      )}

      {/* 3. SIMULATION CONFIGURATION SIDEBAR / PANEL */}
      <div className="mb-6">
        <SimulationControlPanel
          onRunSimulation={handleRunSimulation}
          policyStatus={policyStatus}
          isRunning={isSimulating}
          progress={simProgress}
          latestSim={latestSim}
        />
      </div>

          {/* 4. DASHBOARD CONTROL BAR */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-4 mb-6 flex flex-wrap items-center justify-between gap-4">

            {/* Left: Focus / Selection status */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Grid3X3 className="w-5 h-5 text-sky-600" />
                <h2 className="text-base font-bold text-slate-800">
                  4×4 Virtual Compute Matrix (16 Nodes)
                </h2>
              </div>

              {selectedServerId ? (
                <div className="flex items-center gap-2 px-2.5 py-1 bg-sky-50 border border-sky-200/80 rounded-lg text-xs font-mono text-sky-800 animate-fadeIn">
                  <span className="w-2 h-2 rounded-full bg-sky-500 animate-ping" />
                  <span>Isolated: <strong>{selectedServerId}</strong> (100% Opacity, Others 20%)</span>
                  <button
                    onClick={handleClearSelection}
                    className="ml-1 text-sky-600 hover:text-sky-900 underline font-semibold cursor-pointer"
                  >
                    Reset
                  </button>
                </div>
              ) : (
                <span className="hidden md:inline-flex text-xs text-slate-500 font-mono">
                  (Click any CPU to isolate telemetry)
                </span>
              )}
            </div>

            {/* Right: Filters & Controls */}
            <div className="flex items-center gap-2.5">

              {/* Status Filter Tabs */}
              <div className="bg-slate-100 p-1 rounded-xl flex items-center text-xs font-medium">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                    statusFilter === 'all'
                      ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  All (16)
                </button>
                <button
                  onClick={() => setStatusFilter('active')}
                  className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                    statusFilter === 'active'
                      ? 'bg-white text-emerald-800 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Active
                </button>
                <button
                  onClick={() => setStatusFilter('idle')}
                  className={`px-3 py-1 rounded-lg transition-all cursor-pointer ${
                    statusFilter === 'idle'
                      ? 'bg-white text-slate-800 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Idle Sleep
                </button>
              </div>

              {/* Refresh Data */}
              <button
                onClick={loadData}
                disabled={loading}
                className="p-2 rounded-xl border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors cursor-pointer"
                title="Reload from backend"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-sky-600' : ''}`} />
              </button>
            </div>
          </div>

          {/* 5. MAIN INTERACTIVE SECTION: 4x4 GRID + DETAIL PANEL */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

            {/* LEFT / MAIN AREA: 4x4 CPU GRID (8 cols out of 12) */}
            <div className="lg:col-span-8 bg-white/70 backdrop-blur-sm rounded-3xl border border-slate-200/90 p-5 sm:p-6 shadow-xs">

              <div className="flex items-center justify-between text-xs text-slate-500 mb-4 pb-2 border-b border-slate-100 font-mono">
                <span>RACK-A (SRV 01-04) • RACK-B (05-08) • RACK-C (09-12) • RACK-D (13-16)</span>
                <span className="hidden sm:inline">2D High-Density Socket Layout</span>
              </div>

              {/* The 4x4 Neat Grid Layout with Dynamic Data Binding */}
              <div
                id="cpu-matrix-grid"
                className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 sm:gap-4"
              >
                {displayedServers.map((server) => (
                  <CpuChip
                    key={server.server_id}
                    server={server}
                    isSelected={selectedServerId === server.server_id}
                    hasSelection={selectedServerId !== null}
                    onSelect={handleCpuClick}
                  />
                ))}
              </div>

              {/* Color Legend */}
              <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                  <span>Optimal Load (&lt;55%)</span>
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block ml-2" />
                  <span>Standard (55-80%)</span>
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block ml-2" />
                  <span>High (&gt;80%)</span>
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block ml-2" />
                  <span>Idle Sleep</span>
                </div>

                <span className="font-mono text-[11px] text-slate-400">
                  {selectedServerId ? `Focusing on ${selectedServerId}` : 'Click any CPU to isolate (others drop to 20% opacity)'}
                </span>
              </div>
            </div>

            {/* RIGHT AREA: DETAILED INFORMATION PANEL (4 cols out of 12) */}
            <div className="lg:col-span-4 sticky top-20">
              <ServerDetailPanel
                server={selectedServer}
                onClose={handleClearSelection}
                onToggleStatus={handleToggleServerStatus}
                isUpdating={isUpdating}
              />
            </div>

          </div>

      {/* 6. MODAL BREAKDOWN OF ENERGY SAVINGS */}
      <EnergySavingsModal
        isOpen={isEnergyModalOpen}
        onClose={() => setIsEnergyModalOpen(false)}
        comparison={comparison}
      />

    </div>
  );
}
