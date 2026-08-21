import React from 'react';

export default function ReviewAnalysis({ reviewAnalysis }) {
  if (!reviewAnalysis) return null;

  const {
    source_note,
    total_reviews_analyzed,
    positive_percentage,
    neutral_percentage,
    negative_percentage,
    most_praised_features,
    common_complaints,
    recurring_themes,
    rating_distribution,
    summary
  } = reviewAnalysis;

  return (
    <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h4 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
            <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span>Verified Customer Sentiment Analysis</span>
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">{source_note}</p>
        </div>
        <div className="text-xs text-slate-500 font-medium">
          {total_reviews_analyzed?.toLocaleString('en-IN')} ratings represented
        </div>
      </div>

      {/* Sentiment Progress Bars */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs font-semibold">
          <span className="text-emerald-700">Positive: {positive_percentage}%</span>
          <span className="text-amber-700">Neutral: {neutral_percentage}%</span>
          <span className="text-red-600">Negative: {negative_percentage}%</span>
        </div>
        <div className="w-full h-3 bg-slate-100 rounded-full flex overflow-hidden">
          <div style={{ width: `${positive_percentage}%` }} className="bg-emerald-500 h-full" title={`Positive ${positive_percentage}%`}></div>
          <div style={{ width: `${neutral_percentage}%` }} className="bg-amber-400 h-full" title={`Neutral ${neutral_percentage}%`}></div>
          <div style={{ width: `${negative_percentage}%` }} className="bg-red-400 h-full" title={`Negative ${negative_percentage}%`}></div>
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200/80 italic">
          "{summary}"
        </p>
      )}

      {/* Praised vs Complaints Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
        {most_praised_features && most_praised_features.length > 0 && (
          <div className="bg-emerald-50/60 p-3 rounded-xl border border-emerald-100 space-y-1.5">
            <div className="font-bold text-emerald-900 flex items-center space-x-1.5">
              <svg className="w-4 h-4 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
              <span>Most Praised Aspects</span>
            </div>
            <ul className="space-y-1 text-emerald-950 font-medium">
              {most_praised_features.map((item, idx) => (
                <li key={idx} className="flex items-start space-x-1">
                  <span className="text-emerald-500 font-bold">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {common_complaints && common_complaints.length > 0 && (
          <div className="bg-amber-50/60 p-3 rounded-xl border border-amber-100 space-y-1.5">
            <div className="font-bold text-amber-900 flex items-center space-x-1.5">
              <svg className="w-4 h-4 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>Common Caveats / Complaints</span>
            </div>
            <ul className="space-y-1 text-amber-950 font-medium">
              {common_complaints.map((item, idx) => (
                <li key={idx} className="flex items-start space-x-1">
                  <span className="text-amber-500 font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
