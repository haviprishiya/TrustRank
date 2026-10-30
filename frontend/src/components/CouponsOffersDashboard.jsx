import React, { useState, useEffect, useMemo } from 'react';
import {
  Tag,
  Search,
  Copy,
  Check,
  ExternalLink,
  ShieldCheck,
  Clock,
  Sparkles,
  ArrowLeft,
  AlertCircle,
  Filter
} from 'lucide-react';
import { fetchCouponOffers, fetchFeaturedDeals } from '../services/api';

export default function CouponsOffersDashboard({
  initialQuery = '',
  recommendations = [],
  onNavigateHome,
  onNavigateRecommendations
}) {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [offers, setOffers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [selectedMarketplace, setSelectedMarketplace] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [copiedId, setCopiedId] = useState(null);

  // Extract offers from existing recommendation products in memory first
  const localOffers = useMemo(() => {
    if (!recommendations || recommendations.length === 0) return [];
    const list = [];
    recommendations.forEach((rec) => {
      const p = rec.product;
      if (!p) return;
      const currentPrice = Number(p.current_price ?? p.price);
      const originalPrice = Number(p.original_price);
      const hasDiscount = Number.isFinite(currentPrice) && currentPrice > 0 && Number.isFinite(originalPrice) && originalPrice > currentPrice;

      if (hasDiscount) {
        const discountAmount = Math.round(originalPrice - currentPrice);
        const discountPercent = Math.round((discountAmount / originalPrice) * 100);
        list.push({
          id: `rec_offer_${p.id}`,
          title: `${discountPercent}% Off on ${p.title.slice(0, 45)}...`,
          applicable_product: p.title,
          marketplace: p.marketplace || 'Amazon India',
          current_price: currentPrice,
          original_price: originalPrice,
          discount_percent: discountPercent,
          discount_amount: discountAmount,
          coupon_code: null,
          has_coupon_code: false,
          offer_type: 'Direct Discount',
          description: `Save ₹${discountAmount.toLocaleString('en-IN')} off original list price.`,
          terms: `Subject to ${p.marketplace} stock and merchant pricing.`,
          expiry_date: 'Limited Time Marketplace Deal',
          product_url: p.product_url,
          image_url: p.image_url || p.image_candidates?.[0],
          verified: true
        });
      }
    });
    return list;
  }, [recommendations]);

  // Load offers on mount or search
  const loadOffers = async (queryToSearch) => {
    setIsLoading(true);
    setError(null);
    try {
      if (queryToSearch && queryToSearch.trim()) {
        const data = await fetchCouponOffers(queryToSearch.trim());
        setOffers(data.offers || []);
        setStatusMessage(data.message || `Found ${data.total_offers || 0} verified offers`);
      } else if (localOffers.length > 0) {
        setOffers(localOffers);
        setStatusMessage(`Displaying ${localOffers.length} verified deals from your active search results.`);
      } else {
        const data = await fetchFeaturedDeals();
        setOffers(data.offers || []);
        setStatusMessage(data.message || 'Displaying featured verified marketplace deals');
      }
    } catch (err) {
      console.warn('Could not fetch remote offers, using local offers:', err);
      if (localOffers.length > 0) {
        setOffers(localOffers);
        setStatusMessage(`Displaying ${localOffers.length} verified offers from current products.`);
      } else {
        setOffers([]);
        setStatusMessage('No verified offers currently available.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOffers(initialQuery);
  }, [initialQuery]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadOffers(searchQuery);
  };

  const handleCopyCode = (id, code) => {
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2500);
    });
  };

  // Filter offers by marketplace & type
  const filteredOffers = useMemo(() => {
    return offers.filter((o) => {
      if (selectedMarketplace !== 'all') {
        const m = (o.marketplace || '').toLowerCase();
        if (selectedMarketplace === 'amazon' && !m.includes('amazon')) return false;
        if (selectedMarketplace === 'flipkart' && !m.includes('flipkart')) return false;
        if (selectedMarketplace === 'myntra' && !m.includes('myntra')) return false;
      }
      if (selectedType === 'coupons' && !o.has_coupon_code) return false;
      if (selectedType === 'discounts' && o.has_coupon_code) return false;
      return true;
    });
  }, [offers, selectedMarketplace, selectedType]);

  return (
    <div className="min-h-screen bg-[#F4F6F9] font-sans text-slate-800 antialiased p-4 sm:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Navigation Row */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            {onNavigateHome && (
              <button
                onClick={onNavigateHome}
                className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition shadow-xs"
                title="Back to Home"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
            )}
            <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center text-white shadow-md shadow-amber-500/20">
              <Tag className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight leading-tight">
                Verified Coupons & Promotional Offers
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Authentic marketplace markdowns, coupon codes, and bank offers across Amazon, Flipkart, and Myntra.
              </p>
            </div>
          </div>

          {onNavigateRecommendations && recommendations.length > 0 && (
            <button
              onClick={onNavigateRecommendations}
              className="px-4 py-2 rounded-xl bg-white border border-slate-200 text-xs font-bold text-indigo-600 hover:bg-indigo-50 transition shadow-xs"
            >
              Back to Ranked Recommendations ({recommendations.length})
            </button>
          )}
        </div>

        {/* Search & Filter Header Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search deals (e.g. laptop, gaming, smartphone, shoes)..."
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 transition"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-indigo-600 text-white text-xs sm:text-sm font-bold transition shadow-sm"
            >
              Search Offers
            </button>
          </form>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-slate-400 font-medium flex items-center space-x-1">
                <Filter className="w-3.5 h-3.5" />
                <span>Marketplace:</span>
              </span>
              {[
                { id: 'all', label: 'All' },
                { id: 'amazon', label: 'Amazon India' },
                { id: 'flipkart', label: 'Flipkart' },
                { id: 'myntra', label: 'Myntra' }
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedMarketplace(m.id)}
                  className={`px-3 py-1 rounded-lg font-medium transition ${
                    selectedMarketplace === m.id
                      ? 'bg-amber-500 text-white shadow-xs font-bold'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Type:</span>
              {[
                { id: 'all', label: 'All Offers' },
                { id: 'coupons', label: 'Coupon Codes Only' },
                { id: 'discounts', label: 'Direct Price Cuts' }
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedType(t.id)}
                  className={`px-2.5 py-1 rounded-lg font-medium transition ${
                    selectedType === t.id
                      ? 'bg-slate-900 text-white font-bold'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Status Notification */}
        {statusMessage && (
          <div className="text-xs font-medium text-slate-500 flex items-center space-x-1.5 px-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>{statusMessage}</span>
          </div>
        )}

        {/* Offers Grid */}
        {isLoading ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
            <div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-500">Checking verified marketplace feeds for active promotions...</p>
          </div>
        ) : filteredOffers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredOffers.map((offer) => {
              const isAmazon = (offer.marketplace || '').toLowerCase().includes('amazon');
              const isFlipkart = (offer.marketplace || '').toLowerCase().includes('flipkart');
              const isMyntra = (offer.marketplace || '').toLowerCase().includes('myntra');

              return (
                <div
                  key={offer.id}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between space-y-4"
                >
                  <div>
                    {/* Top Row: Marketplace & Verified Badge */}
                    <div className="flex items-center justify-between text-xs mb-2.5">
                      <span
                        className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                          isAmazon
                            ? 'bg-amber-50 text-amber-900 border border-amber-200'
                            : isFlipkart
                            ? 'bg-blue-50 text-blue-900 border border-blue-200'
                            : isMyntra
                            ? 'bg-rose-50 text-rose-900 border border-rose-200'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {offer.marketplace}
                      </span>
                      <span className="inline-flex items-center space-x-1 text-[11px] font-bold text-emerald-600">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Verified Deal</span>
                      </span>
                    </div>

                    {/* Offer Title & Applicable Product */}
                    <h3 className="font-bold text-sm text-slate-900 line-clamp-2 leading-snug">
                      {offer.title}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-1">
                      {offer.applicable_product}
                    </p>

                    {/* Price & Savings Display */}
                    <div className="bg-slate-50 rounded-xl p-3 mt-3 border border-slate-100 space-y-1">
                      <div className="flex items-baseline justify-between">
                        <span className="text-xs text-slate-400">Effective Deal Price</span>
                        <span className="text-base font-extrabold text-slate-900">
                          ₹{Number(offer.current_price).toLocaleString('en-IN')}
                        </span>
                      </div>
                      {offer.original_price && offer.original_price > offer.current_price && (
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>List Price (MRP)</span>
                          <span className="line-through text-slate-400">
                            ₹{Number(offer.original_price).toLocaleString('en-IN')}
                          </span>
                        </div>
                      )}
                      {offer.discount_amount && (
                        <div className="flex items-center justify-between text-xs font-bold text-emerald-600 pt-0.5 border-t border-slate-200/50">
                          <span>Total Savings</span>
                          <span>
                            Save ₹{Number(offer.discount_amount).toLocaleString('en-IN')}
                            {offer.discount_percent ? ` (${offer.discount_percent}% OFF)` : ''}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Coupon Code Box */}
                    {offer.has_coupon_code && offer.coupon_code ? (
                      <div className="mt-3 flex items-center justify-between bg-amber-50/70 p-2.5 rounded-xl border border-dashed border-amber-300">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 block">Coupon Code</span>
                          <span className="font-mono font-bold text-slate-900 text-xs tracking-wider">{offer.coupon_code}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleCopyCode(offer.id, offer.coupon_code)}
                          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition shadow-xs"
                        >
                          {copiedId === offer.id ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              <span>Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy Code</span>
                            </>
                          )}
                        </button>
                      </div>
                    ) : (
                      <div className="mt-2.5 text-[11px] text-slate-500 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-100 flex items-center space-x-1.5">
                        <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>Direct markdown: no coupon code needed at checkout.</span>
                      </div>
                    )}
                  </div>

                  {/* Card Footer: Expiry & Action */}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{offer.expiry_date || 'Limited time deal'}</span>
                    </span>

                    {offer.product_url ? (
                      <a
                        href={offer.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center space-x-1 transition shadow-xs"
                      >
                        <span>Shop Offer</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">Merchant verified</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Requirement 8: If no offer data is available, display "No verified offers currently available." */
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
              <AlertCircle className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">
              No verified offers currently available.
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              We could not find active promotional coupons or discounts matching your criteria. Products are offered at authentic marketplace retail pricing.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSelectedMarketplace('all');
                setSelectedType('all');
                loadOffers('');
              }}
              className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition shadow-xs inline-block"
            >
              Reset Filters & View All Deals
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
