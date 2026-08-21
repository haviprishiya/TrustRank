import React, { useState } from 'react';
import { ImageOff, ExternalLink, ShieldCheck, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import MarketplaceOffer from './MarketplaceOffer';

export default function RecommendationCard({ recommendation, onSelectProduct, isFeatured = false }) {
  const [imgError, setImgError] = useState(false);

  const {
    product,
    trustrank_score,
    requirement_match_percentage,
    budget_fit_score,
    value_for_money,
    requirement_match_score,
    price_value_score,
    rating_score,
    review_confidence_score,
    availability_score,
    source_reliability_score,
    scoring_breakdown_explanation,
    positive_reasons = [],
    negative_reasons = [],
    neutral_observations = [],
    best_for_you_explanation,
    category_badges = []
  } = recommendation;

  return (
    <div className={`bg-white rounded-2xl border transition-all duration-200 overflow-hidden shadow-sm hover:shadow-md ${
      isFeatured ? 'border-indigo-500 ring-2 ring-indigo-500/10' : 'border-slate-200'
    }`}>
      {/* Badges Bar */}
      <div className="bg-slate-900 px-5 py-3 flex flex-wrap items-center justify-between gap-2 text-white">
        <div className="flex flex-wrap items-center gap-1.5">
          {category_badges && category_badges.map((badge, idx) => (
            <span
              key={idx}
              className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider flex items-center space-x-1 ${
                badge === 'Best for You' ? 'bg-gradient-to-r from-amber-400 to-amber-500 text-slate-950 shadow-sm' :
                badge === 'Best Value' ? 'bg-emerald-500 text-white' :
                badge === 'Best Reviewed' ? 'bg-blue-500 text-white' :
                'bg-indigo-500 text-white'
              }`}
            >
              <span>{badge === 'Best for You' ? '🏆' : badge === 'Best Value' ? '💰' : badge === 'Best Reviewed' ? '⭐' : '🔄'}</span>
              <span>{badge}</span>
            </span>
          ))}
          <span className="text-xs text-slate-400 font-medium">
            {product.brand || "Verified Brand"} • {product.category}
          </span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Match</span>
            <span className="text-sm font-black text-emerald-400">{requirement_match_percentage}%</span>
          </div>
          <div className="h-6 w-px bg-slate-700"></div>
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">TrustRank</span>
            <span className="text-sm font-black text-indigo-300">{trustrank_score}/100</span>
          </div>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="p-5 sm:p-6 space-y-5">
        <div className="flex flex-col sm:flex-row gap-5 items-start">
          {/* Image */}
          <div className="w-full sm:w-44 h-44 bg-slate-50 rounded-xl border border-slate-100 p-2 flex items-center justify-center shrink-0 overflow-hidden relative">
            {product.image_url && !imgError ? (
              <img
                src={product.image_url}
                alt={product.title}
                className="max-h-full max-w-full object-contain hover:scale-105 transition duration-200"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="text-slate-400 flex flex-col items-center justify-center p-3 text-center">
                <ImageOff className="w-8 h-8 text-slate-300 stroke-1" />
                <span className="text-[10px] mt-1 font-medium text-slate-400">Photo not provided by source</span>
              </div>
            )}
          </div>

          {/* Title and Key Specs */}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center space-x-2 text-xs">
              <span className="font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                {product.brand || "Brand"}
              </span>
              <span className="text-slate-500 font-medium">
                {product.rating && product.rating > 0 ? (
                  `⭐ ${product.rating.toFixed(1)} (${product.review_count ? product.review_count.toLocaleString('en-IN') : '—'} reviews)`
                ) : (
                  <span className="text-slate-400 italic">Rating not available</span>
                )}
              </span>
            </div>

            <h3
              onClick={() => onSelectProduct(product)}
              className="text-base sm:text-lg font-bold text-slate-900 hover:text-indigo-600 cursor-pointer transition leading-snug"
            >
              {product.title}
            </h3>

            {/* Price & Value Badge */}
            <div className="flex flex-wrap items-baseline gap-3 pt-1">
              {product.current_price && product.current_price > 0 ? (
                <>
                  <span className="text-2xl font-black text-slate-900 tracking-tight">
                    ₹{product.current_price.toLocaleString('en-IN')}
                  </span>
                  {product.original_price && product.original_price > product.current_price && (
                    <>
                      <span className="text-sm text-slate-400 line-through">
                        ₹{product.original_price.toLocaleString('en-IN')}
                      </span>
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                        {product.discount_percent}% OFF
                      </span>
                    </>
                  )}
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-slate-100 text-slate-700 border border-slate-200">
                    Value: {value_for_money}
                  </span>
                </>
              ) : (
                <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded border border-amber-200">
                  Retail price not listed in feed (check merchant link)
                </span>
              )}
            </div>

            {product.seller && (
              <div className="text-xs text-slate-500">
                Seller / Source: <span className="font-semibold text-slate-700">{product.seller}</span> ({product.marketplace})
              </div>
            )}

            {/* Specifications Chips */}
            {product.specifications && Object.keys(product.specifications).length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-2">
                {Object.entries(product.specifications).slice(0, 4).map(([k, v]) => (
                  <span key={k} className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                    <span className="text-slate-500 font-normal">{k}:</span> {v}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Transparent Scoring Breakdown */}
        <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200 text-xs">
          <span className="font-bold text-slate-700 block text-[11px] uppercase tracking-wider mb-2">
            Transparent TrustRank Scoring Breakdown
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="bg-white p-2 rounded-lg border border-slate-100 text-center">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Requirement (35%)</span>
              <span className="text-sm font-bold text-indigo-600">{requirement_match_score || requirement_match_percentage}%</span>
            </div>
            <div className="bg-white p-2 rounded-lg border border-slate-100 text-center">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Price/Value (25%)</span>
              <span className="text-sm font-bold text-emerald-600">{price_value_score || 75}/100</span>
            </div>
            <div className="bg-white p-2 rounded-lg border border-slate-100 text-center">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Rating (20%)</span>
              <span className="text-sm font-bold text-blue-600">{rating_score !== null && rating_score !== undefined ? `${rating_score}/100` : 'Not available'}</span>
            </div>
            <div className="bg-white p-2 rounded-lg border border-slate-100 text-center">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Availability (20%)</span>
              <span className="text-sm font-bold text-purple-600">{availability_score !== null && availability_score !== undefined ? `${availability_score}/100` : 'Not available'}</span>
            </div>
          </div>
        </div>

        {/* Positive, Negative, Neutral Columns */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
          {/* Positive */}
          <div className="bg-emerald-50/50 p-3.5 rounded-xl border border-emerald-100/80 space-y-1.5">
            <span className="font-bold text-emerald-900 block flex items-center space-x-1">
              <span>✓</span>
              <span>Why We Recommend It</span>
            </span>
            <ul className="space-y-1 text-emerald-950 font-medium">
              {positive_reasons.map((r, i) => (
                <li key={i} className="flex items-start space-x-1.5">
                  <span className="text-emerald-500 font-bold">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Negative / Limitations */}
          <div className="bg-amber-50/50 p-3.5 rounded-xl border border-amber-100/80 space-y-1.5">
            <span className="font-bold text-amber-900 block flex items-center space-x-1">
              <span>⚠</span>
              <span>Limitations & Trade-offs</span>
            </span>
            <ul className="space-y-1 text-amber-950 font-medium">
              {negative_reasons.length > 0 ? (
                negative_reasons.map((r, i) => (
                  <li key={i} className="flex items-start space-x-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))
              ) : (
                <li className="text-slate-500 italic">No major disqualifying limitations.</li>
              )}
            </ul>
          </div>

          {/* Neutral Observations */}
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/80 space-y-1.5">
            <span className="font-bold text-slate-800 block flex items-center space-x-1">
              <span>ℹ</span>
              <span>Neutral Observations</span>
            </span>
            <ul className="space-y-1 text-slate-700 font-medium">
              {neutral_observations.map((r, i) => (
                <li key={i} className="flex items-start space-x-1.5">
                  <span className="text-slate-400 font-bold">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Marketplace Offers Comparison */}
        {product.offers && product.offers.length > 0 && (
          <div className="space-y-2 border-t border-slate-100 pt-4">
            <span className="text-xs font-bold text-slate-600 block uppercase tracking-wider">
              Available at Authorized Marketplaces
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {product.offers.map((off, idx) => (
                <MarketplaceOffer key={idx} offer={off} />
              ))}
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={() => onSelectProduct(product)}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
          >
            <span>View Full Specs & Review Sentiment</span>
            <svg className="w-4 h-4 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition flex items-center space-x-1.5 shadow-sm shadow-indigo-600/20"
          >
            <span>Visit {product.marketplace}</span>
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  );
}
