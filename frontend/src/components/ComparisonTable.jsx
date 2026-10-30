import React from 'react';
import { ImageOff } from 'lucide-react';

function offerFor(rec, marketplace) {
  if (!rec) return null;
  const mTarget = marketplace.toLowerCase();
  const product = rec.product || rec;

  const isTargetMarketplace = (val) => {
    if (!val || typeof val !== 'string') return false;
    const v = val.toLowerCase();
    if (mTarget === 'amazon') return v.includes('amazon');
    if (mTarget === 'flipkart') return v.includes('flipkart');
    if (mTarget === 'myntra') return v.includes('myntra');
    return v.includes(mTarget);
  };

  // 1. Check marketplace_comparison array
  const compList = Array.isArray(rec.marketplace_comparison)
    ? rec.marketplace_comparison
    : (Array.isArray(product.marketplace_comparison) ? product.marketplace_comparison : []);

  const comp = compList.find((offer) =>
    isTargetMarketplace(offer?.marketplace) || isTargetMarketplace(offer?.seller_name)
  );
  if (comp) return comp;

  // 2. Check product.offers list
  const offersList = Array.isArray(product.offers)
    ? product.offers
    : (Array.isArray(rec.offers) ? rec.offers : []);
  const offer = offersList.find((o) =>
    isTargetMarketplace(o?.marketplace) || isTargetMarketplace(o?.seller_name) || isTargetMarketplace(o?.provider)
  );
  if (offer) {
    return {
      marketplace: offer.marketplace || marketplace,
      current_price: offer.current_price,
      original_price: offer.original_price,
      rating: offer.rating,
      review_count: offer.review_count,
      availability: offer.in_stock === true ? 'In Stock' : (offer.in_stock === false ? 'Out of Stock' : (offer.availability || product.availability || 'In Stock')),
      product_url: offer.product_url,
    };
  }

  // 3. Fallback to product itself if it belongs to this marketplace
  const prodMarketplace = product.marketplace || product.seller || product.source || product.provider || '';
  if (isTargetMarketplace(prodMarketplace)) {
    return {
      marketplace: product.marketplace || marketplace,
      current_price: product.current_price,
      original_price: product.original_price,
      rating: product.rating,
      review_count: product.review_count,
      availability: product.availability || 'In Stock',
      product_url: product.product_url,
    };
  }

  return null;
}

function priceCell(rec, marketplace) {
  const offer = offerFor(rec, marketplace);
  if (!offer) return <span className="text-slate-400 italic">No {marketplace} listing</span>;
  if (!offer.current_price || offer.current_price <= 0) return <span className="text-amber-700">Price not provided</span>;
  return <div className="space-y-1"><span className="font-black text-slate-900">₹{offer.current_price.toLocaleString('en-IN')}</span>{offer.has_better_price && <span className="block w-max text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">Better price</span>}</div>;
}

function ratingCell(rec, marketplace) {
  const offer = offerFor(rec, marketplace);
  if (!offer) return <span className="text-slate-400 italic">No {marketplace} listing</span>;
  if (!offer.rating || offer.rating <= 0) return <span className="text-slate-400 italic">Rating not available</span>;
  return <div className="space-y-1"><span>⭐ {offer.rating.toFixed(1)} {offer.review_count !== null && offer.review_count !== undefined ? `(${offer.review_count.toLocaleString('en-IN')} reviews)` : '(reviews not listed)'}</span>{offer.has_higher_rating && <span className="block w-max text-[10px] font-bold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded">Higher rated</span>}</div>;
}

function availabilityCell(rec, marketplace) {
  const offer = offerFor(rec, marketplace);
  if (!offer) return <span className="text-slate-400 italic">No {marketplace} listing</span>;
  return offer.availability ? <span className="font-semibold text-slate-700">{offer.availability}</span> : <span className="text-slate-400 italic">Availability not provided</span>;
}

function ProductThumbnail({ product }) {
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

  const [imgIdx, setImgIdx] = React.useState(0);

  React.useEffect(() => {
    setImgIdx(0);
  }, [product?.id, product?.image_url, product?.image_candidates]);

  const hasImage = candidates.length > 0 && imgIdx < candidates.length;

  return (
    <div className="w-full h-24 bg-white rounded-lg border border-slate-200 p-1 flex items-center justify-center mb-2 overflow-hidden">
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
        <div className="flex flex-col items-center justify-center text-slate-400 space-y-1 p-1 text-center">
          <ImageOff className="w-5 h-5 text-slate-300 stroke-1" />
          <span className="text-[9px] text-slate-400 font-medium">No Image</span>
        </div>
      )}
    </div>
  );
}

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
                  <ProductThumbnail product={rec.product} />
                  <span className="text-xs font-bold text-indigo-700 block">{rec.product.brand || "Brand"}</span>
                  <div
                    onClick={() => onSelectProduct(rec.product, rec)}
                    className="text-xs font-bold text-slate-900 hover:text-indigo-600 cursor-pointer line-clamp-2 mt-0.5"
                  >
                    {rec.product.title}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {/* Marketplace-specific values are real fetched offers; no value is inferred when a marketplace is absent. */}
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Amazon Price (INR)</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3">{priceCell(rec, 'Amazon')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Flipkart Price (INR)</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3">{priceCell(rec, 'Flipkart')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Myntra Price (INR)</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3">{priceCell(rec, 'Myntra')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Amazon Rating & Reviews</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3 text-slate-700 font-medium">{ratingCell(rec, 'Amazon')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Flipkart Rating & Reviews</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3 text-slate-700 font-medium">{ratingCell(rec, 'Flipkart')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Myntra Rating & Reviews</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3 text-slate-700 font-medium">{ratingCell(rec, 'Myntra')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Amazon Availability</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3">{availabilityCell(rec, 'Amazon')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Flipkart Availability</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3">{availabilityCell(rec, 'Flipkart')}</td>)}
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-3 font-bold text-slate-600 bg-slate-50/60">Myntra Availability</td>
              {comparisonProducts.map((rec, idx) => <td key={idx} className="p-3">{availabilityCell(rec, 'Myntra')}</td>)}
            </tr>
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
