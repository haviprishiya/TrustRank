import React, { useState } from 'react';
import { Flag, X, Check, AlertCircle, Tag, ShieldAlert } from 'lucide-react';
import { submitCouponReport } from '../services/api';

const REPORT_REASONS = [
  'Coupon code is not working.',
  'Coupon has expired.',
  'Incorrect discount amount.',
  'Invalid coupon code.',
  'Misleading offer.',
  'Other.'
];

export default function CouponReportModal({
  isOpen,
  onClose,
  coupon,
  onReportSubmitted
}) {
  if (!isOpen || !coupon) return null;

  const [selectedReason, setSelectedReason] = useState(REPORT_REASONS[0]);
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedReason) {
      setErrorMsg('Please select a reason for reporting.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg('');
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('trustrank_auth_token') : null;
      const payload = {
        coupon_id: String(coupon.id),
        coupon_code: coupon.coupon_code || null,
        marketplace: coupon.marketplace || 'Amazon India',
        item_title: coupon.applicable_product || coupon.title || 'Marketplace Offer',
        reason: selectedReason,
        description: description.trim() || null,
        product_url: coupon.product_url || null
      };

      const result = await submitCouponReport(token, payload);
      setSuccessMsg('Report submitted successfully! Our moderation team will investigate this coupon.');
      if (onReportSubmitted) {
        onReportSubmitted(result);
      }
      setTimeout(() => {
        onClose();
        setSuccessMsg('');
        setDescription('');
      }, 1800);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="relative bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-5 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold shadow-xs">
              <Flag className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 leading-tight">
                Report Coupon or Offer
              </h3>
              <p className="text-xs text-slate-500">
                Help us keep discounts authentic and verified
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

        {/* Coupon Snippet Preview */}
        <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1.5 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold px-2 py-0.5 rounded text-[10px] bg-slate-200 text-slate-700">
              {coupon.marketplace}
            </span>
            {coupon.coupon_code && (
              <span className="font-mono font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 text-[11px]">
                CODE: {coupon.coupon_code}
              </span>
            )}
          </div>
          <h4 className="font-bold text-slate-900 truncate" title={coupon.title}>
            {coupon.title}
          </h4>
          <p className="text-slate-500 truncate">
            {coupon.applicable_product}
          </p>
        </div>

        {/* Success Alert */}
        {successMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
            <Check className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Report Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2">
              Why are you reporting this coupon?
            </label>
            <div className="space-y-2">
              {REPORT_REASONS.map((reason) => (
                <label
                  key={reason}
                  className={`flex items-center space-x-3 p-2.5 rounded-xl border text-xs cursor-pointer transition ${
                    selectedReason === reason
                      ? 'border-indigo-500 bg-indigo-50/50 text-slate-900 font-semibold'
                      : 'border-slate-200 hover:border-slate-300 text-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="report_reason"
                    value={reason}
                    checked={selectedReason === reason}
                    onChange={() => {
                      setSelectedReason(reason);
                      setErrorMsg('');
                    }}
                    className="text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                  />
                  <span>{reason}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold text-slate-700">
                Additional Details (Optional)
              </label>
              <span className="text-[10px] text-slate-400">
                {description.length}/1000
              </span>
            </div>
            <textarea
              rows={3}
              maxLength={1000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Code returned an error at checkout, or the price was different than advertised..."
              className="w-full p-3 rounded-xl border border-slate-300 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none font-medium"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-bold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !!successMsg}
              className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-rose-600/20 transition flex items-center justify-center space-x-1.5"
            >
              <Flag className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Submitting...' : 'Submit Report'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
