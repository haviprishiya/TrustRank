import React from 'react';

export default function ProviderStatusBanner({ providers, isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full p-6 space-y-5 shadow-2xl border border-slate-200 max-h-[85vh] overflow-y-auto">
        <div className="flex items-start justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <svg className="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <span>Marketplace Providers Status</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Live inspection of authorized marketplace connectors and environment configuration.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-full bg-slate-100 transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-3">
          {providers?.map((p) => {
            const isActive = p.status === 'active' || p.status === 'idle' || p.status === 'ready' || (p.configured && p.status === 'initialized');
            const isOptional = Boolean(p.is_optional || p.status?.includes('optional'));
            const isCredentialsRequired = p.status === 'credentials_required' && !isOptional;
            const status = p.status || 'unknown';

            let badgeClass = 'bg-slate-200 text-slate-700';
            let badgeText = status.replace('_', ' ');

            if (isActive) {
              badgeClass = 'bg-emerald-100 text-emerald-800';
              badgeText = 'Connected · ' + (status === 'initialized' ? 'Ready' : status.replace('_', ' '));
            } else if (isOptional) {
              badgeClass = 'bg-slate-100 text-slate-600 border border-slate-200';
              badgeText = 'Optional · Unavailable';
            } else if (isCredentialsRequired) {
              badgeClass = 'bg-amber-100 text-amber-900 border border-amber-200';
              badgeText = 'Credentials Required';
            }

            return (
              <div key={p.provider_id} className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-sm text-slate-900">{p.name}</span>
                    <span className="text-xs text-slate-500">({p.marketplace})</span>
                  </div>
                  <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${badgeClass}`}>
                    {badgeText}
                  </span>
                </div>

                <p className="text-xs text-slate-600 font-medium">
                  {p.message}
                </p>

                {p.env_keys_required && p.env_keys_required.length > 0 && (
                  <div className="text-[11px] text-slate-500 bg-white p-2 rounded-lg border border-slate-200 font-mono">
                    Environment variables: {p.env_keys_required.join(', ')}
                  </div>
                )}

                {p.latency_ms !== null && p.latency_ms !== undefined && (
                  <div className="text-[10px] text-slate-400">
                    Response time: {p.latency_ms.toFixed(0)} ms • Items fetched: {p.items_fetched}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
