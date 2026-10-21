import React, { useEffect } from 'react';
import { 
  X, 
  Zap, 
  TrendingDown, 
  DollarSign, 
  Leaf, 
  Wind, 
  Server, 
  Layers, 
  ShieldCheck 
} from 'lucide-react';

export default function EnergySavingsModal({ 
  isOpen, 
  onClose, 
  savingsData 
}) {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const data = savingsData || {
    total_energy_saved_kwh: 4860.5,
    total_cost_saved_usd: 680.47,
    carbon_reduction_kg: 2041.4,
    pue_ratio: 1.15,
    idle_servers_consolidated: 4,
    cooling_efficiency_boost_pct: 24.8,
    breakdown: []
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/40 backdrop-blur-xs transition-opacity duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="energy-modal-title"
    >
      <div 
        className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full p-6 sm:p-8 transform transition-all overflow-hidden relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Subtle Tech Glow behind header */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-emerald-100/60 to-sky-100/40 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

        {/* Modal Header */}
        <div className="flex items-start justify-between relative z-10 mb-6">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 p-0.5 shadow-md">
              <div className="w-full h-full bg-white rounded-[14px] flex items-center justify-center">
                <Zap className="w-6 h-6 text-emerald-600 fill-emerald-500/20" />
              </div>
            </div>
            <div>
              <h2 id="energy-modal-title" className="text-xl font-bold text-slate-900 tracking-tight">
                Data Center Energy Optimization
              </h2>
              <p className="text-xs text-slate-500">
                Digital Twin real-time thermal & workload consolidation breakdown
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            id="close-energy-modal"
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Highlight KPI Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mb-6 relative z-10">
          
          {/* Total Saved kWh */}
          <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-2xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-emerald-700 text-xs font-semibold">
              <span>Energy Conserved</span>
              <TrendingDown className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="my-2">
              <span className="text-2xl font-bold font-mono text-emerald-900">
                {data.total_energy_saved_kwh.toLocaleString()}
              </span>
              <span className="text-xs text-emerald-700 font-medium ml-1">kWh / mo</span>
            </div>
            <p className="text-[11px] text-emerald-700">~24.8% reduction vs baseline</p>
          </div>

          {/* Cost Savings */}
          <div className="bg-sky-50/80 border border-sky-200/80 rounded-2xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-sky-700 text-xs font-semibold">
              <span>Utility Cost Saved</span>
              <DollarSign className="w-4 h-4 text-sky-600" />
            </div>
            <div className="my-2">
              <span className="text-2xl font-bold font-mono text-sky-900">
                ${data.total_cost_saved_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-xs text-sky-700 font-medium ml-1">/ month</span>
            </div>
            <p className="text-[11px] text-sky-700">Calculated @ $0.14 / kWh</p>
          </div>

          {/* Carbon Offset */}
          <div className="bg-teal-50/80 border border-teal-200/80 rounded-2xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-teal-700 text-xs font-semibold">
              <span>Carbon Abatement</span>
              <Leaf className="w-4 h-4 text-teal-600" />
            </div>
            <div className="my-2">
              <span className="text-2xl font-bold font-mono text-teal-900">
                {data.carbon_reduction_kg.toLocaleString()}
              </span>
              <span className="text-xs text-teal-700 font-medium ml-1">kg CO₂e</span>
            </div>
            <p className="text-[11px] text-teal-700">Eq. to ~97 mature trees / yr</p>
          </div>
        </div>

        {/* Detailed Breakdown Accordion / List */}
        <div className="relative z-10 mb-6">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
            Algorithmic Optimization Pillars
          </h3>

          <div className="space-y-2.5">
            {data.breakdown && data.breakdown.length > 0 ? (
              data.breakdown.map((item, idx) => (
                <div 
                  key={idx} 
                  className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl flex items-start gap-3 hover:bg-slate-100/60 transition-colors"
                >
                  <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center shrink-0 mt-0.5 text-slate-600">
                    {idx === 0 ? <Server className="w-4 h-4 text-emerald-600" /> :
                     idx === 1 ? <Wind className="w-4 h-4 text-sky-600" /> :
                     <Layers className="w-4 h-4 text-indigo-600" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-800">{item.category}</h4>
                      <span className="font-mono text-xs font-bold text-emerald-700">
                        +{item.amount_kwh.toLocaleString()} kWh (${item.saved_usd.toFixed(2)})
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400">Loading breakdown metrics...</p>
            )}
          </div>
        </div>

        {/* PUE Efficiency Comparison Bar */}
        <div className="bg-slate-50 border border-slate-200/90 rounded-2xl p-4 relative z-10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Power Usage Effectiveness (PUE) Ratio</span>
            </span>
            <span className="font-mono font-bold text-xs px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">
              Twin PUE: {data.pue_ratio} (Target: &lt;1.20)
            </span>
          </div>

          <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden flex">
            <div className="bg-emerald-500 h-full" style={{ width: '68%' }} title="Twin Efficiency" />
            <div className="bg-slate-300 h-full" style={{ width: '32%' }} title="Legacy Overhead" />
          </div>

          <div className="flex justify-between text-[10px] text-slate-600 font-mono mt-1.5">
            <span>Ideal PUE 1.0 (100% IT Load)</span>
            <span>Digital Twin: 1.15</span>
            <span>Industry Avg: 1.58</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="mt-6 flex justify-end relative z-10">
          <button
            onClick={onClose}
            id="dismiss-energy-modal-btn"
            className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition-all shadow-xs cursor-pointer"
          >
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  );
}
