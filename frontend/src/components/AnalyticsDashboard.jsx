import React from 'react';

export default function AnalyticsDashboard({ analytics }) {
  if (!analytics || analytics.total_products_analyzed === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 border border-slate-200 text-center text-slate-500">
        No analytical data available. Search for a product and generate recommendations to view live analytics.
      </div>
    );
  }

  const {
    total_products_analyzed,
    total_reviews_represented,
    average_rating,
    positive_review_percentage,
    neutral_review_percentage,
    negative_review_percentage,
    brand_analysis,
    marketplace_analysis,
    price_distribution,
    rating_distribution
  } = analytics;

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Products */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Products Analysed</span>
          <div className="text-3xl font-black text-slate-900">{total_products_analyzed}</div>
          <p className="text-[11px] text-slate-500 font-medium">Real live marketplace listings</p>
        </div>

        {/* Total Reviews */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Reviews Represented</span>
          <div className="text-3xl font-black text-indigo-600">{total_reviews_represented?.toLocaleString('en-IN')}</div>
          <p className="text-[11px] text-slate-500 font-medium">Verified buyer evaluations</p>
        </div>

        {/* Avg Rating */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Average Rating</span>
          <div className="text-3xl font-black text-emerald-600">⭐ {average_rating?.toFixed(1)} / 5.0</div>
          <p className="text-[11px] text-slate-500 font-medium">Across active search results</p>
        </div>

        {/* Sentiment Split */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Sentiment Split</span>
          <div className="flex items-center space-x-2 text-xs font-bold">
            <span className="text-emerald-600">{positive_review_percentage}% Pos</span>
            <span className="text-slate-300">•</span>
            <span className="text-amber-600">{neutral_review_percentage}% Neu</span>
            <span className="text-slate-300">•</span>
            <span className="text-red-500">{negative_review_percentage}% Neg</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full flex overflow-hidden">
            <div style={{ width: `${positive_review_percentage}%` }} className="bg-emerald-500 h-full"></div>
            <div style={{ width: `${neutral_review_percentage}%` }} className="bg-amber-400 h-full"></div>
            <div style={{ width: `${negative_review_percentage}%` }} className="bg-red-400 h-full"></div>
          </div>
        </div>
      </div>

      {/* Brand Analysis Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 space-y-4">
        <div>
          <h3 className="text-base font-black text-slate-900 flex items-center space-x-2">
            <span>Brand Intelligence & Market Breakdown</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Aggregated pricing, rating, and customer sentiment across manufacturers in this category.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-200 text-[11px] font-bold uppercase text-slate-400 bg-slate-50/50">
                <th className="p-3">Brand</th>
                <th className="p-3">Product Count</th>
                <th className="p-3">Avg Price (INR)</th>
                <th className="p-3">Avg Rating</th>
                <th className="p-3">Total Reviews</th>
                <th className="p-3">Positive Sentiment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-medium text-slate-800">
              {brand_analysis?.map((b) => (
                <tr key={b.brand} className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">{b.brand}</td>
                  <td className="p-3">{b.product_count} products</td>
                  <td className="p-3 font-bold">₹{b.average_price.toLocaleString('en-IN')}</td>
                  <td className="p-3">⭐ {b.average_rating.toFixed(1)}</td>
                  <td className="p-3">{b.total_reviews.toLocaleString('en-IN')}</td>
                  <td className="p-3">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-emerald-600 w-10">{b.positive_percentage}%</span>
                      <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div style={{ width: `${b.positive_percentage}%` }} className="bg-emerald-500 h-full"></div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Marketplace Analysis & Distributions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Marketplace Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Marketplace Share & Comparison</h4>
            <p className="text-xs text-slate-500">Live offer count and average prices by store</p>
          </div>

          <div className="space-y-3">
            {marketplace_analysis?.map((m) => (
              <div key={m.marketplace} className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900">{m.marketplace}</span>
                  <span className="text-slate-500 font-semibold">{m.product_count} Offers</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600">
                  <span>Avg Price: <strong className="text-slate-900">₹{m.average_price.toLocaleString('en-IN')}</strong></span>
                  <span>Avg Rating: <strong className="text-slate-900">⭐ {m.average_rating.toFixed(1)}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Rating Distribution */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-slate-900">Rating Distribution Bracket</h4>
            <p className="text-xs text-slate-500">Proportion of products by customer star range</p>
          </div>

          <div className="space-y-2.5">
            {rating_distribution?.map((rb) => (
              <div key={rb.rating_range} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-700">
                  <span>{rb.rating_range}</span>
                  <span>{rb.count} products ({rb.percentage}%)</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div style={{ width: `${rb.percentage}%` }} className="bg-indigo-600 h-full"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
