import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ErrorBar, Cell, ResponsiveContainer } from 'recharts';
import { BarChart3, Play, RefreshCw, Info, Moon } from 'lucide-react';
import { fetchLatestComparison, runComparison } from '../services/api';

const POLICY_META = {
  'min-min': { label: 'Min-Min', color: '#2a78d6' },
  'power-aware': { label: 'Power-aware', color: '#eb6834' },
  dqn: { label: 'DQN', color: '#1baf7a' }
};

const METRICS = [
  { key: 'total_energy_kwh', label: 'Energy', unit: 'kWh', digits: 4, lowerIsBetter: true },
  { key: 'makespan', label: 'Completion time', unit: 's', digits: 1, lowerIsBetter: true },
  { key: 'avg_utilization', label: 'CPU utilization (awake servers)', unit: '%', digits: 1, lowerIsBetter: false },
  { key: 'sla_violations', label: 'SLA violations', unit: 'tasks', digits: 1, lowerIsBetter: true }
];

const fmt = (v, digits) => (v == null ? '—' : Number(v).toFixed(digits));

function MetricTooltip({ active, payload, metric }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-md px-3 py-2 text-xs font-mono text-slate-700">
      <div className="flex items-center gap-1.5 font-semibold text-slate-900">
        <span className="w-2 h-2 rounded-sm" style={{ background: d.color }} />
        {d.label}
      </div>
      <div className="mt-0.5">
        {fmt(d.mean, metric.digits)} ± {fmt(d.std, metric.digits)} {metric.unit}
      </div>
    </div>
  );
}

