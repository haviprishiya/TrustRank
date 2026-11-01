import React, { useState } from 'react';
import { Tag, Check, Copy, ExternalLink, ShieldCheck, Clock, AlertCircle, Flag } from 'lucide-react';
import CouponReportModal from './CouponReportModal';

export default function ProductOffersSection({ product, defaultExpanded = false }) {
  if (!product) return null;

  const [copiedCode, setCopiedCode] = useState(null);
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [reportingCoupon, setReportingCoupon] = useState(null);
  const [reportSuccessToast, setReportSuccessToast] = useState('');

  const currency = product.currency || 'INR';
  const formatMoney = (val) => {
    if (typeof val !== 'number' || !Number.isFinite(val)) return '—';
    return new Intl.NumberFormat(currency === 'INR' ? 'en-IN' : undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 0
    }).format(val);
  };

  // Extract genuine offer details from product data
  const currentPrice = Number(product.current_price ?? product.price);
  const originalPrice = Number(product.original_price);
  const hasValidPricing = Number.isFinite(currentPrice) && currentPrice > 0;
  const hasDiscount = hasValidPricing && Number.isFinite(originalPrice) && originalPrice > currentPrice;
  const discountAmount = hasDiscount ? Math.round(originalPrice - currentPrice) : null;
  const discountPercent = hasDiscount
    ? Math.round(((originalPrice - currentPrice) / originalPrice) * 100)
    : (product.discount_percent || null);

  // Check for genuine coupon codes in features, description or raw_data
  let couponCode = null;
  let expiryDate = null;
  const combinedText = [
    ...(product.features || []),
    product.description || '',
    JSON.stringify(product.raw_data || {})
  ].join(' ');

  const couponMatch = combinedText.match(/\b(?:use|apply|coupon|code|promo|voucher)\s*[:\s-]?\s*([A-Z0-9]{4,15})\b/i);
  if (couponMatch) {
    const candidate = couponMatch[1].toUpperCase();
    if (!['HTTP', 'HTTPS', 'TRUE', 'FALSE', 'INDIA', 'AMAZON', 'FLIPKART', 'MYNTRA', 'NONE'].includes(candidate)) {
      couponCode = candidate;
    }
  }

  const expiryMatch = combinedText.match(/(?:valid\s*(?:till|until|through)|ends\s*(?:on)?|expires\s*(?:on)?)\s*([0-9]{1,2}\s+[A-Za-z]+(?:\s+[0-9]{4})?|[A-Za-z]+\s+[0-9]{1,2})/i);
  if (expiryMatch) {
    expiryDate = `Valid till ${expiryMatch[1].trim()}`;
  }

  // Determine if there is any verified offer available
  const hasVerifiedOffer = hasDiscount || Boolean(couponCode);

  const handleCopy = (code) => {
    if (!code) return;
    navigator.clipboard.writeText(code).then(() => {
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2500);
    });
  };

  return (
    <div className="mt-3 pt-3 border-t border-slate-100">
      {/* Offers Section Header */}
      <div className="flex items-center justify-between mb-2">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center space-x-1.5 text-xs font-bold text-slate-800 hover:text-indigo-600 transition"
        >
          <div className="w-5 h-5 rounded-md bg-amber-50 text-amber-600 flex items-center justify-center">
            <Tag className="w-3 h-3" />
          </div>
          <span>Offers & Discounts</span>
          {hasVerifiedOffer ? (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 font-bold ml-1">
              {discountPercent ? `${discountPercent}% OFF` : 'Offer Active'}
            </span>
          ) : (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-500 font-medium ml-1">
              0 Active
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-700"
        >
          {isExpanded ? 'Hide' : 'View Offers'}
        </button>
      </div>

      {/* Offers Content */}
      {isExpanded && (
        <div className="space-y-2 mt-2 animate-in fade-in duration-200">
          {hasVerifiedOffer ? (
            <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-50/60 via-slate-50 to-indigo-50/40 border border-emerald-200/80 text-xs space-y-2">
              {/* Verified Badge & Marketplace */}
              <div className="flex items-center justify-between text-[11px]">
                <span className="inline-flex items-center space-x-1 font-bold text-emerald-700">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Verified Marketplace Offer</span>
                </span>
                <span className="text-slate-500 font-medium">{product.marketplace || 'Online'}</span>
              </div>

              {/* Price Breakdown */}
              <div className="flex flex-wrap items-baseline gap-2 pt-0.5">
                <span className="text-sm font-black text-slate-900">
                  Effective Price: {formatMoney(currentPrice)}
                </span>
                {hasDiscount && (
                  <>
                    <span className="text-xs text-slate-400 line-through">
                      MRP: {formatMoney(originalPrice)}
                    </span>
                    <span className="text-xs font-bold text-emerald-600">
                      (Save {formatMoney(discountAmount)} · {discountPercent}% off)
                    </span>
                  </>
                )}
              </div>

              {/* Coupon Code Row (if applicable) */}
              {couponCode ? (
                <div className="flex items-center justify-between bg-white px-2.5 py-1.5 rounded-lg border border-dashed border-amber-300">
                  <div className="flex items-center space-x-1.5 min-w-0">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Coupon:</span>
                    <span className="font-mono font-bold text-slate-900 text-xs tracking-wider">{couponCode}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <button
                      type="button"
                      onClick={() => handleCopy(couponCode)}
                      className="flex items-center space-x-1 px-2 py-1 rounded bg-amber-500 hover:bg-amber-600 text-white font-bold text-[10px] transition shadow-xs"
                    >
                      {copiedCode === couponCode ? (
                        <>
                          <Check className="w-3 h-3" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy Code</span>
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => setReportingCoupon({
                        coupon_id: `prod_${product.product_id || product.id || 'offer'}`,
                        coupon_code: couponCode,
                        marketplace: product.marketplace,
                        title: product.title,
                        discount_display: discountPercent ? `${discountPercent}% OFF` : undefined,
                        current_price: currentPrice
                      })}
                      className="flex items-center space-x-0.5 px-1.5 py-1 rounded border border-rose-200 text-rose-600 hover:bg-rose-50 font-bold text-[10px] transition"
                      title="Report coupon issue"
                    >
                      <Flag className="w-2.5 h-2.5" />
                      <span>Report</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-[11px] text-slate-500 bg-white/80 px-2 py-1 rounded border border-slate-100 flex items-center space-x-1">
                  <Check className="w-3 h-3 text-emerald-500 shrink-0" />
                  <span>Direct marketplace markdown — no coupon code required at checkout.</span>
                </div>
              )}

              {/* Expiry & Validity */}
              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                <span className="flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-slate-400" />
                  <span>{expiryDate || 'Limited Period Marketplace Deal'}</span>
                </span>
                <div className="flex items-center space-x-2">
                  {couponCode && (
                    <button
                      type="button"
                      onClick={() => setReportingCoupon({
                        coupon_id: `prod_${product.product_id || product.id || 'offer'}`,
                        coupon_code: couponCode,
                        marketplace: product.marketplace,
                        title: product.title,
                        discount_display: discountPercent ? `${discountPercent}% OFF` : undefined,
                        current_price: currentPrice
                      })}
                      className="text-[10px] text-slate-400 hover:text-rose-600 font-semibold transition flex items-center space-x-0.5"
                    >
                      <Flag className="w-2.5 h-2.5" />
                      <span>Report</span>
                    </button>
                  )}
                  {product.product_url && (
                    <a
                      href={product.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-0.5"
                    >
                      <span>Claim on {product.marketplace}</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ) : (
            /* Requirement 8: If no offer data is available, display "No verified offers currently available." */
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs flex items-center space-x-2 text-slate-500">
              <AlertCircle className="w-4 h-4 text-slate-400 shrink-0" />
              <div>
                <span className="font-medium text-slate-700 block text-[11px]">No verified offers currently available.</span>
                <span className="text-[10px] text-slate-400">This product is listed at standard marketplace retail rates without active promotional coupons.</span>
              </div>
            </div>
          )}
        </div>
      )}

      {reportSuccessToast && (
        <div className="mt-2 p-2 bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] rounded-lg flex items-center space-x-1 font-medium">
          <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>{reportSuccessToast}</span>
        </div>
      )}

      {reportingCoupon && (
        <CouponReportModal
          coupon={reportingCoupon}
          onClose={() => setReportingCoupon(null)}
          onSuccess={(msg) => {
            setReportSuccessToast(msg);
            setTimeout(() => setReportSuccessToast(''), 4000);
          }}
        />
      )}
    </div>
  );
}
