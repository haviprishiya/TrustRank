import React, { useState } from 'react';
import { ImageOff, ExternalLink } from 'lucide-react';

export default function ProductCard({ product, onSelect }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between space-y-3">
      {/* Image */}
      <div className="w-full h-44 bg-slate-50 rounded-xl p-2 flex items-center justify-center overflow-hidden relative">
        {product.image_url && !imgError ? (
          <img
            src={product.image_url}
            alt={product.title}
            className="max-h-full max-w-full object-contain hover:scale-105 transition"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-400 space-y-1.5 p-3 text-center">
            <ImageOff className="w-8 h-8 text-slate-300 stroke-1" />
            <span className="text-[11px] font-medium text-slate-400">Photo not provided by source</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="space-y-1.5 flex-1">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
            {product.brand || "Verified Brand"}
          </span>
          <span className="text-slate-500 font-medium">
            {product.rating && product.rating > 0 ? (
              `⭐ ${product.rating.toFixed(1)} (${product.review_count ? product.review_count.toLocaleString() : '—'})`
            ) : (
              <span className="text-slate-400 italic">No ratings</span>
            )}
          </span>
        </div>

        <h4 className="font-bold text-sm text-slate-900 line-clamp-2 hover:text-indigo-600 cursor-pointer" onClick={() => onSelect(product)}>
          {product.title}
        </h4>

        <div className="flex items-baseline space-x-2 pt-1">
          {product.current_price && product.current_price > 0 ? (
            <>
              <span className="text-lg font-black text-slate-900">
                ₹{product.current_price.toLocaleString('en-IN')}
              </span>
              {product.original_price && product.original_price > product.current_price && (
                <span className="text-xs text-slate-400 line-through">
                  ₹{product.original_price.toLocaleString('en-IN')}
                </span>
              )}
            </>
          ) : (
            <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-1 rounded">
              Price unavailable from source feed
            </span>
          )}
        </div>

        {product.seller && (
          <div className="text-[11px] text-slate-500 truncate">
            Seller: <span className="font-medium text-slate-700">{product.seller}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[11px] text-slate-500 font-medium">{product.marketplace}</span>
        <button
          onClick={() => onSelect(product)}
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-indigo-50 text-indigo-700 font-bold transition"
        >
          Details & Analysis
        </button>
      </div>
    </div>
  );
}
