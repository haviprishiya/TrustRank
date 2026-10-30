import React, { useState } from 'react';
import { Package, ExternalLink, Heart, Check } from 'lucide-react';
import { saveProduct } from '../services/api';
import ProductOffersSection from './ProductOffersSection';

export default function ProductCard({ product, onSelect, onOpenPriceAlert }) {
  const candidates = React.useMemo(() => {
    const list = [];
    if (product.image_url) list.push(product.image_url);
    if (Array.isArray(product.image_candidates)) {
      product.image_candidates.forEach((u) => {
        if (u && typeof u === 'string' && !list.includes(u)) list.push(u);
      });
    }
    return list;
  }, [product.image_url, product.image_candidates]);

  const [imgIdx, setImgIdx] = useState(0);
  const [isWishlisted, setIsWishlisted] = useState(false);

  const handleWishlistToggle = async (e) => {
    e.stopPropagation();
    try {
      const token = localStorage.getItem('trustrank_auth_token');
      await saveProduct(token, product);
      setIsWishlisted(true);
      setTimeout(() => setIsWishlisted(false), 2500);
    } catch (err) {
      console.warn('Could not save to wishlist:', err);
    }
  };

  React.useEffect(() => {
    setImgIdx(0);
  }, [product.id, product.image_url, product.image_candidates]);

  const hasImage = candidates.length > 0 && imgIdx < candidates.length;
  const price = Number(product.current_price ?? product.price);
  const hasPrice = Number.isFinite(price) && price > 0;
  const currency = product.currency || 'INR';
  const money = (value) => new Intl.NumberFormat(undefined, {
    style: 'currency', currency, maximumFractionDigits: 2
  }).format(value);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition flex flex-col justify-between space-y-3">
      {/* Image */}
      <div className="w-full h-44 bg-slate-50 rounded-xl p-2 flex items-center justify-center overflow-hidden relative">
        {hasImage ? (
          <img
            src={candidates[imgIdx]}
            alt={product.title}
            referrerPolicy="no-referrer"
            loading="lazy"
            className="max-h-full max-w-full object-contain hover:scale-105 transition"
            onError={() => setImgIdx((prev) => prev + 1)}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-indigo-50/40 text-slate-400 p-3 text-center rounded-lg border border-slate-100/80">
            <div className="w-12 h-12 rounded-xl bg-white shadow-sm border border-slate-200/80 flex items-center justify-center mb-2">
              <Package className="w-6 h-6 text-indigo-500 stroke-1.5" />
            </div>
            <span className="text-[11px] font-bold text-slate-700 truncate max-w-[130px]">{product.brand || "Product"}</span>
            <span className="text-[10px] text-slate-400 mt-0.5">{product.marketplace || "Amazon / Flipkart"}</span>
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
          {hasPrice ? (
            <>
              <span className="text-lg font-black text-slate-900">
                {money(price)}
              </span>
              {product.original_price && product.original_price > price && (
                <span className="text-xs text-slate-400 line-through">
                  {money(product.original_price)}
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
        {(product.availability || product.asin) && (
          <div className="text-[11px] text-slate-500 flex flex-wrap gap-x-2">
            {product.availability && <span>{product.availability}</span>}
            {product.asin && <span>ASIN: {product.asin}</span>}
          </div>
        )}
        {/* Offers Section */}
        <ProductOffersSection product={product} />
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[11px] text-slate-500 font-medium">{product.marketplace}</span>
        <div className="flex items-center gap-2">
          {product.product_url && (
            <a href={product.product_url} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-indigo-700" aria-label="View product on Amazon">
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (onOpenPriceAlert) onOpenPriceAlert(product);
            }}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:text-amber-600 hover:bg-amber-50/60 text-xs transition"
            title="Set Price Drop Alert"
          >
            <svg className="w-3.5 h-3.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          <button
            type="button"
            onClick={handleWishlistToggle}
            className={`p-1.5 rounded-lg border text-xs font-semibold transition flex items-center space-x-1 ${
              isWishlisted
                ? 'bg-rose-50 border-rose-200 text-rose-600'
                : 'border-slate-200 text-slate-500 hover:text-rose-600 hover:bg-rose-50/50'
            }`}
            title="Add to Smart Wishlist"
          >
            <Heart className={`w-3.5 h-3.5 ${isWishlisted ? 'fill-rose-500 text-rose-500' : ''}`} />
          </button>
          <button
            onClick={() => onSelect(product)}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-indigo-50 text-indigo-700 font-bold transition"
          >
            Details & Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
