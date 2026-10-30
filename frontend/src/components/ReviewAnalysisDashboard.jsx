import React, { useState } from 'react';
import {
  Home,
  Search,
  Star,
  Scale,
  MessageSquare,
  User,
  Settings,
  ExternalLink,
  Smile,
  Frown,
  Meh,
  TrendingUp,
  ChevronDown
} from 'lucide-react';

// Default reference data matching the screenshot exactly
const DEFAULT_PRODUCT = {
  title: 'ASUS TUF Gaming F15',
  subtitle: 'Gaming Laptop | 15.6" FHD | Intel i5 | 16GB RAM | 512GB SSD',
  marketplaces: ['Amazon', 'Flipkart', 'Myntra'],
  totalReviews: 1248,
  positiveReviews: 864,
  positivePct: 69.2,
  negativeReviews: 248,
  negativePct: 19.9,
  neutralReviews: 136,
  neutralPct: 10.9,
  averageRating: 4.2,
  themes: [
    { name: 'Product Quality', percentage: 32, color: '#2563EB' },
    { name: 'Value for Money', percentage: 24, color: '#10B981' },
    { name: 'Battery Life', percentage: 18, color: '#F59E0B' },
    { name: 'Performance', percentage: 15, color: '#8B5CF6' },
    { name: 'Design & Build', percentage: 11, color: '#06B6D4' }
  ],
  trendDates: ['Oct 10', 'Oct 11', 'Oct 12', 'Oct 13', 'Oct 14', 'Oct 15', 'Oct 16'],
  recentReviews: [
    {
      customer: 'Rohit S.',
      rating: 4,
      sentiment: 'Positive',
      review: 'Great performance and value for money. ...'
    },
    {
      customer: 'Priya K.',
      rating: 5,
      sentiment: 'Positive',
      review: 'Battery life is excellent. Worth buying! ...'
    },
    {
      customer: 'Arun M.',
      rating: 3,
      sentiment: 'Neutral',
      review: 'Good laptop, but the build quality could be better. ...'
    },
    {
      customer: 'Sneha R.',
      rating: 2,
      sentiment: 'Negative',
      review: 'Overheating issue after long usage. ...'
    },
    {
      customer: 'Karthik V.',
      rating: 4,
      sentiment: 'Positive',
      review: 'Perfect for gaming and heavy tasks. ...'
    }
  ]
};

// Realistic ASUS TUF Laptop SVG matching the reference screenshot
function LaptopGraphic({ className = "w-28 h-20" }) {
  return (
    <div className={`${className} flex items-center justify-center shrink-0`}>
      <svg viewBox="0 0 170 115" className="w-full h-full drop-shadow">
        {/* Screen Bezel */}
        <rect x="25" y="10" width="120" height="76" rx="4" fill="#1E293B" stroke="#0F172A" strokeWidth="1.5" />
        {/* Screen Display */}
        <defs>
          <linearGradient id="tufScreen" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1E1B4B" />
            <stop offset="30%" stopColor="#2563EB" />
            <stop offset="65%" stopColor="#9333EA" />
            <stop offset="85%" stopColor="#EC4899" />
            <stop offset="100%" stopColor="#38BDF8" />
          </linearGradient>
          <linearGradient id="screenWave1" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.85" />
            <stop offset="50%" stopColor="#A855F7" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#F43F5E" stopOpacity="0.8" />
          </linearGradient>
        </defs>
        <rect x="28" y="13" width="114" height="70" rx="2" fill="url(#tufScreen)" />
        {/* Dynamic colorful wave reflections */}
        <path d="M 28 55 Q 65 22 98 48 T 142 32 L 142 83 L 28 83 Z" fill="url(#screenWave1)" opacity="0.85" />
        <path d="M 45 83 Q 80 44 118 68 T 142 62 L 142 83 L 45 83 Z" fill="#7C3AED" opacity="0.55" />
        {/* Top Camera */}
        <circle cx="85" cy="11.5" r="1.2" fill="#64748B" />
        {/* Hinge Connection */}
        <rect x="70" y="86" width="30" height="2" fill="#0F172A" />
        {/* Base Keyboard Deck */}
        <polygon points="12,102 158,102 148,86 22,86" fill="#0F172A" stroke="#1E293B" strokeWidth="1" />
        {/* Keyboard Recess */}
        <polygon points="30,97 140,97 135,88 35,88" fill="#1E293B" />
        {/* Trackpad */}
        <rect x="72" y="98" width="26" height="3" rx="0.5" fill="#334155" />
        {/* Front Lip */}
        <rect x="10" y="102" width="150" height="3" rx="1.5" fill="#334155" />
      </svg>
    </div>
  );
}

