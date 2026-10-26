import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import ComparePage from './pages/ComparePage';

export default function App() {
  const [isBackendConnected, setIsBackendConnected] = useState(false);

  useEffect(() => {
    // Health probe to verify backend connectivity
    fetch('http://localhost:8000/api/health')
      .then((res) => {
        if (res.ok) setIsBackendConnected(true);
      })
      .catch(() => {
        setIsBackendConnected(false);
      });
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-slate-50 flex flex-col text-slate-800">
        <Navbar isBackendConnected={isBackendConnected} />

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <footer className="border-t border-slate-200/80 bg-white/60 py-6 text-center text-xs text-slate-600 font-mono">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>Data Center Digital Twin • Full-Stack React + Vite + FastAPI + SQLite</span>
            <div className="flex items-center gap-4">
              <span className="text-slate-600">16 Virtual Sockets Active</span>
            </div>
          </div>
        </footer>

      </div>
    </Router>
  );
}
