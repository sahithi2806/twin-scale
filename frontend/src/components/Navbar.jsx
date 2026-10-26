import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Cpu, Zap, Activity, BarChart3 } from 'lucide-react';

export default function Navbar({ onOpenEnergyModal, isBackendConnected }) {
  const location = useLocation();
  const isDashboard = location.pathname === '/dashboard';
  const isCompare = location.pathname === '/compare';

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-emerald-400 p-0.5 shadow-sm group-hover:shadow-md transition-all">
            <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
              <Cpu className="w-5 h-5 text-sky-600 transition-transform group-hover:scale-110" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 tracking-tight text-lg">TwinScale</span>
              <span className="text-[10px] uppercase font-mono font-semibold px-1.5 py-0.5 bg-sky-50 text-sky-700 border border-sky-200/70 rounded">
                DC-Twin v1.0
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">Data Center Virtual Infrastructure</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-2 sm:gap-4">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              !isDashboard && !isCompare
                ? 'text-sky-700 bg-sky-50/80 font-semibold' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/60'
            }`}
          >
            Overview
          </Link>

          <Link
            to="/dashboard"
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all ${
              isDashboard 
                ? 'text-white bg-sky-600 shadow-xs font-semibold' 
                : 'text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/70'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>CPU Dashboard</span>
          </Link>

          <Link
            to="/compare"
            id="nav-compare"
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-all ${
              isCompare
                ? 'text-white bg-sky-600 shadow-xs font-semibold'
                : 'text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/70'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Compare Results</span>
          </Link>

          {/* Backend Status indicator */}
          <div className="hidden md:flex items-center gap-2 pl-3 ml-2 border-l border-slate-200 text-xs">
            <span className={`w-2 h-2 rounded-full ${isBackendConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'}`} />
            <span className="text-slate-500 font-mono">
              {isBackendConnected ? 'FastAPI: Live' : 'Demo State'}
            </span>
          </div>

          {/* Quick Energy Action Button */}
          {onOpenEnergyModal && (
            <button
              onClick={onOpenEnergyModal}
              id="nav-energy-button"
              className="ml-2 flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100/80 text-emerald-700 border border-emerald-200/80 rounded-lg text-xs font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] shadow-xs cursor-pointer"
              title="Click to view digital twin energy optimization breakdown"
            >
              <Zap className="w-3.5 h-3.5 text-emerald-600 fill-emerald-500/20" />
              <span>Energy: +24.8%</span>
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
