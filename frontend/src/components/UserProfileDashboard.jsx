import React, { useState, useEffect, useMemo } from 'react';
import {
  User,
  Search,
  Sparkles,
  Layers,
  MessageSquare,
  Tag,
  Bookmark,
  Heart,
  Bell,
  ToggleLeft,
  ToggleRight,
  Trash2,
  ExternalLink,
  Clock,
  ArrowLeft,
  Check,
  Copy,
  Calendar,
  ShieldCheck,
  AlertCircle,
  Eye,
  RefreshCw,
  ShoppingBag,
  Star,
  ChevronRight,
  Filter,
  Mail
} from 'lucide-react';
import {
  fetchProfileDashboard,
  fetchResearchHistory,
  clearResearchHistory,
  removeSavedProduct,
  saveProduct,
  fetchPriceAlerts,
  updateAlertStatus,
  deletePriceAlert,
  checkPriceAlertsNow,
  updateAlertEmail
} from '../services/api';

export default function UserProfileDashboard({
  currentUser,
  authToken,
  onOpenAuthModal,
  onNavigateHome,
  onNavigateRecommendations,
  onNavigateComparison,
  onNavigateReviewAnalysis,
  onNavigateCoupons,
  onReopenSearch,
  onSelectProduct
}) {
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'search' | 'recommendation' | 'comparison' | 'review_analysis' | 'coupon' | 'saved'
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [copiedCouponId, setCopiedCouponId] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearTargetCategory, setClearTargetCategory] = useState('all');
  const [wishlistSort, setWishlistSort] = useState('newest'); // 'newest' | 'discount' | 'price_asc'
  const [alertsData, setAlertsData] = useState({ alerts: [], unread_notifications: [], total_alerts: 0, active_alerts: 0, target_reached_alerts: 0 });
  const [isCheckingAlerts, setIsCheckingAlerts] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState('');
  const [alertEmail, setAlertEmail] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('trustrank_user_email') || currentUser?.email || '';
    }
    return '';
  });
  const [isUpdatingAlertEmail, setIsUpdatingAlertEmail] = useState(false);
  const [alertEmailMsg, setAlertEmailMsg] = useState('');
  const [alertEmailError, setAlertEmailError] = useState('');

  // Load dashboard data
  const loadDashboard = async (showLoadingSpinner = true) => {
    if (showLoadingSpinner) setIsLoading(true);
    else setIsRefreshing(true);
    setError(null);
    try {
      const [data, alerts] = await Promise.all([
        fetchProfileDashboard(authToken),
        fetchPriceAlerts(authToken).catch(() => ({ alerts: [], unread_notifications: [], total_alerts: 0, active_alerts: 0, target_reached_alerts: 0 }))
      ]);
      setDashboardData(data);
      setAlertsData(alerts);
    } catch (err) {
      console.error('Failed to load profile dashboard:', err);
      setError('Unable to load customer research history. Please check connection or try again.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboard(true);
  }, [authToken]);

  const showNotification = (msg) => {
    setActionSuccessMsg(msg);
    setTimeout(() => setActionSuccessMsg(''), 3000);
  };

  // Handle Price Alert Status Toggle
  const handleToggleAlertStatus = async (alertId, currentStatus) => {
    try {
      const nextStatus = currentStatus === 'active' ? 'disabled' : 'active';
      await updateAlertStatus(authToken, alertId, nextStatus);
      showNotification(`Alert is now ${nextStatus}.`);
      await loadDashboard(false);
    } catch (err) {
      console.error('Failed to toggle alert status:', err);
    }
  };

  // Handle Delete Price Alert
  const handleDeleteAlert = async (alertId, title) => {
    try {
      await deletePriceAlert(authToken, alertId);
      showNotification(`Price alert for "${title.slice(0, 30)}..." deleted.`);
      await loadDashboard(false);
    } catch (err) {
      console.error('Failed to delete alert:', err);
    }
  };

  // Handle On-Demand Price Check
  const handleCheckPricesNow = async () => {
    setIsCheckingAlerts(true);
    try {
      const res = await checkPriceAlertsNow(authToken);
      showNotification(`Price check completed: ${res.checked_count} checked, ${res.triggered_count} targets reached.`);
      await loadDashboard(false);
    } catch (err) {
      console.error('Failed to run price check:', err);
    } finally {
      setIsCheckingAlerts(false);
    }
  };

  // Handle Update Alert Notification Email
  const handleUpdateAlertEmail = async (e) => {
    if (e) e.preventDefault();
    if (!alertEmail || !alertEmail.trim()) {
      setAlertEmailError('Please enter a valid email address.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(alertEmail.trim())) {
      setAlertEmailError('Please enter a valid email address (e.g. name@example.com).');
      return;
    }
    setIsUpdatingAlertEmail(true);
    setAlertEmailError('');
    try {
      const res = await updateAlertEmail(authToken, alertEmail.trim());
      if (typeof window !== 'undefined') {
        localStorage.setItem('trustrank_user_email', alertEmail.trim());
      }
      setAlertEmailMsg(`Email updated to ${res.email_masked}. Price drop alerts will notify this address.`);
      setTimeout(() => setAlertEmailMsg(''), 4000);
      await loadDashboard(false);
    } catch (err) {
      setAlertEmailError(err.message || 'Failed to update alert notification email.');
    } finally {
      setIsUpdatingAlertEmail(false);
    }
  };

  // Handle Remove Saved Product
  const handleRemoveSaved = async (productId, title) => {
    try {
      await removeSavedProduct(authToken, productId);
      showNotification(`Removed "${title.slice(0, 30)}..." from saved items.`);
      await loadDashboard(false);
    } catch (err) {
      console.error('Failed to remove saved product:', err);
    }
  };

  // Handle Clear History
  const handleConfirmClearHistory = async () => {
    try {
      const catToClear = clearTargetCategory === 'all' ? null : clearTargetCategory;
      await clearResearchHistory(authToken, catToClear);
      setShowClearConfirm(false);
      showNotification(
        clearTargetCategory === 'all'
          ? 'All research history cleared successfully.'
          : `${clearTargetCategory.replace('_', ' ')} history cleared.`
      );
      await loadDashboard(false);
    } catch (err) {
      console.error('Failed to clear history:', err);
    }
  };

  // Copy coupon code
  const handleCopyCode = (id, code) => {
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCouponId(id);
      setTimeout(() => setCopiedCouponId(null), 2500);
    });
  };

  // Format date helper
  const formatDate = (isoString) => {
    if (!isoString) return 'Recent';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  const getInitials = (user) => {
    if (user?.name) return user.name.charAt(0).toUpperCase();
    if (user?.email) return user.email.charAt(0).toUpperCase();
    return 'C';
  };

  const stats = dashboardData?.stats || {
    total_searches: 0,
    total_recommendations: 0,
    total_comparisons: 0,
    total_reviews_analyzed: 0,
    total_coupons_viewed: 0,
    total_saved_products: 0
  };

  const customer = dashboardData?.customer || currentUser;
  const historyItems = dashboardData?.recent_history || [];
  const savedProducts = dashboardData?.saved_products || [];

  // Smart Wishlist: Total savings calculation & sorting
  const totalSavings = useMemo(() => {
    return savedProducts.reduce((sum, p) => {
      const price = Number(p.price);
      const orig = Number(p.original_price);
      if (Number.isFinite(orig) && Number.isFinite(price) && orig > price) {
        return sum + (orig - price);
      }
      return sum;
    }, 0);
  }, [savedProducts]);

  const sortedWishlist = useMemo(() => {
    const list = [...savedProducts];
    if (wishlistSort === 'discount') {
      return list.sort((a, b) => {
        const discA = (a.original_price && a.price && a.original_price > a.price) ? (a.original_price - a.price) : 0;
        const discB = (b.original_price && b.price && b.original_price > b.price) ? (b.original_price - b.price) : 0;
        return discB - discA;
      });
    }
    if (wishlistSort === 'price_asc') {
      return list.sort((a, b) => (Number(a.price) || 0) - (Number(b.price) || 0));
    }
    return list;
  }, [savedProducts, wishlistSort]);

  // Filter history items by active tab
  const filteredHistory = useMemo(() => {
    if (activeTab === 'all') return historyItems;
    if (activeTab === 'saved') return [];
    return historyItems.filter((item) => item.category === activeTab);
  }, [historyItems, activeTab]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-16">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="bg-white border-b border-slate-200 sticky top-16 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={onNavigateHome}
              className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition flex items-center space-x-1 text-xs font-semibold"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Back to Search</span>
            </button>
            <div className="h-5 w-px bg-slate-200" />
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">
                TR
              </div>
              <div>
                <h1 className="text-sm sm:text-base font-bold text-slate-900 leading-tight">
                  Customer Profile & Research History
                </h1>
                <p className="text-[11px] text-slate-500 hidden sm:block">
                  Revisit previous searches, recommendations, comparisons, and reviews
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => loadDashboard(false)}
              disabled={isRefreshing}
              className="p-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600 transition text-xs flex items-center space-x-1"
              title="Refresh Research History"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-indigo-600' : ''}`} />
              <span className="hidden md:inline">Refresh</span>
            </button>

            {historyItems.length > 0 && (
              <button
                onClick={() => {
                  setClearTargetCategory(activeTab === 'saved' ? 'all' : activeTab);
                  setShowClearConfirm(true);
                }}
                className="px-3 py-1.5 rounded-xl border border-rose-200 text-rose-600 hover:bg-rose-50 transition text-xs font-semibold flex items-center space-x-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear History</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Action Toast Alert */}
      {actionSuccessMsg && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-4 py-2.5 rounded-xl shadow-xl flex items-center space-x-2 text-xs font-medium animate-in fade-in slide-in-from-bottom-3 duration-200">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* SECTION 1: PROFILE DASHBOARD HEADER */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-indigo-50/80 via-blue-50/40 to-transparent rounded-full pointer-events-none -mr-20 -mt-20" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            {/* Customer Avatar & Bio */}
            <div className="flex items-start sm:items-center space-x-4">
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-purple-600 text-white font-extrabold flex items-center justify-center text-2xl sm:text-3xl shadow-lg shadow-indigo-600/20 border-2 border-white">
                {getInitials(customer)}
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                    {customer?.name || (customer?.email ? customer.email.split('@')[0] : 'Guest Customer')}
                  </h2>
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                    <ShieldCheck className="w-3 h-3 text-emerald-600" />
                    <span>{customer ? 'Verified Member' : 'Guest Session'}</span>
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 font-medium">
                  {customer?.email || 'Guest mode — Log in to securely sync your research history across all devices'}
                </p>
                <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-500">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>Member since: {formatDate(customer?.created_at)}</span>
                  </span>
                  {customer?.last_login_at && (
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>Last active: {formatDate(customer.last_login_at)}</span>
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Account Status / Sign In Button */}
            <div className="flex items-center space-x-3 self-start md:self-center">
              {!currentUser && onOpenAuthModal && (
                <button
                  onClick={onOpenAuthModal}
                  className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition flex items-center space-x-1.5"
                >
                  <User className="w-4 h-4" />
                  <span>Sign In / Create Account</span>
                </button>
              )}
              {currentUser && (
                <div className="bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200 text-right">
                  <p className="text-[11px] text-slate-500 font-medium">Session Status</p>
                  <p className="text-xs font-bold text-emerald-600 flex items-center justify-end space-x-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span>Active & Synced</span>
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* METRIC COUNTERS (5 Key Pillars) */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mt-8 pt-6 border-t border-slate-100">
            {/* 1. Products Searched */}
            <div
              onClick={() => setActiveTab('search')}
              className={`p-4 rounded-2xl border transition cursor-pointer ${
                activeTab === 'search'
                  ? 'bg-indigo-50/80 border-indigo-200 ring-2 ring-indigo-500/20'
                  : 'bg-slate-50 hover:bg-slate-100/80 border-slate-200/70'
              }`}
            >
              <div className="flex items-center justify-between text-indigo-600 mb-2">
                <Search className="w-4 h-4" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Searches</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{stats.total_searches}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Queries Researched</p>
            </div>

            {/* 2. Recommendations Viewed */}
            <div
              onClick={() => setActiveTab('recommendation')}
              className={`p-4 rounded-2xl border transition cursor-pointer ${
                activeTab === 'recommendation'
                  ? 'bg-indigo-50/80 border-indigo-200 ring-2 ring-indigo-500/20'
                  : 'bg-slate-50 hover:bg-slate-100/80 border-slate-200/70'
              }`}
            >
              <div className="flex items-center justify-between text-blue-600 mb-2">
                <Sparkles className="w-4 h-4" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Ranked</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{stats.total_recommendations}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Recs Explored</p>
            </div>

            {/* 3. Comparisons Viewed */}
            <div
              onClick={() => setActiveTab('comparison')}
              className={`p-4 rounded-2xl border transition cursor-pointer ${
                activeTab === 'comparison'
                  ? 'bg-indigo-50/80 border-indigo-200 ring-2 ring-indigo-500/20'
                  : 'bg-slate-50 hover:bg-slate-100/80 border-slate-200/70'
              }`}
            >
              <div className="flex items-center justify-between text-purple-600 mb-2">
                <Layers className="w-4 h-4" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Top 5</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{stats.total_comparisons}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Comparisons Run</p>
            </div>

            {/* 4. Review Analyses Viewed */}
            <div
              onClick={() => setActiveTab('review_analysis')}
              className={`p-4 rounded-2xl border transition cursor-pointer ${
                activeTab === 'review_analysis'
                  ? 'bg-indigo-50/80 border-indigo-200 ring-2 ring-indigo-500/20'
                  : 'bg-slate-50 hover:bg-slate-100/80 border-slate-200/70'
              }`}
            >
              <div className="flex items-center justify-between text-emerald-600 mb-2">
                <MessageSquare className="w-4 h-4" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Reviews</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{stats.total_reviews_analyzed}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Sentiments Checked</p>
            </div>

            {/* 5. Coupons & Offers Explored */}
            <div
              onClick={() => setActiveTab('coupon')}
              className={`p-4 rounded-2xl border transition cursor-pointer ${
                activeTab === 'coupon'
                  ? 'bg-indigo-50/80 border-indigo-200 ring-2 ring-indigo-500/20'
                  : 'bg-slate-50 hover:bg-slate-100/80 border-slate-200/70'
              }`}
            >
              <div className="flex items-center justify-between text-amber-600 mb-2">
                <Tag className="w-4 h-4" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Offers</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{stats.total_coupons_viewed}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Deals Discovered</p>
            </div>

            {/* 6. Saved Products */}
            <div
              onClick={() => setActiveTab('saved')}
              className={`p-4 rounded-2xl border transition cursor-pointer ${
                activeTab === 'saved'
                  ? 'bg-indigo-50/80 border-indigo-200 ring-2 ring-indigo-500/20'
                  : 'bg-slate-50 hover:bg-slate-100/80 border-slate-200/70'
              }`}
            >
              <div className="flex items-center justify-between text-rose-600 mb-2">
                <Bookmark className="w-4 h-4" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Wishlist</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{stats.total_saved_products}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Wishlist Items</p>
            </div>
          </div>
        </div>

        {/* IN-APP PRICE DROP NOTIFICATION BANNER */}
        {alertsData.unread_notifications && alertsData.unread_notifications.length > 0 && (
          <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white rounded-3xl p-5 shadow-lg space-y-3 animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center font-bold">
                  <Bell className="w-4 h-4 text-white animate-bounce" />
                </div>
                <div>
                  <h4 className="font-extrabold text-sm sm:text-base leading-tight">
                    Price Drop Alert Reached ({alertsData.unread_notifications.length})
                  </h4>
                  <p className="text-xs text-emerald-100">
                    Live verified prices have dropped to or below your target price!
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveTab('alerts')}
                className="px-3 py-1.5 rounded-xl bg-white text-emerald-800 text-xs font-bold hover:bg-emerald-50 transition shadow-xs"
              >
                View Alerts
              </button>
            </div>
            <div className="space-y-2 pt-1 border-t border-white/20">
              {alertsData.unread_notifications.map((notif) => (
                <div key={notif.id} className="bg-white/10 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div>
                    <span className="font-bold">{notif.product_title}</span>
                    <span className="opacity-80"> on {notif.marketplace}</span>
                    <p className="text-[11px] text-emerald-200 mt-0.5">{notif.message}</p>
                  </div>
                  {notif.product_url && (
                    <a
                      href={notif.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-lg bg-white/20 hover:bg-white/30 text-white font-bold transition flex items-center space-x-1 shrink-0 self-start sm:self-auto"
                    >
                      <span>Buy Now</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SECTION 2: SMART WISHLIST & SAVED PRODUCTS */}
        {(activeTab === 'all' || activeTab === 'saved') && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold shadow-xs">
                  <Heart className="w-5 h-5 fill-rose-500 text-rose-500" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-extrabold text-slate-900 text-base sm:text-lg">Smart Wishlist ({savedProducts.length})</h3>
                    {totalSavings > 0 && (
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-200">
                        <span>⚡ ₹{Math.round(totalSavings).toLocaleString('en-IN')} Total Savings</span>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Live price tracking, discount notifications, and multi-marketplace stock alerts
                  </p>
                </div>
              </div>

              {savedProducts.length > 0 && (
                <div className="flex items-center space-x-2 self-start sm:self-center">
                  <span className="text-[11px] font-semibold text-slate-400">Sort:</span>
                  <select
                    value={wishlistSort}
                    onChange={(e) => setWishlistSort(e.target.value)}
                    className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 text-slate-700"
                  >
                    <option value="newest">Recently Saved</option>
                    <option value="discount">Highest Discount</option>
                    <option value="price_asc">Lowest Price</option>
                  </select>
                </div>
              )}
            </div>

            {savedProducts.length === 0 ? (
              <div className="py-10 text-center max-w-sm mx-auto space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-rose-50 text-rose-400 flex items-center justify-center mx-auto">
                  <Heart className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-800">Your Smart Wishlist is empty</h4>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    Click the Wishlist button on any product card to track price drops, merchant discounts, and store availability.
                  </p>
                </div>
                <button
                  onClick={onNavigateHome}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
                >
                  Browse Recommendations
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {sortedWishlist.map((p) => {
                  const hasDiscount = p.original_price && p.price && p.original_price > p.price;
                  const discountAmount = hasDiscount ? Math.round(p.original_price - p.price) : 0;
                  const discountPct = hasDiscount ? Math.round((discountAmount / p.original_price) * 100) : 0;

                  return (
                    <div
                      key={p.id}
                      className="rounded-2xl border border-slate-200/90 p-4 hover:shadow-md transition bg-slate-50/50 flex flex-col justify-between group hover:border-slate-300"
                    >
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-700">
                            {p.marketplace || 'Amazon India'}
                          </span>
                          <button
                            onClick={() => handleRemoveSaved(p.product_id, p.title)}
                            className="text-slate-400 hover:text-rose-600 transition p-1"
                            title="Remove from Smart Wishlist"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        {p.image_url && (
                          <div className="h-32 w-full flex items-center justify-center my-3 bg-white rounded-xl p-2 border border-slate-100">
                            <img
                              src={p.image_url}
                              alt={p.title}
                              className="max-h-full max-w-full object-contain group-hover:scale-105 transition duration-200"
                            />
                          </div>
                        )}

                        <h4 className="text-xs font-bold text-slate-900 line-clamp-2 mt-2 leading-snug" title={p.title}>
                          {p.title}
                        </h4>

                        <div className="flex flex-wrap items-baseline gap-2 mt-2">
                          {p.price && (
                            <span className="text-sm font-black text-slate-900">
                              ₹{Number(p.price).toLocaleString('en-IN')}
                            </span>
                          )}
                          {hasDiscount && (
                            <span className="text-xs text-slate-400 line-through">
                              ₹{Number(p.original_price).toLocaleString('en-IN')}
                            </span>
                          )}
                          {p.rating && (
                            <span className="ml-auto flex items-center text-xs font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                              ★ {Number(p.rating).toFixed(1)}
                            </span>
                          )}
                        </div>

                        {/* Smart Price Drop Badge */}
                        {hasDiscount && (
                          <div className="mt-2.5">
                            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[10px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-200">
                              <span>⚡ Save ₹{discountAmount.toLocaleString('en-IN')} ({discountPct}% Off)</span>
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-200 flex items-center space-x-2">
                        {onSelectProduct && (
                          <button
                            onClick={() => onSelectProduct(p)}
                            className="flex-1 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition flex items-center justify-center space-x-1"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Details</span>
                          </button>
                        )}
                        {p.product_url && (
                          <a
                            href={p.product_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 transition"
                            title="View product on store"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* SECTION 2.5: PRICE DROP ALERTS MANAGEMENT */}
        {(activeTab === 'all' || activeTab === 'alerts') && (
          <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold shadow-xs">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-extrabold text-slate-900 text-base sm:text-lg">
                      Price Drop Alerts ({alertsData.alerts.length})
                    </h3>
                    {alertsData.target_reached_alerts > 0 && (
                      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-200">
                        <span>🎉 {alertsData.target_reached_alerts} Target Reached</span>
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Periodic verified marketplace tracking. Triggers only on genuine price drops.
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2 self-start sm:self-center">
                <button
                  onClick={handleCheckPricesNow}
                  disabled={isCheckingAlerts}
                  className="px-3.5 py-1.5 rounded-xl border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-bold transition flex items-center space-x-1.5"
                  title="Check live marketplace prices for active alerts now"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isCheckingAlerts ? 'animate-spin' : ''}`} />
                  <span>{isCheckingAlerts ? 'Checking Live Prices...' : 'Check Prices Now'}</span>
                </button>
              </div>
            </div>

            {/* Email Notification Settings Banner */}
            <div className="bg-slate-50 border border-slate-200/90 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 mt-0.5">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-slate-800">Alert Notification Email</span>
                    {alertsData.alerts.some((a) => a.user_email_masked) && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200/60 font-mono">
                        Active: {alertsData.alerts.find((a) => a.user_email_masked)?.user_email_masked}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Automatic email dispatch when genuine marketplace price reaches or drops below your target.
                  </p>
                </div>
              </div>

              <form onSubmit={handleUpdateAlertEmail} className="flex items-center space-x-2 shrink-0">
                <input
                  type="email"
                  value={alertEmail}
                  onChange={(e) => {
                    setAlertEmail(e.target.value);
                    setAlertEmailError('');
                  }}
                  placeholder="Enter alert email address"
                  className="px-3 py-1.5 text-xs rounded-xl border border-slate-300 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white font-medium w-48 sm:w-56"
                  required
                />
                <button
                  type="submit"
                  disabled={isUpdatingAlertEmail}
                  className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold transition flex items-center space-x-1 shadow-xs"
                >
                  <span>{isUpdatingAlertEmail ? 'Saving...' : 'Save Email'}</span>
                </button>
              </form>
            </div>

            {/* Email feedback messages */}
            {alertEmailMsg && (
              <div className="p-2.5 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
                <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{alertEmailMsg}</span>
              </div>
            )}
            {alertEmailError && (
              <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{alertEmailError}</span>
              </div>
            )}

            {alertsData.alerts.length === 0 ? (
              <div className="py-10 text-center max-w-sm mx-auto space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center mx-auto">
                  <Bell className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-800">No active price drop alerts</h4>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                    Click the Price Alert bell on any product card to track verified price drops without fake notifications.
                  </p>
                </div>
                <button
                  onClick={onNavigateHome}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
                >
                  Explore Products
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {alertsData.alerts.map((alt) => {
                  const isReached = alt.status === 'target_reached';
                  const isUnavailable = alt.status === 'price_unavailable';
                  const isDisabled = alt.status === 'disabled';
                  const isActive = alt.status === 'active';

                  return (
                    <div
                      key={alt.id}
                      className={`rounded-2xl border p-4 transition flex flex-col justify-between space-y-3 ${
                        isReached
                          ? 'bg-emerald-50/60 border-emerald-300 ring-2 ring-emerald-500/20'
                          : isDisabled
                          ? 'bg-slate-50/70 border-slate-200 opacity-70'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="space-y-2">
                        {/* Status Badge & Marketplace */}
                        <div className="flex items-center justify-between">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                            {alt.marketplace}
                          </span>
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide flex items-center space-x-1 ${
                              isReached
                                ? 'bg-emerald-600 text-white'
                                : isUnavailable
                                ? 'bg-amber-100 text-amber-800'
                                : isDisabled
                                ? 'bg-slate-200 text-slate-600'
                                : 'bg-blue-100 text-blue-700'
                            }`}
                          >
                            <span>
                              {isReached ? '🎉 Target Reached' : isUnavailable ? '⚠️ Price Unavailable' : isDisabled ? 'Disabled' : 'Alert Active'}
                            </span>
                          </span>
                        </div>

                        {/* Title */}
                        <h4 className="text-xs font-bold text-slate-900 line-clamp-2 leading-snug" title={alt.product_title}>
                          {alt.product_title}
                        </h4>

                        {/* Price Details Comparison */}
                        <div className="p-3 bg-slate-50 rounded-xl space-y-1.5 text-xs">
                          <div className="flex items-center justify-between text-slate-600">
                            <span>Current Verified Price:</span>
                            <span className="font-extrabold text-slate-900">
                              ₹{alt.current_price.toLocaleString('en-IN')}
                            </span>
                          </div>
                          <div className="flex items-center justify-between text-slate-600">
                            <span>Target Price:</span>
                            <span className="font-bold text-indigo-700">
                              ₹{alt.target_price.toLocaleString('en-IN')}
                            </span>
                          </div>
                          <div className="flex items-center justify-between border-t border-slate-200 pt-1 text-[11px]">
                            <span className="text-slate-500">Difference:</span>
                            <span className={`font-bold ${alt.price_difference <= 0 ? 'text-emerald-700' : 'text-slate-700'}`}>
                              {alt.price_difference <= 0
                                ? `₹${Math.abs(alt.price_difference).toLocaleString('en-IN')} below target!`
                                : `₹${alt.price_difference.toLocaleString('en-IN')} drop needed (${alt.percentage_drop_needed}%)`}
                            </span>
                          </div>
                        </div>

                        {/* Email Notification Status Badge */}
                        <div className="p-2.5 bg-slate-50/80 rounded-xl border border-slate-100 space-y-1 text-xs">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-slate-500 font-medium flex items-center space-x-1">
                              <Mail className="w-3 h-3 text-slate-400" />
                              <span>Email Notification:</span>
                            </span>
                            {!alt.email_notify ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-600">
                                Email Off
                              </span>
                            ) : alt.email_status === 'sent' ? (
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-black bg-emerald-100 text-emerald-800 border border-emerald-200">
                                <Check className="w-3 h-3 text-emerald-600" />
                                <span>Email Sent</span>
                              </span>
                            ) : alt.email_status === 'failed' ? (
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-black bg-rose-100 text-rose-800 border border-rose-200">
                                <AlertCircle className="w-3 h-3 text-rose-600" />
                                <span>Email Delivery Failed</span>
                              </span>
                            ) : alt.email_status === 'not_configured' ? (
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                                <span>Email Not Configured</span>
                              </span>
                            ) : alt.email_status === 'disabled' ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-600">
                                Disabled
                              </span>
                            ) : (
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                                <span>Waiting for Drop</span>
                              </span>
                            )}
                          </div>

                          {alt.user_email_masked && (
                            <div className="flex items-center justify-between text-[10px] text-slate-400 pt-0.5">
                              <span>Recipient:</span>
                              <span className="font-mono text-slate-600 font-medium">{alt.user_email_masked}</span>
                            </div>
                          )}

                          {alt.email_status === 'failed' && alt.email_error && (
                            <p className="text-[10px] text-rose-700 bg-rose-50 border border-rose-200/60 p-1.5 rounded font-medium mt-1 leading-tight">
                              {alt.email_error}
                            </p>
                          )}
                        </div>

                        {/* Notification message if triggered */}
                        {alt.notification_message && (
                          <p className="text-[11px] text-emerald-800 bg-emerald-100/70 p-2 rounded-lg font-medium">
                            {alt.notification_message}
                          </p>
                        )}
                      </div>

                      {/* Card Footer Actions */}
                      <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                        <div className="flex items-center space-x-1.5">
                          <button
                            onClick={() => handleToggleAlertStatus(alt.id, alt.status)}
                            className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition"
                            title={isDisabled ? 'Enable Alert' : 'Disable Alert'}
                          >
                            {isDisabled ? 'Enable' : 'Disable'}
                          </button>
                          <button
                            onClick={() => handleDeleteAlert(alt.id, alt.product_title)}
                            className="p-1.5 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 transition"
                            title="Delete Price Alert"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        {alt.product_url && (
                          <a
                            href={alt.product_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition flex items-center space-x-1"
                          >
                            <span>Store</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* SECTION 3: RESEARCH HISTORY TABS & FEED */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-sm space-y-6">
          {/* Header & Tabs */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
            <div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <span>Research History Log</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-normal">
                  {filteredHistory.length} events
                </span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Detailed chronological log of your searches, recommended products, comparisons, and reviews
              </p>
            </div>

            {/* Category Filter Pills */}
            <div className="flex items-center flex-wrap gap-1.5 bg-slate-100 p-1 rounded-2xl text-xs font-semibold">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'all' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All ({historyItems.length})
              </button>
              <button
                onClick={() => setActiveTab('search')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'search' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🔍 Searches ({stats.total_searches})
              </button>
              <button
                onClick={() => setActiveTab('recommendation')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'recommendation' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ⭐ Recommendations ({stats.total_recommendations})
              </button>
              <button
                onClick={() => setActiveTab('comparison')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'comparison' ? 'bg-purple-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ⚖️ Comparisons ({stats.total_comparisons})
              </button>
              <button
                onClick={() => setActiveTab('review_analysis')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'review_analysis' ? 'bg-emerald-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                📊 Reviews ({stats.total_reviews_analyzed})
              </button>
              <button
                onClick={() => setActiveTab('coupon')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'coupon' ? 'bg-amber-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🎟️ Offers ({stats.total_coupons_viewed})
              </button>
              <button
                onClick={() => setActiveTab('saved')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'saved' ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                ❤️ Wishlist ({savedProducts.length})
              </button>
              <button
                onClick={() => setActiveTab('alerts')}
                className={`px-3 py-1.5 rounded-xl transition ${
                  activeTab === 'alerts' ? 'bg-amber-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                🔔 Alerts ({alertsData.alerts.length})
              </button>
            </div>
          </div>

          {/* LOADING STATE */}
          {isLoading && (
            <div className="py-16 text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
              <p className="text-xs text-slate-500 font-medium">Loading your research history...</p>
            </div>
          )}

          {/* EMPTY STATE */}
          {!isLoading && filteredHistory.length === 0 && activeTab !== 'saved' && (
            <div className="py-16 text-center max-w-md mx-auto space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
                <Clock className="w-7 h-7" />
              </div>
              <div>
                <h4 className="text-base font-bold text-slate-800">
                  No {activeTab === 'all' ? 'research' : activeTab.replace('_', ' ')} history found
                </h4>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {activeTab === 'search'
                    ? 'Search for any product on TrustRank to see your search queries recorded here.'
                    : activeTab === 'recommendation'
                    ? 'Explore ranked recommendations to log products you have researched.'
                    : activeTab === 'comparison'
                    ? 'Compare top products side-by-side to review previous comparisons.'
                    : activeTab === 'review_analysis'
                    ? 'Analyze customer review sentiment to save review insights here.'
                    : 'Start exploring products on TrustRank to build your research log.'}
                </p>
              </div>
              <button
                onClick={onNavigateHome}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-sm"
              >
                Start Product Research
              </button>
            </div>
          )}

          {/* HISTORY ITEMS TIMELINE / LIST */}
          {!isLoading && filteredHistory.length > 0 && (
            <div className="space-y-3">
              {filteredHistory.map((item) => {
                const isSearch = item.category === 'search';
                const isRec = item.category === 'recommendation';
                const isComp = item.category === 'comparison';
                const isReview = item.category === 'review_analysis';
                const isCoupon = item.category === 'coupon';

                return (
                  <div
                    key={item.id}
                    className="p-4 sm:p-5 rounded-2xl border border-slate-200/90 hover:border-slate-300 bg-white hover:bg-slate-50/50 transition duration-150 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    {/* Left: Category Icon & Details */}
                    <div className="flex items-start space-x-3.5">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-white shadow-xs ${
                          isSearch
                            ? 'bg-indigo-600'
                            : isRec
                            ? 'bg-blue-600'
                            : isComp
                            ? 'bg-purple-600'
                            : isReview
                            ? 'bg-emerald-600'
                            : 'bg-amber-600'
                        }`}
                      >
                        {isSearch && <Search className="w-5 h-5" />}
                        {isRec && <Sparkles className="w-5 h-5" />}
                        {isComp && <Layers className="w-5 h-5" />}
                        {isReview && <MessageSquare className="w-5 h-5" />}
                        {isCoupon && <Tag className="w-5 h-5" />}
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide ${
                              isSearch
                                ? 'bg-indigo-100 text-indigo-700'
                                : isRec
                                ? 'bg-blue-100 text-blue-700'
                                : isComp
                                ? 'bg-purple-100 text-purple-700'
                                : isReview
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-amber-100 text-amber-700'
                            }`}
                          >
                            {item.category.replace('_', ' ')}
                          </span>

                          <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{formatDate(item.created_at)}</span>
                          </span>
                        </div>

                        <h4 className="text-sm font-bold text-slate-900 leading-snug">
                          {item.title}
                        </h4>

                        {/* Metadata snippets */}
                        {isSearch && item.query && (
                          <p className="text-xs text-slate-500">
                            Search Query: <span className="font-semibold text-slate-700">"{item.query}"</span>
                          </p>
                        )}

                        {isRec && item.metadata?.product && (
                          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 pt-0.5">
                            <span className="font-semibold text-slate-800">
                              ₹{Number(item.metadata.product.price || 0).toLocaleString('en-IN')}
                            </span>
                            <span>•</span>
                            <span className="text-slate-500">{item.metadata.product.marketplace}</span>
                            {item.metadata.product.trust_score && (
                              <>
                                <span>•</span>
                                <span className="font-bold text-indigo-600">
                                  TrustScore {Number(item.metadata.product.trust_score).toFixed(1)}/100
                                </span>
                              </>
                            )}
                          </div>
                        )}

                        {isComp && item.metadata?.compared_products && (
                          <p className="text-xs text-slate-500">
                            Compared {item.metadata.compared_products.length} products:{' '}
                            <span className="font-medium text-slate-700">
                              {item.metadata.compared_products.map((cp) => cp.title || cp.product_title).slice(0, 3).join(', ')}
                            </span>
                          </p>
                        )}

                        {isReview && item.metadata && (
                          <p className="text-xs text-slate-500">
                            Customer Sentiment:{' '}
                            <span className="font-semibold text-emerald-600">
                              {item.metadata.sentiment_summary?.positive || 78}% Positive
                            </span>
                            {item.metadata.total_reviews && (
                              <span> ({item.metadata.total_reviews} total reviews analysed)</span>
                            )}
                          </p>
                        )}

                        {isCoupon && item.metadata && (
                          <div className="flex items-center space-x-2 text-xs pt-0.5">
                            {item.metadata.coupon_code && (
                              <span className="font-mono font-bold bg-amber-50 text-amber-800 px-2 py-0.5 rounded border border-amber-200">
                                {item.metadata.coupon_code}
                              </span>
                            )}
                            {item.metadata.discount_amount && (
                              <span className="font-bold text-emerald-700">
                                Save ₹{item.metadata.discount_amount}
                              </span>
                            )}
                            <span className="text-slate-500">• {item.metadata.marketplace || 'Marketplace'}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right: Actions */}
                    <div className="flex items-center space-x-2 self-end md:self-center">
                      {isSearch && onReopenSearch && item.query && (
                        <button
                          onClick={() => onReopenSearch(item.query)}
                          className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition flex items-center space-x-1"
                        >
                          <Search className="w-3.5 h-3.5" />
                          <span>Reopen Search</span>
                        </button>
                      )}

                      {isRec && (
                        <>
                          {onSelectProduct && item.metadata?.product && (
                            <button
                              onClick={() => onSelectProduct(item.metadata.product)}
                              className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition flex items-center space-x-1"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              <span>View</span>
                            </button>
                          )}
                          <button
                            onClick={async () => {
                              if (item.metadata?.product) {
                                await saveProduct(authToken, item.metadata.product);
                                showNotification('Product saved to your bookmarks!');
                                await loadDashboard(false);
                              }
                            }}
                            className="p-1.5 rounded-xl border border-slate-200 hover:bg-rose-50 hover:text-rose-600 text-slate-600 transition"
                            title="Save to bookmarks"
                          >
                            <Bookmark className="w-4 h-4" />
                          </button>
                        </>
                      )}

                      {isComp && onNavigateComparison && (
                        <button
                          onClick={onNavigateComparison}
                          className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition flex items-center space-x-1"
                        >
                          <Layers className="w-3.5 h-3.5" />
                          <span>View Comparison</span>
                        </button>
                      )}

                      {isReview && onNavigateReviewAnalysis && (
                        <button
                          onClick={() => onNavigateReviewAnalysis(item.metadata?.product)}
                          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center space-x-1"
                        >
                          <MessageSquare className="w-3.5 h-3.5" />
                          <span>Open Analysis</span>
                        </button>
                      )}

                      {isCoupon && (
                        <button
                          onClick={() => handleCopyCode(item.id, item.metadata?.coupon_code)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 ${
                            copiedCouponId === item.id
                              ? 'bg-emerald-600 text-white'
                              : 'bg-amber-100 hover:bg-amber-200 text-amber-900'
                          }`}
                        >
                          {copiedCouponId === item.id ? (
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
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* CONFIRM CLEAR HISTORY MODAL */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center">
              <AlertCircle className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-base font-bold text-slate-900">
                Clear Research History?
              </h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Are you sure you want to delete your{' '}
                <strong className="text-slate-800">
                  {clearTargetCategory === 'all' ? 'complete research history' : `${clearTargetCategory} history`}
                </strong>
                ? This action will remove all recorded logs for this account.
              </p>
            </div>

            <div className="flex items-center space-x-3 pt-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-700 text-xs font-bold hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmClearHistory}
                className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold shadow-md shadow-rose-600/20 transition flex items-center justify-center space-x-1"
              >
                <Trash2 className="w-4 h-4" />
                <span>Yes, Clear</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
