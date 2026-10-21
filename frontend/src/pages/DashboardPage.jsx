import React, { useState, useEffect } from 'react';
import { 
  fetchServers, 
  fetchEnergySavings, 
  toggleServerStatus, 
  FALLBACK_16_SERVERS, 
  FALLBACK_ENERGY_SAVINGS 
} from '../services/api';

import StatsBar from '../components/StatsBar';
import CpuChip from '../components/CpuChip';
import ServerDetailPanel from '../components/ServerDetailPanel';
import EnergySavingsModal from '../components/EnergySavingsModal';

import { 
  RefreshCw, 
  SlidersHorizontal, 
  Zap, 
  Eye, 
  Grid3X3, 
  Play, 
  Pause, 
  Info,
  CheckCircle2,
  Server
} from 'lucide-react';

export default function DashboardPage() {
  const [servers, setServers] = useState([]);
  const [savingsData, setSavingsData] = useState(null);
  const [selectedServerId, setSelectedServerId] = useState(null);
  const [isEnergyModalOpen, setIsEnergyModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'active' | 'idle'
  const [isLiveSimulating, setIsLiveSimulating] = useState(false);

  // Load servers and savings from backend API on mount
  const loadData = async () => {
    setLoading(true);
    try {
      const [serversRes, savingsRes] = await Promise.all([
        fetchServers(),
        fetchEnergySavings()
      ]);
      setServers(serversRes.data || FALLBACK_16_SERVERS);
      setSavingsData(savingsRes.data || FALLBACK_ENERGY_SAVINGS);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
      setServers(FALLBACK_16_SERVERS);
      setSavingsData(FALLBACK_ENERGY_SAVINGS);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Live simulation tick: subtly fluctuates active utilization for realism
  useEffect(() => {
    if (!isLiveSimulating) return;

    const interval = setInterval(() => {
      setServers((prevServers) =>
        prevServers.map((srv) => {
          if (srv.status.toLowerCase() === 'idle') return srv;
          // Subtly fluctuate utilization +/- 1.5%
          const delta = (Math.random() - 0.48) * 3;
          const nextUtil = Math.min(99.5, Math.max(15, srv.current_utilization + delta));
          const nextTemp = Math.min(72, Math.max(38, srv.temperature_c + (delta * 0.1)));
          return {
            ...srv,
            current_utilization: Number(nextUtil.toFixed(1)),
            temperature_c: Number(nextTemp.toFixed(1))
          };
        })
      );
    }, 2000);

    return () => clearInterval(interval);
  }, [isLiveSimulating]);

  // Handle CPU click: toggle or select
  const handleCpuClick = (server) => {
    if (selectedServerId === server.server_id) {
      // If clicking already selected, deselect to restore all to 100%
      setSelectedServerId(null);
    } else {
      setSelectedServerId(server.server_id);
    }
  };

  // Clear selection handler
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
        // Fallback local toggle if backend isn't reachable
        setServers((prev) =>
          prev.map((s) => {
            if (s.server_id === serverId) {
              const newStatus = s.status === 'active' ? 'idle' : 'active';
              return {
                ...s,
                status: newStatus,
                current_utilization: newStatus === 'idle' ? 0.0 : 68.5,
                active_workloads: newStatus === 'idle' ? 0 : 15,
                temperature_c: newStatus === 'idle' ? 33.2 : 54.0,
                power_draw_w: newStatus === 'idle' ? 70.0 : 340.0
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

  // Selected server object
  const selectedServer = servers.find((s) => s.server_id === selectedServerId);

  // Filtered servers (for grid view)
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
        onOpenEnergyModal={() => setIsEnergyModalOpen(true)}
      />

      {/* 2. DASHBOARD CONTROL BAR */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-4 mb-6 flex flex-wrap items-center justify-between gap-4">
        
        {/* Left: View & Focus State Indicator */}
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
            <span className="hidden md:inline-flex text-xs text-slate-600 font-mono">
              (Click any CPU to isolate)
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

          {/* Live Simulation Toggle */}
          <button
            onClick={() => setIsLiveSimulating(!isLiveSimulating)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all cursor-pointer ${
              isLiveSimulating
                ? 'bg-sky-50 border-sky-300 text-sky-700'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
            title="Toggle live telemetry fluctuation simulation"
          >
            {isLiveSimulating ? (
              <>
                <Pause className="w-3.5 h-3.5 text-sky-600" />
                <span>Pause Live</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 text-slate-500" />
                <span>Simulate Live</span>
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

      {/* 3. MAIN INTERACTIVE SECTION: 4x4 GRID + DETAIL PANEL */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT / MAIN AREA: 4x4 CPU GRID (8 cols out of 12) */}
        <div className="lg:col-span-8 bg-white/70 backdrop-blur-sm rounded-3xl border border-slate-200/90 p-5 sm:p-6 shadow-xs">
          
          {/* Rack Row Headers & Information */}
          <div className="flex items-center justify-between text-xs text-slate-600 mb-4 pb-2 border-b border-slate-100 font-mono">
            <span>RACK-A (SRV 01-04) • RACK-B (05-08) • RACK-C (09-12) • RACK-D (13-16)</span>
            <span className="hidden sm:inline">2D High-Density Socket Layout</span>
          </div>

          {/* The 4x4 Neat Grid Layout */}
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

          {/* Helper Instructions below grid */}
          <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-600 gap-2">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>Optimal Load (&lt;55%)</span>
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block ml-2" />
              <span>Standard (55-85%)</span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block ml-2" />
              <span>Heavy (&gt;85%)</span>
              <span className="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block ml-2" />
              <span>Idle</span>
            </div>

            <span className="font-mono text-[11px] text-slate-600">
              {selectedServerId ? `Focusing on ${selectedServerId}` : 'Hover or click any socket'}
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

      {/* 4. MODAL BREAKDOWN OF ENERGY SAVINGS */}
      <EnergySavingsModal
        isOpen={isEnergyModalOpen}
        onClose={() => setIsEnergyModalOpen(false)}
        savingsData={savingsData}
      />

    </div>
  );
}
