import React, { useState, useEffect } from 'react';

const STAGES = [
  "Parsing search intent & identifying product type...",
  "Querying Amazon India & Flipkart authorized feeds in INR...",
  "Normalizing specifications & pricing across providers...",
  "Deduplicating multi-marketplace product offers...",
  "Running TrustRank scoring against your requirements...",
  "Aggregating verified buyer review sentiment & top 5 comparison..."
];

export default function LoadingState({ message = "Conducting live shopping research..." }) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 700);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white rounded-3xl p-10 border border-slate-200 shadow-xl max-w-lg mx-auto text-center space-y-6 my-12">
      {/* Animated Pulse Icon */}
      <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-indigo-500/20 animate-ping"></div>
        <div className="w-16 h-16 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-600/30">
          <svg className="w-8 h-8 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-bold text-slate-900">{message}</h3>
        <p className="text-xs text-indigo-600 font-semibold min-h-[20px] transition-all">
          {STAGES[stageIndex]}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-indigo-600 h-full transition-all duration-500 rounded-full"
          style={{ width: `${((stageIndex + 1) / STAGES.length) * 100}%` }}
        ></div>
      </div>
    </div>
  );
}
