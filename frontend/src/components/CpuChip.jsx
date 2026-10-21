import React from 'react';
import { Cpu, Zap, Activity, Flame } from 'lucide-react';

export default function CpuChip({
  server,
  isSelected,
  hasSelection,
  onSelect
}) {
  const {
    server_id,
    capacity,
    current_utilization,
    status,
    temperature_c,
    rack_id
  } = server;

  const isIdle = status.toLowerCase() === 'idle';
  const util = Math.round(current_utilization);

  // Utilization color palette (soft blue/green tech accents)
  const getUtilColor = () => {
    if (isIdle || util === 0) return {
      badge: 'bg-slate-100 text-slate-600 border-slate-200',
      bar: 'bg-slate-300',
      ring: 'stroke-slate-300',
      text: 'text-slate-500'
    };
    if (util < 55) return {
      badge: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
      bar: 'bg-emerald-500',
      ring: 'stroke-emerald-500',
      text: 'text-emerald-700'
    };
    if (util < 85) return {
      badge: 'bg-sky-50 text-sky-700 border-sky-200/80',
      bar: 'bg-sky-500',
      ring: 'stroke-sky-500',
      text: 'text-sky-700'
    };
    return {
      badge: 'bg-amber-50 text-amber-700 border-amber-200/80',
      bar: 'bg-amber-500',
      ring: 'stroke-amber-500',
      text: 'text-amber-700'
    };
  };

  const colors = getUtilColor();

  // Opacity logic:
  // - If nothing is selected: 100% opacity
  // - If this chip is selected: 100% opacity + highlight
  // - If another chip is selected: 20% opacity (80% transparent)
  let opacityClass = 'opacity-100';
  if (hasSelection) {
    opacityClass = isSelected 
      ? 'opacity-100 ring-2 ring-sky-500 ring-offset-2 ring-offset-slate-50 shadow-md scale-[1.03] z-10' 
      : 'opacity-20 hover:opacity-40';
  }

  // Extract core count snippet from capacity (e.g. "64 vCPU" -> "64C")
  const coreMatch = capacity.match(/(\d+)\s*v?CPU/i);
  const coreDisplay = coreMatch ? `${coreMatch[1]}C` : 'x86';

  return (
    <div
      onClick={() => onSelect(server)}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      aria-label={`Server ${server_id}, Utilization: ${current_utilization}%, Status: ${status}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(server);
        }
      }}
      id={`cpu-chip-${server_id}`}
      className={`group relative p-2.5 bg-white rounded-xl border transition-all duration-300 cursor-pointer select-none ${
        isSelected 
          ? 'border-sky-400 bg-sky-50/20' 
          : 'border-slate-200/90 hover:border-slate-300 hover:shadow-xs'
      } ${opacityClass}`}
    >
      {/* Decorative CPU Perimeter Pins (Top & Bottom) */}
      <div className="absolute -top-1 left-3 right-3 h-1 cpu-socket-pin-h opacity-40 group-hover:opacity-75 transition-opacity" />
      <div className="absolute -bottom-1 left-3 right-3 h-1 cpu-socket-pin-h opacity-40 group-hover:opacity-75 transition-opacity" />
      <div className="absolute top-3 bottom-3 -left-1 w-1 cpu-socket-pin-v opacity-40 group-hover:opacity-75 transition-opacity" />
      <div className="absolute top-3 bottom-3 -right-1 w-1 cpu-socket-pin-v opacity-40 group-hover:opacity-75 transition-opacity" />

      {/* Main CPU Integrated Heat Spreader (IHS) Container */}
      <div className="metallic-ihs rounded-lg p-2.5 border border-slate-200 flex flex-col justify-between h-[150px] relative overflow-hidden">
        
        {/* Alignment corner notch (Physical CPU socket index mark) */}
        <div className="absolute top-0 left-0 w-3 h-3 bg-amber-400/30 border-r border-b border-amber-500/30 rounded-br-sm" />

        {/* Top Header: ID & Core Spec */}
        <div className="flex items-center justify-between pl-2">
          <div className="flex items-center gap-1.5">
            <span className="font-mono font-bold text-xs text-slate-800 tracking-wider">
              {server_id}
            </span>
            <span className="text-[10px] font-mono px-1 py-0.2 bg-slate-200/70 text-slate-600 rounded">
              {coreDisplay}
            </span>
          </div>

          {/* Status Dot */}
          <div className="flex items-center gap-1">
            <span
              className={`w-2 h-2 rounded-full ${
                isIdle 
                  ? 'bg-slate-400' 
                  : 'bg-emerald-500 ring-2 ring-emerald-200 animate-tech-pulse'
              }`}
            />
            <span className="text-[9px] font-mono uppercase font-semibold text-slate-500">
              {status}
            </span>
          </div>
        </div>

        {/* Center: Circular Utilization Gauge & Figure */}
        <div className="flex items-center justify-center my-1">
          <div className="relative w-16 h-16 flex items-center justify-center">
            {/* SVG Progress Ring */}
            <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
              {/* Background track */}
              <path
                className="stroke-slate-200"
                strokeWidth="3.2"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              {/* Animated Progress path */}
              <path
                className={`${colors.ring} transition-all duration-700 ease-out`}
                strokeDasharray={`${util}, 100`}
                strokeWidth="3.2"
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>

            {/* Value in Center */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className={`text-sm font-bold font-mono tracking-tight ${colors.text}`}>
                {isIdle ? '0%' : `${util}%`}
              </span>
              <span className="text-[8px] uppercase tracking-wider text-slate-600 font-semibold">
                CPU
              </span>
            </div>
          </div>
        </div>

        {/* Footer: Rack Location & Temperature / Workload */}
        <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono border-t border-slate-200/70 pt-1.5">
          <span className="text-slate-500">{rack_id || 'RACK-01'}</span>
          <div className="flex items-center gap-0.5 text-slate-600">
            {isIdle ? (
              <span className="text-emerald-700 font-semibold bg-emerald-50 px-1 rounded">SLEEP</span>
            ) : (
              <>
                <Flame className="w-2.5 h-2.5 text-slate-400" />
                <span>{temperature_c ? `${Math.round(temperature_c)}°C` : '42°C'}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Selected Indicator Badge */}
      {isSelected && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-sky-600 text-white text-[9px] font-bold uppercase rounded-full shadow-xs tracking-wider">
          Inspecting
        </div>
      )}
    </div>
  );
}
