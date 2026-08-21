import React from 'react';

export default function ErrorState({ error, onRetry }) {
  return (
    <div className="bg-red-50/70 rounded-3xl p-8 border border-red-200 max-w-lg mx-auto text-center space-y-4 my-8">
      <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 mx-auto flex items-center justify-center">
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>

      <div className="space-y-1">
        <h3 className="text-base font-bold text-red-900">An Error Occurred</h3>
        <p className="text-xs text-red-700">
          {error?.message || "Failed to communicate with TrustRank live services."}
        </p>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="px-5 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition shadow-sm"
        >
          Retry
        </button>
      )}
    </div>
  );
}
