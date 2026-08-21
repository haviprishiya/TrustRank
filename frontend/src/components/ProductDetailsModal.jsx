import React from 'react';
import MarketplaceOffer from './MarketplaceOffer';
import ReviewAnalysis from './ReviewAnalysis';

export default function ProductDetailsModal({ product, onClose }) {
  if (!product) return null;

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
          <div className="w-full sm:w-56 h-56 bg-slate-50 rounded-2xl p-4 flex items-center justify-center border border-slate-100 shrink-0">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.title}
                className="max-h-full max-w-full object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : (
              <div className="text-slate-400 text-xs font-medium">Photo not provided by source</div>
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
        {product.offers && product.offers.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-slate-900">Authorized Marketplace Offers</h4>
            <div className="space-y-2">
              {product.offers.map((off, idx) => (
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

        {/* Modal Close Button */}
        <div className="pt-2 flex justify-end">
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
  );
}
