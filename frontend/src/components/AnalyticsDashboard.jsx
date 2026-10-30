import React from 'react';
import { Package, ExternalLink, ShieldCheck, Trophy, Sparkles, Star } from 'lucide-react';

export default function AnalyticsDashboard({
  analytics,
  recommendations = [],
  topComparison = [],
  bestForYou = null,
  bestValue = null,
  bestReviewed = null,
  bestAlternative = null,
  onSelectProduct = () => {}
}) {
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

      {/* Top Recommendation Highlights */}
      {recommendations.length > 0 && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <div>
              <h3 className="text-base font-black text-slate-900 flex items-center space-x-2">
                <Trophy className="w-5 h-5 text-amber-500" />
                <span>Top Recommendation Highlights</span>
              </h3>
              <p className="text-xs text-slate-500">
                Key winners identified by TrustRank algorithms across Amazon India and Flipkart
              </p>
            </div>
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
              {recommendations.length} Scored Recommendations
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Best for You', rec: bestForYou || recommendations[0], icon: '🏆', color: 'from-amber-500 to-amber-600' },
              { label: 'Best Value', rec: bestValue || recommendations[1], icon: '💰', color: 'from-emerald-500 to-emerald-600' },
              { label: 'Best Reviewed', rec: bestReviewed || recommendations[2], icon: '⭐', color: 'from-blue-500 to-blue-600' },
              { label: 'Top Alternative', rec: bestAlternative || recommendations[3], icon: '🔄', color: 'from-indigo-500 to-indigo-600' },
            ].filter(card => card.rec).map((card, idx) => {
              const r = card.rec;
              const p = r.product;
              return (
                <div key={idx} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex flex-col justify-between space-y-3 hover:border-indigo-400 transition group">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full text-white bg-gradient-to-r ${card.color}`}>
                        {card.icon} {card.label}
                      </span>
                      <span className="text-xs font-black text-indigo-700">
                        {r.trustrank_score}/100
                      </span>
                    </div>

                    <div className="w-full h-28 bg-slate-50 rounded-xl p-2 flex items-center justify-center overflow-hidden">
                      {p.image_url ? (
                        <img
                          src={p.image_url}
                          alt={p.title}
                          referrerPolicy="no-referrer"
                          loading="lazy"
                          className="max-h-full max-w-full object-contain group-hover:scale-105 transition"
                          onError={(e) => { e.target.style.display = 'none'; }}
                        />
                      ) : (
                        <Package className="w-8 h-8 text-slate-300 stroke-1" />
                      )}
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                        {p.brand}
                      </span>
                      <h4
                        onClick={() => onSelectProduct(p, r)}
                        className="text-xs font-bold text-slate-900 hover:text-indigo-600 cursor-pointer line-clamp-2 mt-1"
                      >
                        {p.title}
                      </h4>
                    </div>

                    <div className="flex items-baseline justify-between pt-1">
                      <span className="text-sm font-black text-slate-900">
                        {p.current_price ? `₹${p.current_price.toLocaleString('en-IN')}` : 'Check store'}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-500">
                        {p.marketplace}
                      </span>
                    </div>

                    {r.positive_reasons?.length > 0 && (
                      <p className="text-[11px] text-emerald-800 bg-emerald-50/80 p-2 rounded-lg line-clamp-2 font-medium">
                        ✓ {r.positive_reasons[0]}
                      </p>
                    )}
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => onSelectProduct(p, r)}
                      className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold transition flex-1 text-center"
                    >
                      Analysis Report
                    </button>
                    {p.product_url && (
                      <a
                        href={p.product_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition"
                        title={`View on ${p.marketplace}`}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendation Scoring Matrix Table */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <div>
              <h3 className="text-base font-black text-slate-900 flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                <span>Recommendation Intelligence & Scoring Matrix</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Full comparative analysis across candidate listings with transparent algorithmic scores
              </p>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Ranked by Multi-Factor TrustRank Score
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[750px]">
              <thead>
                <tr className="border-b border-slate-200 text-[11px] font-bold uppercase text-slate-400 bg-slate-50/50">
                  <th className="p-3 w-12 text-center">Rank</th>
                  <th className="p-3">Product Name & Brand</th>
                  <th className="p-3">Marketplace</th>
                  <th className="p-3">TrustRank</th>
                  <th className="p-3">Spec Match</th>
                  <th className="p-3">Live Price</th>
                  <th className="p-3">Verified Rating</th>
                  <th className="p-3">Key Advantage</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs font-medium text-slate-800">
                {recommendations.map((rec, idx) => {
                  const p = rec.product;
                  const score = rec.trustrank_score;
                  const match = rec.requirement_match_percentage;
                  const badge = rec.category_badges?.[0];
                  return (
                    <tr key={p.id || idx} className="hover:bg-slate-50/70 transition">
                      <td className="p-3 text-center">
                        <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-black text-[11px] ${
                          idx === 0 ? 'bg-amber-100 text-amber-800 font-extrabold' :
                          idx === 1 ? 'bg-slate-200 text-slate-700' :
                          idx === 2 ? 'bg-amber-50 text-amber-900' :
                          'text-slate-400 font-bold'
                        }`}>
                          #{idx + 1}
                        </span>
                      </td>
                      <td className="p-3 max-w-[240px]">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-10 h-10 bg-slate-50 rounded-lg border border-slate-100 p-1 shrink-0 flex items-center justify-center overflow-hidden">
                            {p.image_url ? (
                              <img
                                src={p.image_url}
                                alt={p.title}
                                referrerPolicy="no-referrer"
                                loading="lazy"
                                className="max-h-full max-w-full object-contain"
                                onError={(e) => { e.target.style.display = 'none'; }}
                              />
                            ) : (
                              <Package className="w-4 h-4 text-slate-300 stroke-1" />
                            )}
                          </div>
                          <div className="min-w-0">
                            <span className="text-[10px] font-bold text-indigo-700 block truncate">{p.brand}</span>
                            <div
                              onClick={() => onSelectProduct(p, rec)}
                              className="font-bold text-slate-900 hover:text-indigo-600 cursor-pointer truncate"
                              title={p.title}
                            >
                              {p.title}
                            </div>
                            {badge && (
                              <span className="inline-block mt-0.5 text-[9px] font-extrabold uppercase px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                                {badge}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="p-3 font-semibold text-slate-700 whitespace-nowrap">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          p.marketplace?.toLowerCase().includes('amazon')
                            ? 'bg-amber-50 text-amber-800 border border-amber-200/60'
                            : 'bg-blue-50 text-blue-800 border border-blue-200/60'
                        }`}>
                          {p.marketplace || 'Store'}
                        </span>
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <span className={`font-black text-xs ${
                            score >= 85 ? 'text-emerald-600' :
                            score >= 70 ? 'text-indigo-600' : 'text-slate-600'
                          }`}>
                            {score}/100
                          </span>
                          <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              style={{ width: `${Math.min(100, score)}%` }}
                              className={`h-full ${
                                score >= 85 ? 'bg-emerald-500' :
                                score >= 70 ? 'bg-indigo-600' : 'bg-slate-400'
                              }`}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="p-3 font-bold text-emerald-600 whitespace-nowrap">
                        {match}%
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        <div className="font-black text-slate-900">
                          {p.current_price ? `₹${p.current_price.toLocaleString('en-IN')}` : '—'}
                        </div>
                        {rec.value_for_money && (
                          <span className="text-[10px] text-slate-400 block font-semibold">
                            {rec.value_for_money} Value
                          </span>
                        )}
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        <span className="font-bold text-slate-800">
                          {p.rating ? `⭐ ${p.rating.toFixed(1)}` : '—'}
                        </span>
                        {p.review_count ? (
                          <span className="text-[10px] text-slate-400 block">
                            ({p.review_count.toLocaleString('en-IN')})
                          </span>
                        ) : null}
                      </td>
                      <td className="p-3 max-w-[200px]">
                        <span className="text-slate-600 truncate block text-[11px]" title={rec.positive_reasons?.[0] || 'Meets search criteria'}>
                          {rec.positive_reasons?.[0] || 'Meets search criteria'}
                        </span>
                      </td>
                      <td className="p-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => onSelectProduct(p, rec)}
                          className="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition"
                        >
                          View Report
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

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
                  <td className="p-3 font-bold">{b.average_price !== null && b.average_price !== undefined ? `₹${b.average_price.toLocaleString('en-IN')}` : '—'}</td>
                  <td className="p-3">{b.average_rating !== null && b.average_rating !== undefined ? `⭐ ${b.average_rating.toFixed(1)}` : '—'}</td>
                  <td className="p-3">{b.total_reviews?.toLocaleString('en-IN') || 0}</td>
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
                  <span>Avg Price: <strong className="text-slate-900">{m.average_price !== null && m.average_price !== undefined ? `₹${m.average_price.toLocaleString('en-IN')}` : '—'}</strong></span>
                  <span>Avg Rating: <strong className="text-slate-900">{m.average_rating !== null && m.average_rating !== undefined ? `⭐ ${m.average_rating.toFixed(1)}` : '—'}</strong></span>
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
