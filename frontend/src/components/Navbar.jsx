import React from 'react';

export default function Navbar({ onReset, onViewProviders, activeView, setActiveView, providersCount, liveItemCount }) {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={onReset}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-200 bg-clip-text text-transparent">TrustRank</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/30">Live Data</span>
            </div>
            <p className="text-[11px] text-slate-400 font-normal">Real-Time Shopping Intelligence & Recommendations</p>
          </div>
        </div>

        {/* Navigation & Controls */}
        <div className="flex items-center space-x-2 sm:space-x-4">
          {liveItemCount > 0 && (
            <div className="hidden md:flex items-center space-x-1 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse mr-1"></span>
              <span>{liveItemCount} Live Products Analysed</span>
            </div>
          )}

          {activeView !== 'home' && (
            <div className="flex items-center bg-slate-800 rounded-lg p-1 border border-slate-700 text-xs">
              <button
                onClick={() => setActiveView('recommendations')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${activeView === 'recommendations' ? 'bg-indigo-600 text-white shadow' : 'text-slate-300 hover:text-white'}`}
              >
                Recommendations
              </button>
              <button
                onClick={() => setActiveView('comparison')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${activeView === 'comparison' ? 'bg-indigo-600 text-white shadow' : 'text-slate-300 hover:text-white'}`}
              >
                Top 5 Comparison
              </button>
              <button
                onClick={() => setActiveView('analytics')}
                className={`px-3 py-1.5 rounded-md font-medium transition ${activeView === 'analytics' ? 'bg-indigo-600 text-white shadow' : 'text-slate-300 hover:text-white'}`}
              >
                Analytics Dashboard
              </button>
            </div>
          )}

          <button
            onClick={onViewProviders}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
            title="Inspect Marketplace Providers Status"
          >
            <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <span className="hidden sm:inline">Providers</span>
          </button>
        </div>
      </div>
    </header>
  );
}