export default function ReviewAnalysisDashboard({
  product = null,
  recommendations = [],
  onSelectProduct = null,
  onNavigateHome = null,
  onNavigateSearch = null,
  onNavigateRecommendations = null,
  onNavigateComparison = null,
  onNavigateProfile = null,
  onNavigateSettings = null,
  currentUser = null,
  onSearch = null
}) {
  const [searchInput, setSearchInput] = useState('');
  const [isViewAllReviews, setIsViewAllReviews] = useState(false);

  const activeData = React.useMemo(() => {
    if (!product) {
      return DEFAULT_PRODUCT;
    }

    const ra = product.review_analysis || {};
    const totalReviews = ra.total_reviews_analyzed || product.review_count || DEFAULT_PRODUCT.totalReviews;
    const avgRating = ra.combined_rating || product.rating || DEFAULT_PRODUCT.averageRating;
    const posPct = ra.positive_percentage || DEFAULT_PRODUCT.positivePct;
    const negPct = ra.negative_percentage || DEFAULT_PRODUCT.negativePct;
    const neuPct = ra.neutral_percentage || DEFAULT_PRODUCT.neutralPct;

    const positiveCount = Math.round((posPct / 100) * totalReviews) || DEFAULT_PRODUCT.positiveReviews;
    const negativeCount = Math.round((negPct / 100) * totalReviews) || DEFAULT_PRODUCT.negativeReviews;
    const neutralCount = Math.max(0, totalReviews - positiveCount - negativeCount) || DEFAULT_PRODUCT.neutralReviews;

    let recentReviews = DEFAULT_PRODUCT.recentReviews;
    if (ra.written_reviews && ra.written_reviews.length > 0) {
      recentReviews = ra.written_reviews.slice(0, 10).map((r, idx) => ({
        customer: r.reviewer_name || `Customer ${idx + 1}`,
        rating: Math.round(r.rating || 4),
        sentiment: (r.rating || 4) >= 4 ? 'Positive' : (r.rating || 4) === 3 ? 'Neutral' : 'Negative',
        review: r.review_text || r.title || 'Verified purchase review.'
      }));
    }

    const specsList = [];
    if (product.category) specsList.push(product.category);
    if (product.specifications) {
      Object.entries(product.specifications).slice(0, 4).forEach(([k, v]) => specsList.push(`${v}`));
    }
    const subtitle = specsList.length > 0 ? specsList.join(' | ') : (product.brand || DEFAULT_PRODUCT.subtitle);

    const marketplaces = ['Amazon', 'Flipkart'];
    if (product.offers) {
      product.offers.forEach((o) => {
        const m = o.marketplace;
        if (m && !marketplaces.some((mp) => mp.toLowerCase() === m.toLowerCase())) {
          marketplaces.push(m);
        }
      });
    }
    if (!marketplaces.includes('Myntra')) {
      marketplaces.push('Myntra');
    }

    return {
      title: product.title || DEFAULT_PRODUCT.title,
      subtitle: subtitle || DEFAULT_PRODUCT.subtitle,
      image: product.image_url || product.image_candidates?.[0] || null,
      marketplaces: marketplaces.slice(0, 3),
      totalReviews,
      positiveReviews: positiveCount,
      positivePct: posPct,
      negativeReviews: negativeCount,
      negativePct: negPct,
      neutralReviews: neutralCount,
      neutralPct: neuPct,
      averageRating: avgRating,
      themes: DEFAULT_PRODUCT.themes,
      trendDates: DEFAULT_PRODUCT.trendDates,
      recentReviews
    };
  }, [product]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchInput.trim() && onSearch) {
      onSearch(searchInput.trim());
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    const full = Math.min(5, Math.max(0, Math.floor(rating)));
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} className={`text-xs ${i <= full ? 'text-amber-400' : 'text-slate-200'}`}>
          ★
        </span>
      );
    }
    return <div className="flex items-center space-x-0.5">{stars}</div>;
  };

  // SVG Doughnut Chart Calculation
  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ~314.159
  const posLength = (activeData.positivePct / 100) * circumference;
  const negLength = (activeData.negativePct / 100) * circumference;
  const neuLength = (activeData.neutralPct / 100) * circumference;

  const posOffset = 0;
  const negOffset = -posLength;
  const neuOffset = -(posLength + negLength);

  return (
    <div className="flex h-screen bg-[#F4F6F9] font-sans text-slate-800 antialiased select-none overflow-hidden">
      {/* 1. LEFT SIDEBAR */}
      <aside className="w-56 bg-[#0B132B] flex flex-col justify-start shrink-0 text-slate-300 h-screen sticky top-0 py-5 z-30">
        {/* Brand Header */}
        <div className="px-5 mb-6 flex items-center space-x-3 cursor-pointer" onClick={onNavigateHome}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white shrink-0">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.2"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
          </div>
          <div>
            <div className="text-base font-bold text-white tracking-tight leading-none">TrustRank</div>
            <div className="text-[10px] text-slate-400 mt-1 font-normal tracking-tight">
              Smarter Shopping, Better Choices
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="px-3 space-y-1 text-xs font-medium">
          <button
            onClick={onNavigateHome}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition group"
          >
            <Home className="w-4 h-4 text-slate-400 group-hover:text-white transition" />
            <span>Home</span>
          </button>

          <button
            onClick={onNavigateSearch || onNavigateHome}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition group"
          >
            <Search className="w-4 h-4 text-slate-400 group-hover:text-white transition" />
            <span>Search</span>
          </button>

          <button
            onClick={onNavigateRecommendations}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition group"
          >
            <Star className="w-4 h-4 text-slate-400 group-hover:text-white transition" />
            <span>Recommendations</span>
          </button>

          <button
            onClick={onNavigateComparison}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition group"
          >
            <Scale className="w-4 h-4 text-slate-400 group-hover:text-white transition" />
            <span>Compare Products</span>
          </button>

          {/* ACTIVE ITEM: Review Analysis */}
          <button
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl bg-[#2563EB] text-white shadow-md shadow-blue-600/30 font-medium transition"
          >
            <MessageSquare className="w-4 h-4 text-white" />
            <span>Review Analysis</span>
          </button>

          <button
            onClick={onNavigateProfile}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition group"
          >
            <User className="w-4 h-4 text-slate-400 group-hover:text-white transition" />
            <span>Profile</span>
          </button>

          <button
            onClick={onNavigateSettings}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800/60 transition group"
          >
            <Settings className="w-4 h-4 text-slate-400 group-hover:text-white transition" />
            <span>Settings</span>
          </button>
        </nav>
      </aside>

      {/* 2. MAIN VIEW AREA */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Navbar Header (Integrated seamlessly into background) */}
        <header className="h-11 px-8 flex items-center justify-between shrink-0">
          {/* Search Bar Input */}
          <form onSubmit={handleSearchSubmit} className="relative w-80 max-w-sm">
            <Search className="w-3.5 h-3.5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search for products..."
              className="w-full pl-9 pr-4 py-1.5 bg-white border border-slate-200/90 rounded-xl text-xs placeholder:text-slate-400 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition shadow-xs"
            />
          </form>

          {/* User Profile Pill */}
          <div
            onClick={onNavigateProfile}
            className="flex items-center space-x-2 cursor-pointer hover:opacity-80 transition"
          >
            <div className="w-7 h-7 rounded-full bg-slate-300/80 text-slate-600 flex items-center justify-center font-bold text-xs">
              <User className="w-3.5 h-3.5 text-slate-600" />
            </div>
            <span className="text-xs font-semibold text-slate-700">
              {currentUser?.name || 'Hi, User'}
            </span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </div>
        </header>

        {/* Dashboard Main Content Container */}
        <main className="px-8 pb-3 pt-0 space-y-2.5 max-w-7xl w-full mx-auto">
          {/* Page Title & Description */}
          <div className="flex items-center space-x-2.5">
            <div className="text-[#2563EB] shrink-0">
              <svg className="w-7 h-7 text-[#2563EB]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                <circle cx="8" cy="10" r="1.2" fill="white" />
                <circle cx="12" cy="10" r="1.2" fill="white" />
                <circle cx="16" cy="10" r="1.2" fill="white" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight leading-tight">
                Review Analysis
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Understand what customers are saying. Get insights from real reviews.
              </p>
            </div>
          </div>

          {/* ROW 1: Product Information Card & Total Reviews Analyzed */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
            {/* Product Information Card */}
            <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3.5">
              <div className="flex items-center space-x-3 min-w-0">
                {/* Product Image / Laptop Mockup */}
                <div className="w-24 h-18 bg-slate-50 rounded-xl border border-slate-100 p-1 flex items-center justify-center shrink-0 overflow-hidden">
                  {activeData.image ? (
                    <img
                      src={activeData.image}
                      alt={activeData.title}
                      referrerPolicy="no-referrer"
                      className="max-h-full max-w-full object-contain"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div style={{ display: activeData.image ? 'none' : 'flex' }}>
                    <LaptopGraphic className="w-24 h-16" />
                  </div>
                </div>

                {/* Product Meta */}
                <div className="min-w-0">
                  <h2 className="text-sm font-bold text-slate-900 truncate">
                    {activeData.title}
                  </h2>
                  <p className="text-[11px] text-slate-500 mt-0.5 truncate max-w-md">
                    {activeData.subtitle}
                  </p>

                  {/* Marketplaces */}
                  <div className="flex items-center space-x-3.5 mt-2">
                    {/* Amazon */}
                    <div className="flex items-center space-x-1 text-xs text-slate-700 font-medium">
                      <span className="font-extrabold text-slate-900 text-sm tracking-tighter">a</span>
                      <span>Amazon</span>
                    </div>

                    {/* Flipkart */}
                    <div className="flex items-center space-x-1 text-xs text-slate-700 font-medium">
                      <span className="w-3.5 h-3.5 rounded bg-[#F59E0B] text-white font-black text-[9px] flex items-center justify-center leading-none">
                        f
                      </span>
                      <span>Flipkart</span>
                    </div>

                    {/* Myntra */}
                    <div className="flex items-center space-x-1 text-xs text-slate-700 font-medium">
                      <span className="font-bold text-rose-500 text-xs">M</span>
                      <span>Myntra</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* View Product Details Button */}
              <button
                type="button"
                onClick={() => {
                  if (onSelectProduct && product) {
                    onSelectProduct(product);
                  }
                }}
                className="bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-medium px-3.5 py-2 rounded-xl shadow-sm shadow-blue-500/20 flex items-center space-x-1.5 shrink-0 transition"
              >
                <span>View Product Details</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>

            {/* Total Reviews Analyzed Card */}
            <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-sm flex flex-col justify-between">
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span className="text-xs font-semibold text-slate-700">Total Reviews Analyzed</span>
              </div>

              <div className="my-0.5">
                <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                  {Number(activeData.totalReviews).toLocaleString('en-IN')}
                </span>
              </div>

              <div className="text-[11px] text-slate-400">from multiple marketplaces</div>
            </div>
          </div>

          {/* ROW 2: Four Sentiment Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* 1. Positive Reviews */}
            <div className="bg-white rounded-2xl border border-emerald-100 p-3.5 shadow-sm space-y-0.5">
              <div className="w-5 h-5 rounded-full bg-emerald-50 text-emerald-500 flex items-center justify-center mb-1">
                <Smile className="w-3.5 h-3.5" />
              </div>
              <div className="text-[11px] font-semibold text-emerald-600">Positive Reviews</div>
              <div className="text-xl font-bold text-slate-900">{activeData.positiveReviews}</div>
              <div className="text-[10px] text-slate-400">({activeData.positivePct}%)</div>
            </div>

            {/* 2. Negative Reviews */}
            <div className="bg-white rounded-2xl border border-rose-100 p-3.5 shadow-sm space-y-0.5">
              <div className="w-5 h-5 rounded-full bg-rose-50 text-rose-500 flex items-center justify-center mb-1">
                <Frown className="w-3.5 h-3.5" />
              </div>
              <div className="text-[11px] font-semibold text-rose-500">Negative Reviews</div>
              <div className="text-xl font-bold text-slate-900">{activeData.negativeReviews}</div>
              <div className="text-[10px] text-slate-400">({activeData.negativePct}%)</div>
            </div>

            {/* 3. Neutral Reviews */}
            <div className="bg-white rounded-2xl border border-slate-100 p-3.5 shadow-sm space-y-0.5">
              <div className="w-5 h-5 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mb-1">
                <Meh className="w-3.5 h-3.5" />
              </div>
              <div className="text-[11px] font-semibold text-slate-500">Neutral Reviews</div>
              <div className="text-xl font-bold text-slate-900">{activeData.neutralReviews}</div>
              <div className="text-[10px] text-slate-400">({activeData.neutralPct}%)</div>
            </div>

            {/* 4. Average Rating */}
            <div className="bg-white rounded-2xl border border-blue-100 p-3.5 shadow-sm space-y-0.5">
              <div className="w-5 h-5 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center mb-1">
                <Star className="w-3.5 h-3.5 text-blue-500" strokeWidth={2} />
              </div>
              <div className="text-[11px] font-semibold text-blue-600">Average Rating</div>
              <div className="text-xl font-bold text-slate-900">{Number(activeData.averageRating).toFixed(1)}</div>
              <div className="text-[10px] text-slate-400">(out of 5)</div>
            </div>
          </div>

          {/* ROW 3: Sentiment Distribution & Review Themes */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
            {/* Sentiment Distribution Card */}
            <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col justify-between">
              <h3 className="text-xs font-bold text-slate-900 mb-1.5">Sentiment Distribution</h3>
              <div className="flex items-center justify-around gap-4 py-1">
                {/* SVG Doughnut Chart */}
                <div className="relative w-32 h-32 flex items-center justify-center shrink-0">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 130 130">
                    {/* Background ring */}
                    <circle cx="65" cy="65" r={radius} fill="none" stroke="#F1F5F9" strokeWidth="15" />

                    {/* Positive Arc (Green) */}
                    <circle
                      cx="65"
                      cy="65"
                      r={radius}
                      fill="none"
                      stroke="#10B981"
                      strokeWidth="15"
                      strokeDasharray={`${posLength} ${circumference}`}
                      strokeDashoffset={posOffset}
                      strokeLinecap="round"
                    />

                    {/* Negative Arc (Red) */}
                    <circle
                      cx="65"
                      cy="65"
                      r={radius}
                      fill="none"
                      stroke="#EF4444"
                      strokeWidth="15"
                      strokeDasharray={`${negLength} ${circumference}`}
                      strokeDashoffset={negOffset}
                    />

                    {/* Neutral Arc (Slate) */}
                    <circle
                      cx="65"
                      cy="65"
                      r={radius}
                      fill="none"
                      stroke="#94A3B8"
                      strokeWidth="15"
                      strokeDasharray={`${neuLength} ${circumference}`}
                      strokeDashoffset={neuOffset}
                    />
                  </svg>

                  {/* Center Text */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span className="text-base font-extrabold text-slate-900 leading-none">
                      {activeData.positivePct}%
                    </span>
                    <span className="text-[10px] text-slate-500 font-medium mt-0.5">Positive</span>
                  </div>
                </div>

                {/* Legend list */}
                <div className="space-y-2.5">
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="w-2 h-2 rounded-full bg-[#10B981] shrink-0"></span>
                    <span className="w-16 font-medium text-slate-700">Positive</span>
                    <span className="font-semibold text-slate-900">{activeData.positivePct}%</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="w-2 h-2 rounded-full bg-[#EF4444] shrink-0"></span>
                    <span className="w-16 font-medium text-slate-700">Negative</span>
                    <span className="font-semibold text-slate-900">{activeData.negativePct}%</span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="w-2 h-2 rounded-full bg-[#94A3B8] shrink-0"></span>
                    <span className="w-16 font-medium text-slate-700">Neutral</span>
                    <span className="font-semibold text-slate-900">{activeData.neutralPct}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Review Themes Card */}
            <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col justify-between">
              <h3 className="text-xs font-bold text-slate-900 mb-1.5">Review Themes</h3>
              <div className="space-y-2">
                {activeData.themes.map((theme, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs">
                    <span className="w-24 text-slate-700 font-medium shrink-0 text-[11px]">{theme.name}</span>
                    <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden mx-3">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${(theme.percentage / 36) * 100}%`, backgroundColor: theme.color }}
                      ></div>
                    </div>
                    <span className="w-8 text-right font-semibold text-slate-600 text-[11px]">{theme.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ROW 4: Review Trend & Recent Reviews */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5">
            {/* Review Trend Line Chart */}
            <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm flex flex-col justify-between">
              {/* Header with Legend */}
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-900">
                  <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                  <span>Review Trend</span>
                </div>

                <div className="flex items-center space-x-2.5 text-[10px] font-medium text-slate-600">
                  <div className="flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
                    <span>Positive</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444]"></span>
                    <span>Negative</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#94A3B8]"></span>
                    <span>Neutral</span>
                  </div>
                </div>
              </div>

              {/* SVG Line Chart */}
              <div className="w-full h-32 relative pt-0.5">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 500 145">
                  <defs>
                    <linearGradient id="trendPositiveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10B981" stopOpacity="0.22" />
                      <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
                    </linearGradient>
                    <linearGradient id="trendNegativeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#EF4444" stopOpacity="0.18" />
                      <stop offset="100%" stopColor="#EF4444" stopOpacity="0" />
                    </linearGradient>
                    <linearGradient id="trendNeutralGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#94A3B8" stopOpacity="0.12" />
                      <stop offset="100%" stopColor="#94A3B8" stopOpacity="0" />
                    </linearGradient>
                  </defs>

                  {/* Horizontal Grid Lines & Y-Axis Labels */}
                  {[
                    { label: '200', y: 10 },
                    { label: '150', y: 37 },
                    { label: '100', y: 64 },
                    { label: '50', y: 91 },
                    { label: '0', y: 118 }
                  ].map((grid, idx) => (
                    <g key={idx}>
                      <text x="5" y={grid.y + 3} fill="#94A3B8" fontSize="8" fontWeight="500">
                        {grid.label}
                      </text>
                      <line x1="28" y1={grid.y} x2="490" y2={grid.y} stroke="#F1F5F9" strokeWidth="1" strokeDasharray="3 3" />
                    </g>
                  ))}

                  {/* Positive Area & Line */}
                  <polygon
                    points="55,118 55,74 123,60 191,67 259,55 327,57 395,52 463,44 463,118"
                    fill="url(#trendPositiveGrad)"
                  />
                  <polyline
                    fill="none"
                    stroke="#10B981"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    points="55,74 123,60 191,67 259,55 327,57 395,52 463,44"
                  />
                  {[[55, 74], [123, 60], [191, 67], [259, 55], [327, 57], [395, 52], [463, 44]].map(([cx, cy], i) => (
                    <circle key={i} cx={cx} cy={cy} r="2.8" fill="#10B981" stroke="#FFFFFF" strokeWidth="1.2" />
                  ))}

                  {/* Negative Area & Line */}
                  <polygon
                    points="55,118 55,98 123,86 191,88 259,77 327,79 395,81 463,75 463,118"
                    fill="url(#trendNegativeGrad)"
                  />
                  <polyline
                    fill="none"
                    stroke="#EF4444"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    points="55,98 123,86 191,88 259,77 327,79 395,81 463,75"
                  />
                  {[[55, 98], [123, 86], [191, 88], [259, 77], [327, 79], [395, 81], [463, 75]].map(([cx, cy], i) => (
                    <circle key={i} cx={cx} cy={cy} r="2.8" fill="#EF4444" stroke="#FFFFFF" strokeWidth="1.2" />
                  ))}

                  {/* Neutral Area & Line */}
                  <polygon
                    points="55,118 55,109 123,98 191,98 259,95 327,90 395,95 463,100 463,118"
                    fill="url(#trendNeutralGrad)"
                  />
                  <polyline
                    fill="none"
                    stroke="#94A3B8"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    points="55,109 123,98 191,98 259,95 327,90 395,95 463,100"
                  />
                  {[[55, 109], [123, 98], [191, 98], [259, 95], [327, 90], [395, 95], [463, 100]].map(([cx, cy], i) => (
                    <circle key={i} cx={cx} cy={cy} r="2.8" fill="#94A3B8" stroke="#FFFFFF" strokeWidth="1.2" />
                  ))}

                  {/* X-Axis Dates */}
                  {activeData.trendDates.map((date, idx) => {
                    const x = 55 + idx * 68;
                    return (
                      <text key={idx} x={x} y="134" fill="#94A3B8" fontSize="8" textAnchor="middle" fontWeight="500">
                        {date}
                      </text>
                    );
                  })}
                </svg>
              </div>
            </div>

            {/* Recent Reviews Table Card */}
            <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200/80 p-3.5 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-900">
                    <svg className="w-3.5 h-3.5 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                      <circle cx="8" cy="10" r="1.2" fill="white" />
                      <circle cx="12" cy="10" r="1.2" fill="white" />
                      <circle cx="16" cy="10" r="1.2" fill="white" />
                    </svg>
                    <span>Recent Reviews</span>
                  </div>
                  <button
                    onClick={() => setIsViewAllReviews(!isViewAllReviews)}
                    className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 transition"
                  >
                    {isViewAllReviews ? 'Show Less' : 'View All'}
                  </button>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-slate-100 text-[10px] font-medium text-slate-400">
                        <th className="pb-1 w-24">Customer</th>
                        <th className="pb-1 w-20">Rating</th>
                        <th className="pb-1 w-18">Sentiment</th>
                        <th className="pb-1">Review</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-xs">
                      {(isViewAllReviews ? activeData.recentReviews : activeData.recentReviews.slice(0, 5)).map(
                        (rev, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50 transition">
                            <td className="py-1 pr-2 font-medium text-slate-800 flex items-center space-x-1.5">
                              <div className="w-4 h-4 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
                                <User className="w-2.5 h-2.5" />
                              </div>
                              <span className="truncate max-w-[80px] text-[11px]">{rev.customer}</span>
                            </td>
                            <td className="py-1 pr-2 whitespace-nowrap">{renderStars(rev.rating)}</td>
                            <td className="py-1 pr-2 whitespace-nowrap">
                              <span
                                className={`text-[9px] font-medium px-2 py-0.5 rounded-full inline-block ${
                                  rev.sentiment === 'Positive'
                                    ? 'bg-emerald-50 text-emerald-600'
                                    : rev.sentiment === 'Negative'
                                    ? 'bg-rose-50 text-rose-600'
                                    : 'bg-slate-100 text-slate-600'
                                }`}
                              >
                                {rev.sentiment}
                              </span>
                            </td>
                            <td className="py-1 text-slate-600 truncate max-w-[190px] text-[11px]">{rev.review}</td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
