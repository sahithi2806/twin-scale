import React from 'react';
import { Zap, Server, Activity, ArrowUpRight, ShieldCheck, Thermometer } from 'lucide-react';

export default function StatsBar({
  servers = [],
  savingsData,
  onOpenEnergyModal
}) {
  const totalServers = servers.length;
  const activeServers = servers.filter(s => s.status.toLowerCase() === 'active').length;
  const idleServers = totalServers - activeServers;
  
  const avgUtilization = totalServers > 0
    ? (servers.reduce((acc, s) => acc + s.current_utilization, 0) / totalServers).toFixed(1)
    : '0.0';

  const avgTemp = totalServers > 0
    ? (servers.reduce((acc, s) => acc + (s.temperature_c || 45), 0) / totalServers).toFixed(1)
    : '45.0';

  const totalSavedKwh = savingsData?.total_energy_saved_kwh 
    ? savingsData.total_energy_saved_kwh.toLocaleString() 
    : '4,860';

  const totalSavedUsd = savingsData?.total_cost_saved_usd 
    ? savingsData.total_cost_saved_usd.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }) 
    : '680';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      
      {/* 1. PROMINENT CLICKABLE ENERGY SAVED STATS CARD */}
      <div
        onClick={onOpenEnergyModal}
        id="stat-card-energy-saved"
        role="button"
        tabIndex={0}
        aria-label="Energy Saved Card - Click to open savings breakdown"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onOpenEnergyModal();
          }
        }}
        className="group relative bg-gradient-to-br from-emerald-50 via-white to-teal-50/40 rounded-2xl p-4 border-2 border-emerald-300 hover:border-emerald-500 hover:shadow-md transition-all duration-300 cursor-pointer overflow-hidden shadow-xs"
      >
        {/* Glow corner */}
        <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-400/10 rounded-full blur-xl group-hover:bg-emerald-400/20 transition-all pointer-events-none" />

        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform">
              <Zap className="w-4 h-4 fill-white" />
            </div>
            <div>
              <span className="text-xs font-bold text-emerald-950 uppercase tracking-wide">
                Energy Saved
              </span>
              <span className="block text-[10px] text-emerald-700 font-medium">Digital Twin Net</span>
            </div>
          </div>

          <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full group-hover:bg-emerald-200 transition-colors">
            <span>Breakdown</span>
            <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </div>
        </div>

        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl sm:text-3xl font-extrabold font-mono text-emerald-950 tracking-tight">
            +{totalSavedKwh}
          </span>
          <span className="text-xs font-semibold text-emerald-700 font-mono">kWh/mo</span>
        </div>

        <div className="mt-2 pt-2 border-t border-emerald-100 flex items-center justify-between text-[11px] text-emerald-800">
          <span>Est. <strong>${totalSavedUsd}</strong> Saved</span>
          <span className="font-semibold text-emerald-700">PUE 1.15 ★</span>
        </div>
      </div>

      {/* 2. Cluster Workload & Avg Utilization */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-500 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Cluster Avg Load
          </span>
          <div className="w-7 h-7 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
            <Activity className="w-4 h-4" />
          </div>
        </div>

        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 tracking-tight">
            {avgUtilization}%
          </span>
          <span className="text-xs text-sky-600 font-medium font-mono">Target: &lt;80%</span>
        </div>

        <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className="bg-sky-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(avgUtilization, 100)}%` }}
          />
        </div>
      </div>

      {/* 3. Virtual Node Topology */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-500 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Virtual Server Fleet
          </span>
          <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
            <Server className="w-4 h-4" />
          </div>
        </div>

        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 tracking-tight">
            16
          </span>
          <span className="text-xs text-slate-600 font-mono">Sockets</span>
        </div>

        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono">
          <span className="text-emerald-700 font-semibold">{activeServers} Active</span>
          <span className="text-slate-600 font-semibold">{idleServers} Idle Sleep</span>
        </div>
      </div>

      {/* 4. Thermal & Cooling Performance */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs flex flex-col justify-between">
        <div className="flex items-center justify-between text-slate-500 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Thermal Twin Mean
          </span>
          <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center">
            <Thermometer className="w-4 h-4" />
          </div>
        </div>

        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 tracking-tight">
            {avgTemp}°C
          </span>
          <span className="text-xs text-emerald-700 font-medium">Safe Margin</span>
        </div>

        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-600">
          <span>AI Chilled Airflow</span>
          <span className="font-mono text-emerald-700 font-semibold">Active</span>
        </div>
      </div>

    </div>
  );
}
