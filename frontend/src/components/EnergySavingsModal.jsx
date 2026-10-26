import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { X, Zap, AlertTriangle, BarChart3 } from 'lucide-react';

const kwh = (v, digits = 4) => Number(v).toFixed(digits);
const signed = (v, digits = 1) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(digits)}`;

export default function EnergySavingsModal({ isOpen, onClose, comparison }) {
  useEffect(() => {
    if (!isOpen) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;
  const saving = comparison?.energy_saving;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/40 backdrop-blur-xs"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="energy-modal-title"
    >
      <div
        className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center">
              <Zap className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h2 id="energy-modal-title" className="text-lg font-bold text-slate-900 tracking-tight">
                Energy saved: DQN vs Min-Min
              </h2>
              <p className="text-xs text-slate-500">
                {saving
                  ? `Mean per run over ${comparison.seeds.length} held-out seeds (${comparison.seeds[0]}–${comparison.seeds[comparison.seeds.length - 1]}), sleep ${comparison.params.sleep_enabled ? 'on' : 'off'}`
                  : 'Measured from the latest multi-seed comparison'}
              </p>
            </div>
          </div>
          <button onClick={onClose} id="close-energy-modal" aria-label="Close modal"
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        {!saving ? (
          <div className="text-center py-8 space-y-3">
            <p className="text-sm text-slate-600">
              {comparison
                ? 'The latest comparison did not include DQN (weights unavailable). Train the DQN, then run a comparison.'
                : 'No comparison has been run yet, so there is no measured saving to show.'}
            </p>
            <Link to="/compare" onClick={onClose}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider text-white bg-sky-600 hover:bg-sky-500">
              <BarChart3 className="w-4 h-4" /> Run a comparison
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
              <div className="bg-emerald-50/80 border border-emerald-200/80 rounded-2xl p-4">
                <div className="text-xs font-semibold text-emerald-800">Energy saved</div>
                <div className="text-2xl font-extrabold font-mono text-emerald-950 mt-1">{kwh(saving.saved_kwh)}</div>
                <div className="text-[11px] font-mono text-emerald-800">kWh per run · {kwh(saving.policy_kwh)} vs {kwh(saving.baseline_kwh)}</div>
              </div>
              <div className="bg-sky-50/80 border border-sky-200/80 rounded-2xl p-4">
                <div className="text-xs font-semibold text-sky-800">Relative saving</div>
                <div className="text-2xl font-extrabold font-mono text-sky-950 mt-1">{signed(saving.saved_pct)}%</div>
                <div className="text-[11px] font-mono text-sky-800">of Min-Min energy</div>
              </div>
              <div className="bg-amber-50/80 border border-amber-200/80 rounded-2xl p-4">
                <div className="text-xs font-semibold text-amber-900 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> SLA cost
                </div>
                <div className="text-2xl font-extrabold font-mono text-amber-950 mt-1">{signed(saving.sla_cost)}</div>
                <div className="text-[11px] font-mono text-amber-900">
                  violations per run ({saving.sla_violations_policy.toFixed(1)} vs {saving.sla_violations_baseline.toFixed(1)})
                </div>
              </div>
            </div>

            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-2">Per-server breakdown (kWh per run)</h3>
            <div className="border border-slate-200 rounded-2xl overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200 bg-slate-50">
                    <th className="px-3 py-2 font-semibold">Server</th>
                    <th className="px-3 py-2 font-semibold text-right">Min-Min</th>
                    <th className="px-3 py-2 font-semibold text-right">DQN</th>
                    <th className="px-3 py-2 font-semibold text-right">Saved</th>
                    <th className="px-3 py-2 font-semibold text-right">DQN time asleep</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-slate-700">
                  {saving.per_server.map((s) => (
                    <tr key={s.server_id} className="border-b border-slate-100 last:border-0">
                      <td className="px-3 py-1.5 font-semibold text-slate-800">{s.server_id}</td>
                      <td className="px-3 py-1.5 text-right">{kwh(s.baseline_kwh, 5)}</td>
                      <td className="px-3 py-1.5 text-right">{kwh(s.policy_kwh, 5)}</td>
                      <td className={`px-3 py-1.5 text-right ${s.saved_kwh < 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
                        {signed(s.saved_kwh, 5)}
                      </td>
                      <td className="px-3 py-1.5 text-right">{(100 * s.policy_sleep_fraction).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-[11px] text-slate-500">
              IT energy only (no PUE multiplier). SLA violation = task finishing after arrival + {comparison.params.sla_slack} × its ideal runtime.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
