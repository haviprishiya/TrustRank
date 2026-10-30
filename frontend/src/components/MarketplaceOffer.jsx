import React from 'react';

export default function MarketplaceOffer({ offer }) {
  const { marketplace, current_price, original_price, discount_percent, in_stock, product_url, rating, review_count, currency = 'INR' } = offer;
  const formatMoney = (value) => new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : undefined, {
    style: 'currency', currency, maximumFractionDigits: 2,
  }).format(value);

  const isAmazon = marketplace.toLowerCase().includes('amazon');
  const isFlipkart = marketplace.toLowerCase().includes('flipkart');
  const isCroma = marketplace.toLowerCase().includes('croma');
  const isMyntra = marketplace.toLowerCase().includes('myntra');

  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/90 hover:border-slate-300 transition">
      <div className="flex items-center space-x-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${
          isAmazon ? 'bg-amber-100 text-amber-900 border border-amber-200' :
          isFlipkart ? 'bg-blue-100 text-blue-900 border border-blue-200' :
          isCroma ? 'bg-teal-100 text-teal-900 border border-teal-200' :
          isMyntra ? 'bg-pink-100 text-pink-900 border border-pink-200' :
          'bg-slate-200 text-slate-800'
        }`}>
          {isAmazon ? 'AMZ' : isFlipkart ? 'FK' : isCroma ? 'CR' : isMyntra ? 'MYN' : 'SHOP'}
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-900">{marketplace}</span>
            {in_stock === true ? (
              <span className="text-[10px] text-emerald-700 bg-emerald-100/80 px-1.5 py-0.2 rounded font-semibold">In Stock</span>
            ) : in_stock === false ? (
              <span className="text-[10px] text-red-600 bg-red-50 px-1.5 py-0.2 rounded font-semibold">Out of Stock</span>
            ) : (
              <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded font-semibold">Availability unknown</span>
            )}
          </div>
          {rating && (
            <p className="text-[11px] text-slate-500">
              ⭐ {rating.toFixed(1)} ({review_count?.toLocaleString('en-IN') || 0} reviews)
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-3">
        <div className="text-right">
          <div className="text-sm font-bold text-slate-900">
            {current_price !== null && current_price !== undefined ? formatMoney(current_price) : 'Price not listed'}
          </div>
          {original_price && original_price > current_price && (
            <div className="text-[11px] text-slate-400 line-through">{formatMoney(original_price)}</div>
          )}
        </div>

        {product_url ? (
          <a
            href={product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-indigo-600 text-white text-xs font-semibold transition flex items-center space-x-1"
          >
            <span>Buy</span>
            <svg className="w-3 h-3 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 00-2-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        ) : (
          <span className="text-[11px] font-semibold text-slate-400">Direct link unavailable</span>
        )}
      </div>
    </div>
  );
}
