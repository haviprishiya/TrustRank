import React, { useState, useMemo } from 'react';
import RecommendationCard from './RecommendationCard';

export default function ProductGrid({ recommendations, onSelectProduct }) {
  const [selectedBrand, setSelectedBrand] = useState('all');
  const [selectedMarketplace, setSelectedMarketplace] = useState('all');
  const [sortBy, setSortBy] = useState('trustrank'); // trustrank, price_asc, price_desc, rating, reviews
  const [maxPriceFilter, setMaxPriceFilter] = useState(0);

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

  const maxPriceInData = useMemo(() => {
    if (!recommendations.length) return 100000;
    return Math.max(...recommendations.map((r) => r.product.current_price));
  }, [recommendations]);

  // Filter and sort
  const filteredRecommendations = useMemo(() => {
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
        if (maxPriceFilter > 0 && r.product.current_price > maxPriceFilter) {
          return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'trustrank') return b.trustrank_score - a.trustrank_score;
        if (sortBy === 'price_asc') return a.product.current_price - b.product.current_price;
        if (sortBy === 'price_desc') return b.product.current_price - a.product.current_price;
        if (sortBy === 'rating') return b.product.rating - a.product.rating;
        if (sortBy === 'reviews') return b.product.review_count - a.product.review_count;
        return 0;
      });
  }, [recommendations, selectedBrand, selectedMarketplace, sortBy, maxPriceFilter]);

  return (
    <div className="space-y-6">
      {/* Filter and Sorting Controls */}
      <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
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
        </div>

        {/* Sorting Dropdown */}
        <div className="flex items-center space-x-2">
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

      {/* Results Count */}
      <div className="flex items-center justify-between text-xs text-slate-500 font-medium px-1">
        <span>Showing {filteredRecommendations.length} of {recommendations.length} live recommendations</span>
        {selectedBrand !== 'all' || selectedMarketplace !== 'all' || maxPriceFilter > 0 ? (
          <button
            onClick={() => { setSelectedBrand('all'); setSelectedMarketplace('all'); setMaxPriceFilter(0); }}
            className="text-indigo-600 hover:text-indigo-800 font-bold"
          >
            Reset Filters
          </button>
        ) : null}
      </div>

      {/* Cards List */}
      <div className="space-y-4">
        {filteredRecommendations.map((rec, idx) => (
          <RecommendationCard
            key={rec.product.id || idx}
            recommendation={rec}
            onSelectProduct={onSelectProduct}
            isFeatured={idx === 0 && sortBy === 'trustrank'}
          />
        ))}
      </div>
    </div>
  );
}
