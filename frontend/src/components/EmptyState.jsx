import React from 'react';

export default function EmptyState({ title = "No products found", message, onReset }) {
  return (
    <div className="bg-white rounded-3xl p-10 border border-slate-200 shadow-sm max-w-lg mx-auto text-center space-y-4 my-8">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>

      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-900">{title}</h3>
        <p className="text-xs text-slate-500">
          {message || "Live product data is currently unavailable for this search query or provider. Try adjusting your search or requirements."}
        </p>
      </div>

      {onReset && (
        <button
          onClick={onReset}
          className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition"
        >
          New Search
        </button>
      )}
    </div>
  );
}
