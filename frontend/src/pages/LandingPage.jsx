import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Cpu, 
  ArrowRight, 
  Zap, 
  ShieldCheck, 
  Activity, 
  Layers, 
  Thermometer, 
  Database, 
  CheckCircle, 
  Sparkles,
  Server
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-[calc(100vh-4rem)] tech-grid-pattern relative pb-16">
      
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 sm:pt-20 pb-16 text-center">
        
        {/* Soft Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-50 border border-sky-200/80 text-sky-700 text-xs font-semibold mb-6 shadow-2xs">
          <Sparkles className="w-3.5 h-3.5 text-sky-500" />
          <span>Next-Generation Virtual Infrastructure Telemetry</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-[1.15]">
          Data Center <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600">Digital Twin</span> Engine
        </h1>

        {/* Hero Subtitle */}
        <p className="mt-6 text-base sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          A high-fidelity virtual replica of your server infrastructure. Monitor 16 virtual compute nodes in real time, analyze thermal hotspots, and automate idle power consolidation.
        </p>

        {/* Prominent CTA Button */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/dashboard"
            id="hero-go-to-dashboard-btn"
            className="w-full sm:w-auto px-8 py-4 bg-sky-600 hover:bg-sky-500 active:bg-sky-700 text-white font-bold rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-3 text-base group cursor-pointer"
          >
            <Cpu className="w-5 h-5 text-sky-100 group-hover:rotate-12 transition-transform" />
            <span>Go to CPU Dashboard</span>
            <ArrowRight className="w-5 h-5 text-white group-hover:translate-x-1 transition-transform" />
          </Link>

          <a
            href="#architecture"
            className="w-full sm:w-auto px-6 py-4 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-2xl border border-slate-200 shadow-xs transition-colors text-sm flex items-center justify-center gap-2"
          >
            <span>Explore Architecture</span>
          </a>
        </div>

        {/* Tech Proofpoints Strip */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs font-mono text-slate-500">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <span>FastAPI Backend Layer</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <span>SQLite Virtual Store</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <span>4×4 Interactive CPU Matrix</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-500" />
            <span>Opacity Focus Isolation</span>
          </div>
        </div>
      </section>

      {/* Interactive Digital Twin Preview Card */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 mb-20">
        <div className="bg-white/90 backdrop-blur-md rounded-3xl border border-slate-200/90 shadow-xl p-6 sm:p-8 overflow-hidden relative">
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-sky-600 font-bold">
                Live Twin Visualizer
              </span>
              <h2 className="text-xl font-bold text-slate-900 mt-0.5">
                Rack Alpha-1 to Delta-2 Topology
              </h2>
            </div>
            
            <Link
              to="/dashboard"
              className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1 group bg-sky-50 px-3 py-1.5 rounded-lg border border-sky-100"
            >
              <span>Launch Full 4×4 Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          {/* Mini 4x4 preview simulation */}
          <div className="mt-6 grid grid-cols-4 sm:grid-cols-8 gap-2.5">
            {[
              { id: 'SRV-01', util: 85, active: true },
              { id: 'SRV-02', util: 92, active: true },
              { id: 'SRV-03', util: 61, active: true },
              { id: 'SRV-04', util: 0, active: false },
              { id: 'SRV-05', util: 78, active: true },
              { id: 'SRV-06', util: 43, active: true },
              { id: 'SRV-07', util: 89, active: true },
              { id: 'SRV-08', util: 0, active: false },
              { id: 'SRV-09', util: 71, active: true },
              { id: 'SRV-10', util: 83, active: true },
              { id: 'SRV-11', util: 0, active: false },
              { id: 'SRV-12', util: 95, active: true },
              { id: 'SRV-13', util: 69, active: true },
              { id: 'SRV-14', util: 0, active: false },
              { id: 'SRV-15', util: 80, active: true },
              { id: 'SRV-16', util: 54, active: true },
            ].map((node) => (
              <div
                key={node.id}
                className={`p-2 rounded-xl border flex flex-col items-center justify-center text-center transition-all ${
                  node.active
                    ? 'bg-slate-50 border-slate-200/80 hover:border-sky-300'
                    : 'bg-slate-100/60 border-dashed border-slate-300'
                }`}
              >
                <span className="text-[10px] font-mono font-bold text-slate-700">{node.id}</span>
                <span className={`text-[11px] font-mono font-bold mt-1 ${
                  !node.active ? 'text-slate-400' :
                  node.util > 80 ? 'text-amber-600' : 'text-sky-600'
                }`}>
                  {node.active ? `${node.util}%` : 'IDLE'}
                </span>
                <div className={`w-1.5 h-1.5 rounded-full mt-1.5 ${
                  node.active ? 'bg-emerald-500' : 'bg-slate-300'
                }`} />
              </div>
            ))}
          </div>

          <p className="text-xs text-center text-slate-600 mt-5">
            Clicking any socket isolates that server at 100% while dimming others to 20% opacity.
          </p>
        </div>
      </section>

      {/* Digital Twin Core Pillars */}
      <section id="architecture" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How the Digital Twin Functions
          </h2>
          <p className="text-sm text-slate-600 mt-2 max-w-xl mx-auto">
            A bi-directional software layer combining real-time hardware telemetry with predictive energy intelligence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Card 1 */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mb-4">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">
                2D CPU-Socket Visualization
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Experience an intuitive 4×4 physical matrix representing compute blades across four high-density racks. Click any CPU to isolate its load and dim background nodes to 20%.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs font-mono text-sky-700">
              <span>Interactive Opacity Focus</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">
                Dynamic Energy Savings
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                By grouping workloads onto optimal nodes and transitioning idle servers to low-power sleep states, the digital twin cuts facility cooling overhead and lowers PUE toward 1.15.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs font-mono text-emerald-700">
              <span>+4,860 kWh / mo Conserved</span>
            </div>
          </div>

          {/* Card 3 */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center mb-4">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">
                FastAPI + SQLite Architecture
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Clean full-stack synchronization. The FastAPI backend serves the 16 virtual servers via REST endpoints, backed by persistent SQLite storage with toggle and re-seed APIs.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-1.5 text-xs font-mono text-teal-700">
              <span>GET /api/servers (16 Nodes)</span>
            </div>
          </div>

        </div>

        {/* Bottom Banner with CTA */}
        <div className="mt-14 bg-gradient-to-r from-sky-600 to-emerald-600 rounded-3xl p-8 text-white flex flex-col sm:flex-row items-center justify-between gap-6 shadow-lg">
          <div>
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight">
              Ready to Inspect the 16 Virtual Servers?
            </h3>
            <p className="text-sky-100 text-xs sm:text-sm mt-1 max-w-lg">
              Launch the live CPU Utilization Dashboard to explore real-time telemetry, toggle idle states, and view the energy breakdown.
            </p>
          </div>

          <Link
            to="/dashboard"
            className="px-6 py-3.5 bg-white text-slate-900 font-bold text-sm rounded-xl hover:bg-slate-100 transition-colors shrink-0 shadow-md flex items-center gap-2 group cursor-pointer"
          >
            <span>Launch Dashboard</span>
            <ArrowRight className="w-4 h-4 text-sky-600 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

    </div>
  );
}
