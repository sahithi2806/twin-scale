import React, { useState } from 'react';
import { Play, RefreshCw, Sliders, Dices, CheckCircle2, Clock, Layers, Moon } from 'lucide-react';

const SCHEDULERS = [
  { id: 'min-min', label: 'Min-Min', tag: 'Baseline',
    description: 'Greedy earliest-completion placement; spreads load across servers.' },
  { id: 'power-aware', label: 'Power-aware', tag: 'Heuristic',
    description: 'Best-fit consolidation onto awake servers; wakes the most efficient sleeper only when needed.' },
  { id: 'dqn', label: 'DQN', tag: 'RL',
    description: 'Trained Q-network; reward = -(energy + SLA penalty + overload penalty).' }
];

export default function SimulationControlPanel({
  onRunSimulation,
  isRunning,
  progress,
  latestSim,
  policyStatus
}) {
  const [numTasks, setNumTasks] = useState(100);
  const [seed, setSeed] = useState(42);
  const [policy, setPolicy] = useState('min-min');
  const [sleepEnabled, setSleepEnabled] = useState(true);
  const [slaSlack, setSlaSlack] = useState(1.5);

  const handleStart = (e) => {
    e.preventDefault();
    if (isRunning) return;
    onRunSimulation({
      num_tasks: numTasks,
      policy,
      seed,
      sleep_enabled: sleepEnabled,
      sla_slack: slaSlack
    });
  };

  const handleRandomizeSeed = () => {
    setSeed(Math.floor(Math.random() * 900) + 100);
  };

  const taskPresets = [50, 100, 200, 400];

  return (
    <div className="bg-white rounded-3xl border border-slate-200/90 p-5 sm:p-6 shadow-xs relative overflow-hidden">

      {/* Decorative subtle tech glow */}
      <div className="absolute top-0 right-0 w-36 h-36 bg-sky-100/50 rounded-full blur-2xl pointer-events-none -mr-8 -mt-8" />

      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 text-white flex items-center justify-center shadow-xs">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm tracking-tight flex items-center gap-2">
              <span>Simulation Engine & Schedulers</span>
            </h3>
            <p className="text-xs text-slate-500">Configure the synthetic workload and choose a scheduler</p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200/80">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Selected: {SCHEDULERS.find((o) => o.id === policy)?.label}</span>
        </div>
      </div>

      {/* Configuration Form */}
      <form onSubmit={handleStart} className="mt-4 space-y-4 relative z-10">

        {/* Scheduler Policy Selection - Segmented Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-2">
            Select Scheduling Policy (POST /api/simulations)
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5" role="radiogroup" aria-label="Scheduling policy">
            {SCHEDULERS.map((opt) => {
              const availability = policyStatus?.[opt.id];
              const unavailable = availability && !availability.available;
              const active = policy === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  id={`policy-${opt.id}`}
                  disabled={isRunning || unavailable}
                  onClick={() => setPolicy(opt.id)}
                  title={unavailable ? availability.reason : undefined}
                  className={`text-left p-3 rounded-2xl border-2 transition-all flex flex-col justify-between ${
                    unavailable
                      ? 'border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed'
                      : active
                        ? 'border-sky-500 bg-sky-50/60 shadow-xs cursor-pointer'
                        : 'border-slate-200 bg-slate-50 hover:bg-slate-100/60 cursor-pointer'
                  }`}
                >
                  <span className="flex items-center justify-between w-full">
                    <span className="font-bold text-xs text-slate-900 flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${active ? 'bg-sky-600' : 'bg-slate-400'}`} />
                      {opt.label}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 bg-slate-200/70 text-slate-700 rounded font-medium">
                      {opt.tag}
                    </span>
                  </span>
                  <span className="text-[11px] text-slate-500 mt-1 leading-snug">
                    {unavailable ? 'Train first: python train_dqn.py' : opt.description}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <label className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200/80 cursor-pointer">
            <span className="flex items-center gap-2 text-xs font-semibold text-slate-700">
              <Moon className="w-4 h-4 text-indigo-500" />
              Idle servers may sleep
            </span>
            <input type="checkbox" id="sleep-toggle" checked={sleepEnabled} disabled={isRunning}
              onChange={(e) => setSleepEnabled(e.target.checked)} className="accent-sky-600 w-4 h-4" />
          </label>
          <label className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
            <span className="flex items-center gap-2 text-xs font-semibold text-slate-700">
              <Clock className="w-4 h-4 text-amber-600" />
              SLA deadline slack (× ideal runtime)
            </span>
            <input type="number" id="sla-slack-input" min="1" max="10" step="0.1" value={slaSlack} disabled={isRunning}
              onChange={(e) => setSlaSlack(Number(e.target.value))}
              className="w-20 px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500" />
          </label>
        </div>

        {/* Task Count Slider & Presets */}
        <div>
          <div className="flex items-center justify-between text-xs mb-1.5">
            <label htmlFor="tasks-slider" className="font-semibold text-slate-700 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-sky-600" />
              <span>Synthetic Workload Tasks</span>
            </label>
            <span className="font-mono font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
              {numTasks} Tasks
            </span>
          </div>

          <input
            id="tasks-slider"
            type="range"
            min="20"
            max="500"
            step="10"
            value={numTasks}
            disabled={isRunning}
            onChange={(e) => setNumTasks(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-sky-600 disabled:opacity-50"
          />

          {/* Quick Preset Buttons */}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[11px] text-slate-600 font-mono">Presets:</span>
            {taskPresets.map((count) => (
              <button
                key={count}
                type="button"
                disabled={isRunning}
                onClick={() => setNumTasks(count)}
                className={`text-[11px] font-mono px-2.5 py-0.5 rounded-md border transition-all cursor-pointer ${
                  numTasks === count
                    ? 'bg-sky-600 text-white border-sky-600 font-semibold'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200'
                }`}
              >
                {count}
              </button>
            ))}
          </div>
        </div>

        {/* Random Seed */}
        <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
          <div className="flex items-center gap-2">
            <Dices className="w-4 h-4 text-indigo-500" />
            <label htmlFor="seed-input" className="text-xs font-semibold text-slate-700">
              Deterministic Seed (Fair Benchmark):
            </label>
          </div>
          <div className="flex items-center gap-2">
            <input
              id="seed-input"
              type="number"
              value={seed}
              disabled={isRunning}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-20 px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <button
              type="button"
              disabled={isRunning}
              onClick={handleRandomizeSeed}
              className="text-[11px] text-sky-600 hover:text-sky-800 underline font-mono cursor-pointer"
            >
              Randomize
            </button>
          </div>
        </div>

        {/* Prominent 'Start Simulation' Button */}
        <button
          type="submit"
          disabled={isRunning}
          id="start-simulation-btn"
          className={`w-full py-3 px-4 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2.5 transition-all shadow-md cursor-pointer ${
            isRunning
              ? 'bg-sky-400 text-white cursor-wait'
              : 'bg-gradient-to-r from-sky-600 to-teal-600 hover:from-sky-500 hover:to-teal-500 text-white hover:shadow-lg active:scale-[0.99]'
          }`}
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-white" />
              <span>Running {SCHEDULERS.find((o) => o.id === policy)?.label}…</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white text-white" />
              <span>Run Simulation ({SCHEDULERS.find((o) => o.id === policy)?.label})</span>
            </>
          )}
        </button>

        {isRunning && progress && (
          <div className="space-y-1" aria-live="polite">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-600">
              <span className="uppercase tracking-wide">{progress.status}</span>
              <span>{Math.round((progress.progress || 0) * 100)}%</span>
            </div>
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-sky-500 rounded-full transition-all duration-300"
                style={{ width: `${Math.round((progress.progress || 0) * 100)}%` }}
              />
            </div>
          </div>
        )}
      </form>

      {/* Latest Run Results Pill / Card */}
      {latestSim && (
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs font-mono gap-2 relative z-10 bg-slate-50/70 p-3 rounded-xl border border-slate-200/70">
          <div className="flex items-center gap-2 text-slate-700">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Last Run: <strong>{latestSim.run_id}</strong></span>
          </div>

          <div className="flex items-center gap-3 text-slate-600">
            <span>Makespan: <strong>{latestSim.makespan}s</strong></span>
            <span className="text-emerald-700 font-semibold">Energy: <strong>{latestSim.total_energy_kwh} kWh</strong></span>
            <span>SLA violations: <strong>{latestSim.sla_violations}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
}
