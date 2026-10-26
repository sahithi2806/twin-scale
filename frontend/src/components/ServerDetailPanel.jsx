import React from 'react';
import {
  X,
  Cpu,
  Server,
  Thermometer,
  Zap,
  Layers,
  Activity,
  Power,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';

export default function ServerDetailPanel({
  server,
  onClose,
  onToggleStatus,
  isUpdating
}) {
  if (!server) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 flex flex-col items-center justify-center text-center h-full min-h-[380px] shadow-xs">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-3 border border-slate-200/60">
          <Cpu className="w-7 h-7 stroke-[1.5]" />
        </div>
        <h3 className="font-semibold text-slate-700 text-base mb-1">Select a Server Node</h3>
        <p className="text-xs text-slate-500 max-w-[220px] leading-relaxed">
          Click any CPU chip in the 4×4 grid to isolate its simulation telemetry and scheduler metrics.
        </p>
        <div className="mt-4 px-3 py-1.5 bg-sky-50 border border-sky-100 rounded-lg text-[11px] font-mono text-sky-700">
          Min-Min Telemetry Active
        </div>
      </div>
    );
  }

  const {
    server_id,
    capacity,
    current_utilization = 0.0,
    status = 'active',
    rack_id,
    temperature_c = 48.0,
    power_draw_w = 320.0,
    active_workloads = 0,
    power_state = 'on'
  } = server;

  const isIdle = status.toLowerCase() === 'idle';
  const util = Math.round(current_utilization);

  return (
    <div
      id="server-detail-panel"
      className="bg-white rounded-2xl border border-slate-200 shadow-md p-5 flex flex-col justify-between transition-all"
    >
      <div>
        {/* Header with Server ID and Dismiss button */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 p-0.5 shadow-xs">
              <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
                <Cpu className="w-5 h-5 text-sky-600" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-mono font-bold text-lg text-slate-900 tracking-tight">
                  {server_id}
                </h3>
                <span
                  className={`text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded-full border ${
                    isIdle
                      ? 'bg-slate-100 text-slate-600 border-slate-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  }`}
                >
                  {status}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">Location: {rack_id || 'RACK-01'}</p>
            </div>
          </div>

          <button
            onClick={onClose}
            id="close-detail-panel"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Reset focus and view all CPUs"
            aria-label="Close detail panel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Utilization Progress */}
        <div className="my-4 p-3.5 bg-slate-50/80 rounded-xl border border-slate-100">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-sky-600" />
              <span>Simulated Utilization</span>
            </span>
            <span className="font-mono font-bold text-sm text-slate-900">
              {current_utilization.toFixed(1)}%
            </span>
          </div>

          <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isIdle ? 'bg-slate-300 w-0' :
                util < 55 ? 'bg-emerald-500' :
                util < 85 ? 'bg-sky-500' : 'bg-amber-500'
              }`}
              style={{ width: `${Math.min(util, 100)}%` }}
            />
          </div>

          <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1.5">
            <span>0% (Idle threshold)</span>
            <span>{power_state === 'sleep' ? 'Asleep most of the last run' : 'Avg while awake, last run'}</span>
            <span>100% (Peak)</span>
          </div>
        </div>

        {/* Hardware Capacity Specs */}
        <div className="mb-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
            Hardware Capacity
          </span>
          <div className="mt-1.5 p-3 bg-white border border-slate-200/90 rounded-xl flex items-center gap-3">
            <Server className="w-4 h-4 text-slate-400 shrink-0" />
            <div className="overflow-hidden">
              <p className="font-mono font-medium text-xs text-slate-800 truncate">
                {capacity}
              </p>
              <p className="text-[11px] text-slate-600">Min-Min Virtual Target Instance</p>
            </div>
          </div>
        </div>

        {/* Real-time Telemetry Grid */}
        <div className="grid grid-cols-2 gap-2.5 mb-4">

          {/* Temperature */}
          <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs mb-1">
              <Thermometer className="w-3.5 h-3.5 text-rose-500" />
              <span>Thermal Sensor</span>
            </div>
            <div className="font-mono font-bold text-slate-800 text-sm">
              {temperature_c.toFixed(1)}°C
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {temperature_c > 65 ? 'Elevated Heat' : 'Normal Spec'}
            </div>
          </div>

          {/* Power Draw */}
          <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs mb-1">
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              <span>Power Draw</span>
            </div>
            <div className="font-mono font-bold text-slate-800 text-sm">
              {power_draw_w.toFixed(0)} W
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5 font-mono">
              Average over the last run
            </div>
          </div>

          {/* Tasks Assigned */}
          <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs mb-1">
              <Layers className="w-3.5 h-3.5 text-sky-500" />
              <span>Tasks Mapped</span>
            </div>
            <div className="font-mono font-bold text-slate-800 text-sm">
              {active_workloads} Tasks
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              Min-Min assigned
            </div>
          </div>

          {/* Twin Sync Status */}
          <div className="p-3 bg-slate-50/70 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 text-xs mb-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Twin Sync</span>
            </div>
            <div className="font-mono font-semibold text-emerald-700 text-xs">
              Synchronized
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              SQLite Transaction
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons: State Toggle and Deselect */}
      <div className="pt-3 border-t border-slate-100 space-y-2">
        <button
          onClick={() => onToggleStatus(server_id)}
          disabled={isUpdating}
          id="toggle-server-status-btn"
          className={`w-full py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs ${
            isIdle
              ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
              : 'bg-amber-600 hover:bg-amber-700 text-white'
          } ${isUpdating ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          {isUpdating ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Power className="w-3.5 h-3.5" />
          )}
          <span>
            {isIdle ? 'Power On Node (Set Active)' : 'Consolidate Node (Set Idle)'}
          </span>
        </button>

        <button
          onClick={onClose}
          id="view-all-servers-btn"
          className="w-full py-2 px-3 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
        >
          View All Servers (100% Opacity)
        </button>
      </div>
    </div>
  );
}