function MetricChart({ metric, policies, summary }) {
  const data = policies.map((p) => ({
    policy: p,
    label: POLICY_META[p]?.label ?? p,
    color: POLICY_META[p]?.color ?? '#64748b',
    mean: summary[p][metric.key].mean,
    std: summary[p][metric.key].std
  }));
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs">
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="text-sm font-bold text-slate-800">{metric.label}</h3>
        <span className="text-[11px] font-mono text-slate-500">
          mean ± std, {metric.unit} · {metric.lowerIsBetter ? 'lower is better' : 'higher means more consolidation'}
        </span>
      </div>
      <div className="h-52" role="img" aria-label={`${metric.label} by scheduler`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap="30%">
            <CartesianGrid vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: '#cbd5e1' }} tick={{ fontSize: 11, fill: '#475569' }} />
            <YAxis tickLine={false} axisLine={false} width={56} tick={{ fontSize: 11, fill: '#64748b' }}
              domain={[0, 'auto']} allowDataOverflow
              tickFormatter={(v) => Number(v).toFixed(metric.digits > 2 ? 3 : 0)} />
            <Tooltip cursor={{ fill: '#f1f5f9' }} content={<MetricTooltip metric={metric} />} />
            <Bar dataKey="mean" radius={[4, 4, 0, 0]} isAnimationActive={false}>
              {data.map((d) => <Cell key={d.policy} fill={d.color} />)}
              <ErrorBar dataKey="std" width={8} strokeWidth={1.5} stroke="#334155" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function SummaryTable({ comparison }) {
  const { policies, summary } = comparison;
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200">
            <th className="px-4 py-2.5 font-semibold">Scheduler</th>
            {METRICS.map((m) => (
              <th key={m.key} className="px-4 py-2.5 font-semibold text-right whitespace-nowrap">{m.label} ({m.unit})</th>
            ))}
            <th className="px-4 py-2.5 font-semibold text-right whitespace-nowrap">Energy vs Min-Min</th>
          </tr>
        </thead>
        <tbody className="font-mono">
          {policies.map((p) => {
            const s = summary[p];
            const saving = s.vs_baseline_pct?.total_energy_kwh;
            return (
              <tr key={p} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2.5 font-sans font-semibold text-slate-800 whitespace-nowrap">
                  <span className="inline-block w-2.5 h-2.5 rounded-sm mr-2 align-middle" style={{ background: POLICY_META[p]?.color }} />
                  {POLICY_META[p]?.label ?? p}
                </td>
                {METRICS.map((m) => (
                  <td key={m.key} className="px-4 py-2.5 text-right text-slate-700 whitespace-nowrap">
                    {fmt(s[m.key].mean, m.digits)} <span className="text-slate-400">± {fmt(s[m.key].std, m.digits)}</span>
                  </td>
                ))}
                <td className="px-4 py-2.5 text-right whitespace-nowrap text-slate-800">
                  {p === 'min-min' ? 'baseline' : `${saving >= 0 ? '−' : '+'}${Math.abs(saving).toFixed(1)}%`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function ComparePage() {
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({ n_seeds: 10, num_tasks: 200, sleep_enabled: true, sla_slack: 1.5 });

  useEffect(() => {
    fetchLatestComparison()
      .then(setComparison)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleRun = async (e) => {
    e.preventDefault();
    setRunning(true);
    setError(null);
    try {
      setComparison(await runComparison(form));
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const set = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : Number(e.target.value);
    setForm((f) => ({ ...f, [key]: value }));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="bg-white rounded-3xl border border-slate-200/90 p-5 sm:p-6 shadow-xs">
        <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 text-white flex items-center justify-center">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-bold text-slate-900 text-sm">Compare Results</h1>
            <p className="text-xs text-slate-500">Every scheduler runs on the same held-out seeds (1000+), never seen in DQN training.</p>
          </div>
        </div>

        <form onSubmit={handleRun} className="mt-4 flex flex-wrap items-end gap-4 text-xs">
          <label className="flex flex-col gap-1 font-semibold text-slate-700">
            Seeds
            <input type="number" min="2" max="50" value={form.n_seeds} onChange={set('n_seeds')} disabled={running}
              className="w-20 px-2.5 py-1.5 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </label>
          <label className="flex flex-col gap-1 font-semibold text-slate-700">
            Tasks per run
            <input type="number" min="10" max="2000" step="10" value={form.num_tasks} onChange={set('num_tasks')} disabled={running}
              className="w-24 px-2.5 py-1.5 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </label>
          <label className="flex flex-col gap-1 font-semibold text-slate-700">
            SLA slack
            <input type="number" min="1" max="10" step="0.1" value={form.sla_slack} onChange={set('sla_slack')} disabled={running}
              className="w-20 px-2.5 py-1.5 border border-slate-200 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </label>
          <label className="flex items-center gap-2 font-semibold text-slate-700 pb-1.5 cursor-pointer">
            <input type="checkbox" checked={form.sleep_enabled} onChange={set('sleep_enabled')} disabled={running}
              className="accent-sky-600 w-4 h-4" />
            <Moon className="w-3.5 h-3.5 text-indigo-500" />
            Allow idle servers to sleep
          </label>
          <button type="submit" disabled={running} id="run-comparison-btn"
            className="ml-auto px-4 py-2 rounded-xl font-bold uppercase tracking-wider text-white bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-60 flex items-center gap-2 cursor-pointer">
            {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            {running ? 'Running all schedulers…' : 'Run comparison'}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-800 font-mono">{error}</div>
      )}

      {loading ? (
        <p className="text-xs font-mono text-slate-500">Loading latest comparison…</p>
      ) : !comparison ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-600">
          No comparison yet. Choose the settings above and press <strong>Run comparison</strong>.
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-slate-500">
            <span>{comparison.comparison_id}</span>
            <span>seeds {comparison.seeds[0]}–{comparison.seeds[comparison.seeds.length - 1]}</span>
            <span>{comparison.params.num_tasks} tasks/run</span>
            <span>sleep {comparison.params.sleep_enabled ? 'on' : 'off'}</span>
            <span>SLA slack {comparison.params.sla_slack}</span>
            <span className="flex items-center gap-3 ml-auto">
              {comparison.policies.map((p) => (
                <span key={p} className="flex items-center gap-1.5 text-slate-700">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ background: POLICY_META[p]?.color }} />
                  {POLICY_META[p]?.label ?? p}
                </span>
              ))}
            </span>
          </div>

          {Object.keys(comparison.skipped || {}).length > 0 && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 flex items-start gap-2">
              <Info className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                {Object.entries(comparison.skipped).map(([p, reason]) => (
                  <div key={p}><strong>{POLICY_META[p]?.label ?? p} skipped:</strong> {reason}</div>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {METRICS.map((m) => (
              <MetricChart key={m.key} metric={m} policies={comparison.policies} summary={comparison.summary} />
            ))}
          </div>

          <SummaryTable comparison={comparison} />
        </>
      )}
    </div>
  );
}
