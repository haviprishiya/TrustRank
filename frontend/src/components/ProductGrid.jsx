import React, { useState, useMemo } from 'react';
import RecommendationCard from './RecommendationCard';

export default function ProductGrid({ recommendations, onSelectProduct, onOpenPriceAlert }) {
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [selectedMarketplace, setSelectedMarketplace] = useState('all');
  const [sortBy, setSortBy] = useState('trustrank'); // trustrank, price_asc, price_desc, rating, reviews
  const [minPriceFilter, setMinPriceFilter] = useState('');
  const [maxPriceFilter, setMaxPriceFilter] = useState('');
  const [onlyBestValue, setOnlyBestValue] = useState(false);

  // Extract unique brands and marketplaces
  const brands = useMemo(() => {
    const set = new Set(recommendations.map((r) => r.product.brand).filter(Boolean));
    return Array.from(set);
  }, [recommendations]);

  const marketplaces = useMemo(() => {
    const set = new Set();
    recommendations.forEach((r) => {
      if (r.product.marketplace) set.add(r.product.marketplace);
      r.product.offers?.forEach((o) => set.add(o.marketplace));
    });
    return Array.from(set);
  }, [recommendations]);

  // Filter and sort
  const filteredRecommendations = useMemo(() => {
    const minVal = minPriceFilter !== '' ? Number(minPriceFilter) : 0;
    const maxVal = maxPriceFilter !== '' ? Number(maxPriceFilter) : 0;

    return recommendations
      .filter((r) => {
        if (selectedBrand !== 'all' && r.product.brand.toLowerCase() !== selectedBrand.toLowerCase()) {
          return false;
        }
        if (selectedMarketplace !== 'all') {
          const hasMkt = r.product.marketplace === selectedMarketplace ||
            r.product.offers?.some((o) => o.marketplace === selectedMarketplace);
          if (!hasMkt) return false;
        }
        if (minVal > 0 && r.product.current_price && r.product.current_price < minVal) {
          return false;
        }
        if (maxVal > 0 && r.product.current_price && r.product.current_price > maxVal) {
          return false;
        }
        if (onlyBestValue && !r.category_badges?.includes('Best Value')) {
          return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'trustrank') return b.trustrank_score - a.trustrank_score;
        const priceA = typeof a.product.current_price === 'number' ? a.product.current_price : Infinity;
        const priceB = typeof b.product.current_price === 'number' ? b.product.current_price : Infinity;
        if (sortBy === 'price_asc') return priceA - priceB;
        if (sortBy === 'price_desc') return (priceB === Infinity ? -1 : priceB) - (priceA === Infinity ? -1 : priceA);
        const ratingA = typeof a.product.rating === 'number' ? a.product.rating : 0;
        const ratingB = typeof b.product.rating === 'number' ? b.product.rating : 0;
        if (sortBy === 'rating') return ratingB - ratingA;
        const revA = typeof a.product.review_count === 'number' ? a.product.review_count : 0;
        const revB = typeof b.product.review_count === 'number' ? b.product.review_count : 0;
        if (sortBy === 'reviews') return revB - revA;
        return 0;
      });
  }, [recommendations, selectedBrand, selectedMarketplace, sortBy, minPriceFilter, maxPriceFilter, onlyBestValue]);

  const hasActiveFilters = selectedBrand !== 'all' || selectedMarketplace !== 'all' || minPriceFilter !== '' || maxPriceFilter !== '';

  return (
    <div className="space-y-6">
      {/* Filter and Sorting Controls */}
      <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Brand Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-semibold text-slate-500">Brand:</span>
            <select
              value={selectedBrand}
              onChange={(e) => setSelectedBrand(e.target.value)}
              className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 text-slate-800"
            >
              <option value="all">All Brands ({brands.length})</option>
              {brands.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          {/* Marketplace Filter */}
          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-semibold text-slate-500">Store:</span>
            <select
              value={selectedMarketplace}
              onChange={(e) => setSelectedMarketplace(e.target.value)}
              className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 text-slate-800"
            >
              <option value="all">All Marketplaces</option>
              {marketplaces.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Best Value Finder Filter */}
          <button
            type="button"
            onClick={() => setOnlyBestValue(!onlyBestValue)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
              onlyBestValue
                ? 'bg-emerald-600 text-white shadow-xs ring-2 ring-emerald-500/20'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200'
            }`}
            title="Filter to show only verified Best Value products"
          >
            <span>💰</span>
            <span>Best Value Only</span>
            {onlyBestValue && <span className="w-1.5 h-1.5 rounded-full bg-white"></span>}
          </button>

          {/* Price Range Filter (Min & Max) */}
          <div className="flex items-center space-x-1.5 bg-slate-50/80 px-2.5 py-1 rounded-xl border border-slate-200">
            <span className="text-xs font-semibold text-slate-500">Price (₹):</span>
            <div className="flex items-center space-x-1">
              <input
                type="number"
                placeholder="Min"
                value={minPriceFilter}
                onChange={(e) => setMinPriceFilter(e.target.value)}
                className="w-20 px-2 py-1 text-xs font-semibold bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 text-slate-800 shadow-xs"
              />
              <span className="text-slate-400 text-xs font-bold">—</span>
              <input
                type="number"
                placeholder="Max"
                value={maxPriceFilter}
                onChange={(e) => setMaxPriceFilter(e.target.value)}
                className="w-20 px-2 py-1 text-xs font-semibold bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 text-slate-800 shadow-xs"
              />
            </div>
          </div>
        </div>

        {/* Sorting Dropdown */}
        <div className="flex items-center space-x-2 self-start lg:self-auto">
          <span className="text-xs font-semibold text-slate-500">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500 text-indigo-700"
          >
            <option value="trustrank">TrustRank Match (Recommended)</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="rating">Highest Rating</option>
            <option value="reviews">Most Reviewed</option>
          </select>
        </div>
      </div>

      {/* Results Count & Active Filter Indicator */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 font-medium px-1">
        <div className="flex items-center space-x-2">
          <span>Showing <strong>{filteredRecommendations.length}</strong> of {recommendations.length} live recommendations</span>
          {(minPriceFilter || maxPriceFilter) && (
            <span className="px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold border border-indigo-100 text-[11px]">
              ₹{minPriceFilter || '0'} — ₹{maxPriceFilter || '∞'}
            </span>
          )}
        </div>
        {hasActiveFilters && (
          <button
            onClick={() => {
              setSelectedBrand('all');
              setSelectedMarketplace('all');
              setMinPriceFilter('');
              setMaxPriceFilter('');
            }}
            className="text-indigo-600 hover:text-indigo-800 font-bold transition flex items-center space-x-1"
          >
            <span>Reset Filters</span>
            <span>✕</span>
          </button>
        )}
      </div>

      {/* Cards List */}
      <div className="space-y-4">
        {filteredRecommendations.map((rec, idx) => (
          <RecommendationCard
            key={rec.product.id || idx}
            recommendation={rec}
            onSelectProduct={(p) => onSelectProduct(p, rec)}
            isFeatured={idx === 0 && sortBy === 'trustrank'}
            onOpenPriceAlert={onOpenPriceAlert}
          />
        ))}
      </div>
    </div>
  );
}
