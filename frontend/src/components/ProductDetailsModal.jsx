import React, { useState } from 'react';
import { Package, ImageOff, ShieldCheck, CheckCircle, AlertTriangle, Bookmark, Check, Bell } from 'lucide-react';
import { saveProduct } from '../services/api';
import MarketplaceOffer from './MarketplaceOffer';
import ReviewAnalysis from './ReviewAnalysis';
import ProductOffersSection from './ProductOffersSection';

export default function ProductDetailsModal({ product, onClose, onOpenPriceAlert }) {
  if (!product) return null;
  const rec = product._recommendation;
  const [isSaved, setIsSaved] = React.useState(false);

  const handleSaveProduct = async () => {
    try {
      const token = localStorage.getItem('trustrank_auth_token');
      await saveProduct(token, product);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    } catch (e) {
      console.warn('Could not save product:', e);
    }
  };

  const candidates = React.useMemo(() => {
    const list = [];
    if (product?.image_url) list.push(product.image_url);
    if (Array.isArray(product?.image_candidates)) {
      product.image_candidates.forEach((u) => {
        if (u && typeof u === 'string' && !list.includes(u)) list.push(u);
      });
    }
    return list;
  }, [product?.image_url, product?.image_candidates]);

  const [imgIdx, setImgIdx] = useState(0);

  React.useEffect(() => {
    setImgIdx(0);
  }, [product?.id, product?.image_url, product?.image_candidates]);

  const hasImage = candidates.length > 0 && imgIdx < candidates.length;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 space-y-6">
        {/* Header Close */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div>
            <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-md">
              {product.brand} • {product.category}
            </span>
            <h3 className="text-xl font-bold text-slate-900 mt-2 leading-snug">
              {product.title}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 rounded-full bg-slate-100 hover:bg-slate-200 transition"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Product Overview */}
        <div className="flex flex-col sm:flex-row gap-6">
          <div className="w-full sm:w-56 h-56 bg-slate-50 rounded-2xl p-4 flex items-center justify-center border border-slate-100 shrink-0 overflow-hidden relative">
            {hasImage ? (
              <img
                src={candidates[imgIdx]}
                alt={product.title}
                referrerPolicy="no-referrer"
                loading="lazy"
                className="max-h-full max-w-full object-contain"
                onError={() => setImgIdx((prev) => prev + 1)}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-400 space-y-1.5 p-3 text-center">
                <ImageOff className="w-10 h-10 text-slate-300 stroke-1" />
                <span className="text-xs font-medium text-slate-400">Photo not provided by source</span>
              </div>
            )}
          </div>

          <div className="flex-1 space-y-3">
            <div className="flex items-baseline space-x-3">
              {product.current_price && product.current_price > 0 ? (
                <>
                  <span className="text-3xl font-black text-slate-900">
                    ₹{product.current_price.toLocaleString('en-IN')}
                  </span>
                  {product.original_price && product.original_price > product.current_price && (
                    <>
                      <span className="text-base text-slate-400 line-through">
                        ₹{product.original_price.toLocaleString('en-IN')}
                      </span>
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">
                        {product.discount_percent}% OFF
                      </span>
                    </>
                  )}
                </>
              ) : (
                <span className="text-sm font-semibold text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200">
                  Retail price not listed in feed (visit merchant to check live price)
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-600">
              {product.rating && product.rating > 0 ? (
                <>
                  <span>⭐ {product.rating.toFixed(1)} Rating</span>
                  <span>•</span>
                  <span>{product.review_count ? product.review_count.toLocaleString('en-IN') : '—'} Reviews</span>
                  <span>•</span>
                </>
              ) : (
                <>
                  <span className="text-slate-400 italic">No customer ratings</span>
                  <span>•</span>
                </>
              )}
              <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">{product.availability}</span>
              {product.seller && (
                <>
                  <span>•</span>
                  <span className="text-slate-500">Seller: {product.seller}</span>
                </>
              )}
            </div>

            {/* Product Offers & Discounts */}
            <ProductOffersSection product={product} defaultExpanded={true} />

            {/* Features */}
            {product.features && product.features.length > 0 && (
              <div className="space-y-1 text-xs text-slate-600 pt-1">
                <span className="font-bold text-slate-900 block">Key Highlights:</span>
                <ul className="list-disc pl-4 space-y-0.5">
                  {product.features.map((f, idx) => (
                    <li key={idx}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Recommendation Intelligence & TrustRank Analysis Report */}
        {rec && (
          <div className="bg-gradient-to-br from-indigo-50/70 to-slate-50 rounded-2xl p-5 border border-indigo-100/80 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-indigo-100 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                <h4 className="text-sm font-black text-slate-900">TrustRank Recommendation Analysis</h4>
                {rec.category_badges?.map((badge, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider bg-indigo-600 text-white"
                  >
                    {badge}
                  </span>
                ))}
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">Match Score</span>
                  <span className="text-base font-black text-emerald-600">{rec.requirement_match_percentage}%</span>
                </div>
                <div className="h-6 w-px bg-slate-200"></div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 uppercase font-bold block">TrustRank</span>
                  <span className="text-base font-black text-indigo-600">{rec.trustrank_score}/100</span>
                </div>
              </div>
            </div>

            {/* Why Recommended & Limitations Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {rec.positive_reasons?.length > 0 && (
                <div className="bg-emerald-50/70 p-3.5 rounded-xl border border-emerald-100 space-y-1.5">
                  <span className="font-bold text-emerald-900 block flex items-center space-x-1">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <span>Why We Recommend It</span>
                  </span>
                  <ul className="space-y-1 text-emerald-950 font-medium">
                    {rec.positive_reasons.map((r, i) => (
                      <li key={i} className="flex items-start space-x-1.5">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {rec.negative_reasons?.length > 0 && (
                <div className="bg-amber-50/70 p-3.5 rounded-xl border border-amber-100 space-y-1.5">
                  <span className="font-bold text-amber-900 block flex items-center space-x-1">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Trade-offs & Considerations</span>
                  </span>
                  <ul className="space-y-1 text-amber-950 font-medium">
                    {rec.negative_reasons.map((r, i) => (
                      <li key={i} className="flex items-start space-x-1.5">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Factor Scores Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center pt-1">
              <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/80">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Spec Match</span>
                <span className="text-sm font-black text-slate-800">{rec.requirement_match_score || 0} / 30</span>
              </div>
              <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/80">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Price & Value</span>
                <span className="text-sm font-black text-slate-800">{rec.price_value_score || 0} / 25</span>
              </div>
              <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/80">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Buyer Rating</span>
                <span className="text-sm font-black text-slate-800">{rec.rating_score || 0} / 20</span>
              </div>
              <div className="bg-white/80 p-2.5 rounded-xl border border-slate-200/80">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Reliability</span>
                <span className="text-sm font-black text-slate-800">{rec.source_reliability_score || 0} / 10</span>
              </div>
            </div>
          </div>
        )}

        {/* Specifications Table */}
        {product.specifications && Object.keys(product.specifications).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-slate-900">Technical Specifications</h4>
            <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80">
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 text-xs">
                {Object.entries(product.specifications).map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-slate-200/50 pb-1">
                    <dt className="text-slate-500 font-medium">{k}</dt>
                    <dd className="text-slate-900 font-bold text-right">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        )}

        {/* Marketplace Offers */}
        {product.offers && product.offers.filter(o => {
          const m = (o.marketplace || '').toLowerCase();
          return m.includes('amazon') || m.includes('flipkart') || m.includes('myntra');
        }).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-slate-900">Authorized Marketplace Offers</h4>
            <div className="space-y-2">
              {product.offers
                .filter(o => {
                  const m = (o.marketplace || '').toLowerCase();
                  return m.includes('amazon') || m.includes('flipkart') || m.includes('myntra');
                })
                .map((off, idx) => (
                  <MarketplaceOffer key={idx} offer={off} />
                ))}
            </div>
          </div>
        )}

        {/* Review Analysis */}
        {product.review_analysis && (
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-slate-900">Customer Sentiment & Reviews</h4>
            <ReviewAnalysis reviewAnalysis={product.review_analysis} />
          </div>
        )}

        {/* Modal Actions */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-100">
          {product.product_url ? (
            <a
              href={product.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition flex items-center space-x-1.5 shadow-sm shadow-indigo-600/20"
            >
              <span>View Product · {product.marketplace}</span>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          ) : <div />}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => {
                if (onOpenPriceAlert) onOpenPriceAlert(product);
              }}
              className="px-4 py-2.5 rounded-xl border border-amber-200 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-bold transition flex items-center space-x-1.5"
              title="Set Price Drop Alert"
            >
              <Bell className="w-3.5 h-3.5 text-amber-600" />
              <span>Price Alert</span>
            </button>
            <button
              type="button"
              onClick={handleSaveProduct}
              className={`px-4 py-2.5 rounded-xl border text-xs font-bold transition flex items-center space-x-1.5 ${
                isSaved
                  ? 'bg-rose-50 border-rose-200 text-rose-600'
                  : 'border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {isSaved ? <Check className="w-3.5 h-3.5 text-rose-600" /> : <Bookmark className="w-3.5 h-3.5 text-slate-500" />}
              <span>{isSaved ? 'Saved to Profile' : 'Save Product'}</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
            >
              Close Details
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
