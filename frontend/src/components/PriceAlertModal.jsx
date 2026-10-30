import React, { useState, useId } from 'react';
import { Bell, Check, AlertCircle, X, ShieldCheck, ArrowDown, Mail, ExternalLink } from 'lucide-react';
import { createPriceAlert } from '../services/api';

export default function PriceAlertModal({
  product,
  isOpen,
  onClose,
  onAlertCreated
}) {
  if (!isOpen || !product) return null;

  const currentPrice = Number(product.current_price ?? product.price ?? 0);
  const currency = product.currency || 'INR';

  // Default target price to 10% below current price if available
  const defaultTarget = currentPrice > 0 ? Math.round(currentPrice * 0.90) : '';
  const [targetPrice, setTargetPrice] = useState(defaultTarget);
  const [emailNotify, setEmailNotify] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const numTarget = Number(targetPrice);
  const isValid = Number.isFinite(numTarget) && numTarget > 0 && numTarget < currentPrice;
  const difference = currentPrice > 0 && isValid ? Math.round(currentPrice - numTarget) : 0;
  const percentageDrop = currentPrice > 0 && isValid ? Math.round((difference / currentPrice) * 100) : 0;

  const handlePreset = (pct) => {
    if (currentPrice > 0) {
      const calc = Math.round(currentPrice * (1 - pct / 100));
      setTargetPrice(calc);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) {
      if (numTarget <= 0) {
        setError('Please enter a target price greater than ₹0.');
      } else if (numTarget >= currentPrice) {
        setError(`Target price must be lower than the current verified price (₹${currentPrice.toLocaleString('en-IN')}).`);
      }
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('trustrank_auth_token') : null;
      const payload = {
        product_id: String(product.id || product.product_id),
        product_title: product.title,
        marketplace: product.marketplace || 'Amazon India',
        current_price: currentPrice,
        target_price: numTarget,
        currency: currency,
        image_url: product.image_url || (product.image_candidates ? product.image_candidates[0] : null),
        product_url: product.product_url || null,
        email_notify: emailNotify
      };

      const result = await createPriceAlert(token, payload);
      setSuccessMsg(`Price alert activated! We'll notify you when the verified price drops to ₹${numTarget.toLocaleString('en-IN')}.`);
      if (onAlertCreated) onAlertCreated(result);
      setTimeout(() => {
        onClose();
        setSuccessMsg('');
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to set price alert. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-5 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold shadow-xs">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 leading-tight">
                Set Price Drop Alert
              </h3>
              <p className="text-xs text-slate-500">
                Periodic marketplace check with zero fake alerts
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-full hover:bg-slate-100 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Product Snippet */}
        <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 flex items-center space-x-3">
          {(product.image_url || product.image_candidates?.[0]) ? (
            <img
              src={product.image_url || product.image_candidates?.[0]}
              alt={product.title}
              className="w-12 h-12 object-contain bg-white rounded-xl p-1 border border-slate-200"
            />
          ) : (
            <div className="w-12 h-12 rounded-xl bg-slate-200 flex items-center justify-center text-slate-500 font-bold text-xs">
              TR
            </div>
          )}
          <div className="min-w-0 flex-1">
            <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
              {product.marketplace || 'Amazon India'}
            </span>
            <h4 className="text-xs font-bold text-slate-800 truncate mt-1" title={product.title}>
              {product.title}
            </h4>
            <p className="text-xs font-extrabold text-slate-900 mt-0.5">
              Current Verified Price: ₹{currentPrice.toLocaleString('en-IN')}
            </p>
          </div>
        </div>

        {/* Success Alert */}
        {successMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
            <Check className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Target Price Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Your Target Price (₹ INR)
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">
                ₹
              </span>
              <input
                type="number"
                min="1"
                step="1"
                value={targetPrice}
                onChange={(e) => {
                  setTargetPrice(e.target.value);
                  setError('');
                }}
                placeholder="Enter target price"
                className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
          </div>

          {/* Quick Drop Presets */}
          {currentPrice > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 block">Quick Presets:</span>
              <div className="flex items-center space-x-2">
                {[5, 10, 15, 20].map((pct) => (
                  <button
                    key={pct}
                    type="button"
                    onClick={() => handlePreset(pct)}
                    className="flex-1 py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-indigo-50 hover:border-indigo-200 text-slate-700 hover:text-indigo-700 text-xs font-bold transition"
                  >
                    -{pct}%
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Calculation Summary Card */}
          {isValid && (
            <div className="p-3 bg-indigo-50/60 border border-indigo-100 rounded-xl space-y-1.5 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span>Current Price:</span>
                <span className="font-semibold">₹{currentPrice.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex items-center justify-between text-slate-600">
                <span>Target Price:</span>
                <span className="font-bold text-indigo-700">₹{numTarget.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex items-center justify-between border-t border-indigo-100 pt-1 font-bold text-emerald-700">
                <span className="flex items-center space-x-1">
                  <ArrowDown className="w-3.5 h-3.5" />
                  <span>Required Drop:</span>
                </span>
                <span>₹{difference.toLocaleString('en-IN')} ({percentageDrop}% drop)</span>
              </div>
            </div>
          )}

          {/* Email Notify Toggle */}
          <label className="flex items-center space-x-2.5 text-xs text-slate-600 cursor-pointer pt-1">
            <input
              type="checkbox"
              checked={emailNotify}
              onChange={(e) => setEmailNotify(e.target.checked)}
              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 w-4 h-4"
            />
            <span className="flex items-center space-x-1 font-medium">
              <Mail className="w-3.5 h-3.5 text-slate-400" />
              <span>Send email notification when verified price drops</span>
            </span>
          </label>

          {/* Form Actions */}
          <div className="flex items-center space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-bold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !isValid}
              className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition flex items-center justify-center space-x-1.5"
            >
              <Bell className="w-4 h-4" />
              <span>{isLoading ? 'Activating...' : 'Activate Price Alert'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
