import React, { useState, useEffect } from 'react';
import { 
  fetchServers, 
  fetchEnergySavings, 
  toggleServerStatus, 
  runSimulation,
  fetchPolicies,
  fetchLatestSimulation,
  FALLBACK_16_SERVERS, 
  FALLBACK_ENERGY_SAVINGS 
} from '../services/api';

import StatsBar from '../components/StatsBar';
import CpuChip from '../components/CpuChip';
import ServerDetailPanel from '../components/ServerDetailPanel';
import EnergySavingsModal from '../components/EnergySavingsModal';
import SimulationControlPanel from '../components/SimulationControlPanel';
import CompareResultsSection from '../components/CompareResultsSection';

import { 
  RefreshCw, 
  Grid3X3, 
  Play, 
  Pause, 
  CheckCircle2, 
  Zap, 
  Sliders, 
  Clock,
  Sparkles,
  Info,
  BarChart3
} from 'lucide-react';

export default function DashboardPage() {
  const [activeView, setActiveView] = useState('matrix'); // 'matrix' | 'compare'
  const [servers, setServers] = useState([]);
  const [savingsData, setSavingsData] = useState(null);
  const [latestSim, setLatestSim] = useState(null);
  const [selectedServerId, setSelectedServerId] = useState(null);
  const [isEnergyModalOpen, setIsEnergyModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'active' | 'idle'
  const [isLiveFluctuation, setIsLiveFluctuation] = useState(false);
  const [simNotification, setSimNotification] = useState(null);
  const [simProgress, setSimProgress] = useState(null);
  const [simError, setSimError] = useState(null);
  const [policyStatus, setPolicyStatus] = useState(null);

  // Load servers, savings, and latest simulation on initial mount
  const loadData = async () => {
    setLoading(true);
    fetchPolicies().then(setPolicyStatus).catch(() => setPolicyStatus(null));
    try {
      const [serversRes, savingsRes, latestSimRes] = await Promise.all([
        fetchServers(),
        fetchEnergySavings(),
        fetchLatestSimulation()
      ]);
      setServers(serversRes.data || FALLBACK_16_SERVERS);
      setSavingsData(savingsRes.data || FALLBACK_ENERGY_SAVINGS);
      if (latestSimRes) {
        setLatestSim(latestSimRes);
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
      setServers(FALLBACK_16_SERVERS);
      setSavingsData(FALLBACK_ENERGY_SAVINGS);
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

  // Live fluctuation simulation tick (toggleable)
  useEffect(() => {
    if (!isLiveFluctuation) return;

    const interval = setInterval(() => {
      setServers((prevServers) =>
        prevServers.map((srv) => {
          if (srv.status.toLowerCase() === 'idle') return srv;
          const delta = (Math.random() - 0.48) * 2.5;
          const nextUtil = Math.min(98.0, Math.max(15.0, srv.current_utilization + delta));
          return {
            ...srv,
            current_utilization: Number(nextUtil.toFixed(1))
          };
        })
      );
    }, 2000);

    return () => clearInterval(interval);
  }, [isLiveFluctuation]);

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
      if (updated) {
        setServers((prev) =>
          prev.map((s) => (s.server_id === serverId ? updated : s))
        );
      } else {
        setServers((prev) =>
          prev.map((s) => {
            if (s.server_id === serverId) {
              const newStatus = s.status === 'active' ? 'idle' : 'active';
              return {
                ...s,
                status: newStatus,
                current_utilization: newStatus === 'idle' ? 0.0 : 65.0,
                active_workloads: newStatus === 'idle' ? 0 : 12,
                flags: newStatus === 'idle' ? 'IDLE_CONSOLIDATED' : 'OPTIMAL_LOAD'
              };
            }
            return s;
          })
        );
      }
    } catch (err) {
      console.error("Error toggling server status:", err);
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
        savingsData={savingsData}
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
            {activeView !== 'compare' && (
              <button
                onClick={() => setActiveView('compare')}
                className="text-xs text-indigo-700 hover:text-indigo-900 underline font-semibold cursor-pointer font-mono"
              >
                View Comparison →
              </button>
            )}
            <button
              onClick={() => setSimNotification(null)}
              className="text-xs text-emerald-700 hover:text-emerald-900 underline font-semibold cursor-pointer"
            >
              Dismiss
            </button>
          </div>
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

      {/* 4. VIEW SELECTION TABS: 4x4 Matrix vs Compare Results */}
      <div className="flex items-center justify-between mb-6 bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/80">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setActiveView('matrix')}
            id="tab-view-matrix"
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer ${
              activeView === 'matrix'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Grid3X3 className="w-4 h-4 text-sky-600" />
            <span>4×4 Compute Matrix</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-100 rounded text-slate-600">
              16 Sockets
            </span>
          </button>

          <button
            onClick={() => setActiveView('compare')}
            id="tab-view-compare"
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer ${
              activeView === 'compare'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4 text-indigo-600" />
            <span>Compare Results</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded border border-indigo-200">
              Min-Min vs DQN
            </span>
          </button>
        </div>

        <div className="hidden sm:flex items-center gap-2 pr-3 text-xs font-mono text-slate-500">
          <span>{activeView === 'matrix' ? 'Real-Time Telemetry & Server Sockets' : 'Comparative Analytics & Graphs'}</span>
        </div>
      </div>

      {/* CONDITIONAL VIEW RENDERING: 4x4 Matrix Grid vs Compare Results */}
      {activeView === 'compare' ? (
        <CompareResultsSection
          onApplySimulationResult={(simData) => {
            if (simData.servers && simData.servers.length > 0) {
              setServers(simData.servers);
            }
            setLatestSim(simData);
          }}
        />
      ) : (
        <>
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

              {/* Live Fluctuation Toggle */}
              <button
                onClick={() => setIsLiveFluctuation(!isLiveFluctuation)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all cursor-pointer ${
                  isLiveFluctuation
                    ? 'bg-sky-50 border-sky-300 text-sky-700'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
                title="Toggle micro-fluctuation simulation"
              >
                {isLiveFluctuation ? (
                  <>
                    <Pause className="w-3.5 h-3.5 text-sky-600" />
                    <span>Pause Pulse</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 text-slate-500" />
                    <span>Micro Pulse</span>
                  </>
                )}
              </button>

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
        </>
      )}

      {/* 6. MODAL BREAKDOWN OF ENERGY SAVINGS */}
      <EnergySavingsModal
        isOpen={isEnergyModalOpen}
        onClose={() => setIsEnergyModalOpen(false)}
        savingsData={savingsData}
        latestSim={latestSim}
      />

    </div>
  );
}
