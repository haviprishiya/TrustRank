import React from 'react';

export default function ReviewAnalysis({ reviewAnalysis }) {
  if (!reviewAnalysis) return null;

  const {
    source_note,
    total_reviews_analyzed,
    written_reviews_count = 0,
    written_reviews = [],
    positive_percentage,
    neutral_percentage,
    negative_percentage,
    most_praised_features,
    common_complaints,
    recurring_themes,
    rating_distribution,
    summary,
    combined_rating,
    marketplace_breakdown = []
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
            <span>Cross-Marketplace Review Evidence</span>
          </h4>
          <p className="text-[11px] text-slate-400 mt-0.5">{source_note}</p>
        </div>
        <div className="text-right">
          <div className="text-xs font-semibold text-slate-700">
            {total_reviews_analyzed ? `${total_reviews_analyzed.toLocaleString('en-IN')} total ratings` : 'Ratings unavailable'}
          </div>
          <div className="text-[11px] text-indigo-600 font-medium">
            {written_reviews_count > 0 ? `${written_reviews_count} written customer reviews analyzed` : 'Written reviews unavailable'}
          </div>
        </div>
      </div>

      {combined_rating !== null && combined_rating !== undefined && (
        <div className="rounded-xl bg-indigo-50 border border-indigo-100 p-3 flex items-center justify-between">
          <span className="text-xs font-bold text-indigo-950">Combined marketplace rating</span>
          <span className="text-sm font-black text-indigo-700">⭐ {combined_rating.toFixed(2)}/5</span>
        </div>
      )}

      {marketplace_breakdown.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {marketplace_breakdown.map((marketplace) => (
            <div key={marketplace.marketplace} className="rounded-xl bg-slate-50 border border-slate-200 p-3">
              <div className="text-xs font-bold text-slate-900">{marketplace.marketplace}</div>
              <div className="text-xs text-slate-600 mt-1">
                {marketplace.rating !== null && marketplace.rating !== undefined ? `⭐ ${marketplace.rating.toFixed(1)}` : 'Rating unavailable'}
                {marketplace.review_count !== null && marketplace.review_count !== undefined ? ` · ${marketplace.review_count.toLocaleString('en-IN')} reviews` : ' · Review count unavailable'}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {summary && (
        <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200/80 italic">
          "{summary}"
        </p>
      )}

      {!reviewAnalysis.has_detailed_reviews && (
        <p className="text-xs text-slate-500 bg-amber-50 p-3 rounded-xl border border-amber-100">
          Limited review evidence for this requirement. The displayed rating and review count come from the marketplace feeds.
        </p>
      )}

      {reviewAnalysis.has_detailed_reviews && (
      <>
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

      {/* Authentic Customer Reviews */}
      {written_reviews && written_reviews.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
              <span>Authentic Customer Reviews</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-semibold">
                {written_reviews.length} analyzed
              </span>
            </span>
            <span className="text-[10px] text-slate-400">Verified Marketplace Feed</span>
          </div>
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {written_reviews.slice(0, 4).map((rev, idx) => (
              <div key={rev.id || idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/70 text-xs space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center space-x-1.5">
                    {rev.rating !== null && rev.rating !== undefined && (
                      <span className="font-bold text-amber-600">⭐ {rev.rating}</span>
                    )}
                    <span className="font-semibold text-slate-800">{rev.reviewer_name || 'Reviewer unavailable'}</span>
                    {rev.verified_purchase && (
                      <span className="text-[9px] px-1.5 py-0.5 bg-emerald-100 text-emerald-800 font-bold rounded">Verified Purchase</span>
                    )}
                  </div>
                  {rev.review_date && (
                    <span className="text-[10px] text-slate-400">{rev.review_date}</span>
                  )}
                </div>
                {rev.title && (
                  <div className="font-bold text-slate-800 text-[11px]">{rev.title}</div>
                )}
                <p className="text-slate-600 text-[11px] line-clamp-3">
                  {rev.review_text}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      </>
      )}
    </div>
  );
}
