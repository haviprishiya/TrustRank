import React from 'react';

export default function ComparisonTable({ comparisonProducts, onSelectProduct }) {
  if (!comparisonProducts || comparisonProducts.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center text-slate-500">
        No comparison data available for current search.
      </div>
    );
  }

  // All distinct spec keys across top 5
  const allSpecKeys = Array.from(
    new Set(
      comparisonProducts.flatMap((rec) => Object.keys(rec.product.specifications || {}))
    )
  );

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-6 p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-lg font-black text-slate-900 flex items-center space-x-2">
            <span>Top 5 Live Product Comparison</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-100">
              Side-by-Side Analysis
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Directly comparing the top live offers on price, TrustRank score, key specifications, and review sentiment.
          </p>
        </div>
      </div>

      {/* Responsive Horizontal Scroll Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-[700px]">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="p-3 text-xs font-bold uppercase text-slate-400 w-40 bg-slate-50">Feature / Metric</th>
              {comparisonProducts.map((rec, idx) => (
                <th key={idx} className="p-3 text-xs font-bold text-slate-900 bg-slate-50/50 w-56 align-top">
                  {rec.category_badges && rec.category_badges.length > 0 && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase block mb-1.5 w-max ${
                      rec.category_badges.includes('Best for You') ? 'bg-amber-400 text-slate-950 font-black' :
                      rec.category_badges.includes('Best Value') ? 'bg-emerald-500 text-white' :
                      rec.category_badges.includes('Best Reviewed') ? 'bg-blue-500 text-white' :
                      'bg-indigo-500 text-white'
                    }`}>
                      {rec.category_badges[0]}
                    </span>
                  )}
                  {/* Thumbnail */}
                  <div className="w-full h-24 bg-white rounded-lg border border-slate-200 p-1 flex items-center justify-center mb-2 overflow-hidden">
                    {rec.product.image_url ? (
                      <img
                        src={rec.product.image_url}
                        alt={rec.product.title}
                        className="max-h-full max-w-full object-contain"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    ) : (
                      <span className="text-[10px] text-slate-400">No Photo</span>
                    )}
                  </div>
                  <span className="text-xs font-bold text-indigo-700 block">{rec.product.brand || "Brand"}</span>
                  <div
                    onClick={() => onSelectProduct(rec.product)}
                    className="text-xs font-bold text-slate-900 hover:text-indigo-600 cursor-pointer line-clamp-2 mt-0.5"
                  >
                    {rec.product.title}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {/* Price Row */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Live Price (INR)</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 font-black text-slate-900 text-sm">
                  {rec.product.current_price && rec.product.current_price > 0 ? (
                    `₹${rec.product.current_price.toLocaleString('en-IN')}`
                  ) : (
                    <span className="text-amber-700 text-xs font-semibold bg-amber-50 px-2 py-0.5 rounded">Not listed</span>
                  )}
                </td>
              ))}
            </tr>

            {/* Original Price */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Original MRP</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 text-slate-500 font-medium">
                  {rec.product.original_price && rec.product.original_price > (rec.product.current_price || 0) ? (
                    `₹${rec.product.original_price.toLocaleString('en-IN')}`
                  ) : '—'}
                </td>
              ))}
            </tr>

            {/* TrustRank Score */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">TrustRank Score</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 font-black text-indigo-600 text-sm">
                  {rec.trustrank_score} / 100
                </td>
              ))}
            </tr>

            {/* Requirement Match */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Requirement Match</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 font-black text-emerald-600">
                  {rec.requirement_match_percentage}%
                </td>
              ))}
            </tr>

            {/* Rating & Reviews */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Customer Rating</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 text-slate-700 font-medium">
                  {rec.product.rating && rec.product.rating > 0 ? (
                    `⭐ ${rec.product.rating.toFixed(1)} (${rec.product.review_count ? rec.product.review_count.toLocaleString('en-IN') : '—'})`
                  ) : (
                    <span className="text-slate-400 italic">No ratings</span>
                  )}
                </td>
              ))}
            </tr>

            {/* Availability */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Availability</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 text-slate-800 font-semibold">
                  <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px]">
                    {rec.product.availability}
                  </span>
                </td>
              ))}
            </tr>

            {/* Marketplace & Seller */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Marketplace & Seller</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 text-slate-700 font-medium">
                  <div className="font-bold text-slate-900">{rec.product.marketplace}</div>
                  <div className="text-[11px] text-slate-500">{rec.product.seller || "Authorized Seller"}</div>
                </td>
              ))}
            </tr>

            {/* Value for Money */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Value For Money</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 font-bold text-slate-800">
                  {rec.value_for_money}
                </td>
              ))}
            </tr>

            {/* Dynamic Specs Rows */}
            {allSpecKeys.map((specKey) => (
              <tr key={specKey} className="hover:bg-slate-50/50">
                <td className="p-3 font-bold text-slate-600 bg-slate-50/60">{specKey}</td>
                {comparisonProducts.map((rec, idx) => (
                  <td key={idx} className="p-3 text-slate-700 font-medium">
                    {rec.product.specifications?.[specKey] || '—'}
                  </td>
                ))}
              </tr>
            ))}

            {/* Top Positive Aspect */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-emerald-800 bg-emerald-50/40">Top Advantage</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 text-emerald-950 font-medium">
                  {rec.positive_reasons?.[0] || 'Meets requirement specifications'}
                </td>
              ))}
            </tr>

            {/* Top Trade-off */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-amber-800 bg-amber-50/40">Main Trade-off</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3 text-amber-950 font-medium">
                  {rec.negative_reasons?.[0] || 'Standard category specs'}
                </td>
              ))}
            </tr>

            {/* Direct Links */}
            <tr>
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Purchase Link</td>
              {comparisonProducts.map((rec, idx) => (
                <td key={idx} className="p-3">
                  <a
                    href={rec.product.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-indigo-600 text-white font-bold text-xs transition"
                  >
                    <span>View on {rec.product.marketplace}</span>
                    <svg className="w-3 h-3 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
