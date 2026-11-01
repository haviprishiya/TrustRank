import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Flag,
  Check,
  AlertCircle,
  Clock,
  ExternalLink,
  Ban,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  FileText
} from 'lucide-react';
import { fetchAdminReports, updateAdminReportStatus } from '../services/api';

export default function AdminReportManagement({ authToken, onClose }) {
  const [reportsData, setReportsData] = useState({
    total_reports: 0,
    pending_count: 0,
    reviewed_count: 0,
    resolved_count: 0,
    rejected_count: 0,
    reports: []
  });
  const [activeStatusFilter, setActiveStatusFilter] = useState('all'); // 'all' | 'Pending' | 'Reviewed' | 'Resolved' | 'Rejected'
  const [activeTypeFilter, setActiveTypeFilter] = useState('all'); // 'all' | 'coupon' | 'product'
  const [isLoading, setIsLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [updatingId, setUpdatingId] = useState(null);
  const [adminNotesInput, setAdminNotesInput] = useState({});

  const loadReports = async () => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const data = await fetchAdminReports(authToken, {
        status: activeStatusFilter,
        report_type: activeTypeFilter,
        limit: 100
      });
      setReportsData(data);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load report data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [authToken, activeStatusFilter, activeTypeFilter]);

  const handleStatusChange = async (reportId, nextStatus, disableCoupon = false) => {
    setUpdatingId(reportId);
    setActionMsg('');
    setErrorMsg('');
    try {
      const note = adminNotesInput[reportId] || undefined;
      const res = await updateAdminReportStatus(authToken, reportId, {
        status: nextStatus,
        admin_notes: note,
        disable_coupon: disableCoupon
      });
      setActionMsg(
        disableCoupon
          ? `Report marked as ${nextStatus} and coupon has been permanently disabled.`
          : `Report status updated to ${nextStatus}.`
      );
      setTimeout(() => setActionMsg(''), 4000);
      await loadReports();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to update report status.');
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold shadow-xs">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-extrabold text-slate-900 text-base sm:text-lg">
                Report & Moderation Management
              </h3>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700">
                {reportsData.total_reports} Total
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Review user reported coupons, invalid promo codes, and investigate marketplace discrepancies.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={loadReports}
            disabled={isLoading}
            className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold transition flex items-center space-x-1.5"
            title="Refresh reports"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          onClick={() => setActiveStatusFilter('Pending')}
          className={`p-3.5 rounded-2xl border cursor-pointer transition ${
            activeStatusFilter === 'Pending'
              ? 'bg-amber-50 border-amber-300 ring-2 ring-amber-500/20'
              : 'bg-slate-50 border-slate-200 hover:border-slate-300'
          }`}
        >
          <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider block">Pending</span>
          <span className="text-xl font-extrabold text-slate-900 mt-1 block">{reportsData.pending_count}</span>
        </div>
        <div
          onClick={() => setActiveStatusFilter('Reviewed')}
          className={`p-3.5 rounded-2xl border cursor-pointer transition ${
            activeStatusFilter === 'Reviewed'
              ? 'bg-blue-50 border-blue-300 ring-2 ring-blue-500/20'
              : 'bg-slate-50 border-slate-200 hover:border-slate-300'
          }`}
        >
          <span className="text-[11px] font-bold text-blue-800 uppercase tracking-wider block">Reviewed</span>
          <span className="text-xl font-extrabold text-slate-900 mt-1 block">{reportsData.reviewed_count}</span>
        </div>
        <div
          onClick={() => setActiveStatusFilter('Resolved')}
          className={`p-3.5 rounded-2xl border cursor-pointer transition ${
            activeStatusFilter === 'Resolved'
              ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-500/20'
              : 'bg-slate-50 border-slate-200 hover:border-slate-300'
          }`}
        >
          <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider block">Resolved</span>
          <span className="text-xl font-extrabold text-slate-900 mt-1 block">{reportsData.resolved_count}</span>
        </div>
        <div
          onClick={() => setActiveStatusFilter('Rejected')}
          className={`p-3.5 rounded-2xl border cursor-pointer transition ${
            activeStatusFilter === 'Rejected'
              ? 'bg-rose-50 border-rose-300 ring-2 ring-rose-500/20'
              : 'bg-slate-50 border-slate-200 hover:border-slate-300'
          }`}
        >
          <span className="text-[11px] font-bold text-rose-800 uppercase tracking-wider block">Rejected</span>
          <span className="text-xl font-extrabold text-slate-900 mt-1 block">{reportsData.rejected_count}</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3 text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-slate-400 font-semibold">Status:</span>
          {['all', 'Pending', 'Reviewed', 'Resolved', 'Rejected'].map((st) => (
            <button
              key={st}
              onClick={() => setActiveStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg font-bold transition capitalize ${
                activeStatusFilter === st
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-slate-400 font-semibold">Type:</span>
          {['all', 'coupon', 'product'].map((tp) => (
            <button
              key={tp}
              onClick={() => setActiveTypeFilter(tp)}
              className={`px-2.5 py-1 rounded-lg font-bold transition capitalize ${
                activeTypeFilter === tp
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tp}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts / Feedback */}
      {actionMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center space-x-2 font-medium">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Reports List */}
      {isLoading ? (
        <div className="py-12 text-center text-xs text-slate-500">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <span>Loading submitted reports...</span>
        </div>
      ) : reportsData.reports.length === 0 ? (
        <div className="py-12 text-center max-w-sm mx-auto space-y-2">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
          <h4 className="text-sm font-bold text-slate-800">No reports found</h4>
          <p className="text-xs text-slate-500">
            There are no reported items matching the selected filters.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {reportsData.reports.map((rep) => {
            const isPending = rep.status === 'Pending';
            const isReviewed = rep.status === 'Reviewed';
            const isResolved = rep.status === 'Resolved';
            const isRejected = rep.status === 'Rejected';
            const isCouponDisabled = rep.action_taken === 'coupon_disabled';

            return (
              <div
                key={rep.id}
                className={`rounded-2xl border p-5 transition space-y-3 ${
                  isPending
                    ? 'bg-amber-50/40 border-amber-200'
                    : isResolved
                    ? 'bg-emerald-50/30 border-emerald-200'
                    : 'bg-white border-slate-200'
                }`}
              >
                {/* Top Row: Marketplace, Coupon Code, Reason, and Status */}
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700">
                      {rep.marketplace}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-200/60">
                      {rep.reason}
                    </span>
                    {rep.coupon_code && (
                      <span className="font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 text-[10px]">
                        CODE: {rep.coupon_code}
                      </span>
                    )}
                    {isCouponDisabled && (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-black bg-rose-600 text-white">
                        <Ban className="w-3 h-3" />
                        <span>Coupon Disabled</span>
                      </span>
                    )}
                  </div>

                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wide ${
                      isPending
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : isReviewed
                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                        : isResolved
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {rep.status}
                  </span>
                </div>

                {/* Target Title & Details */}
                <div>
                  <h4 className="text-xs font-bold text-slate-900 leading-snug">
                    {rep.item_title || rep.target_id}
                  </h4>
                  {rep.description && (
                    <div className="mt-1.5 p-2.5 bg-white rounded-xl border border-slate-200/80 text-xs text-slate-700">
                      <span className="font-semibold text-slate-500 text-[10px] uppercase block mb-0.5">User Explanation:</span>
                      <p>{rep.description}</p>
                    </div>
                  )}
                  {rep.admin_notes && (
                    <div className="mt-1.5 p-2 bg-indigo-50/70 rounded-xl border border-indigo-100 text-xs text-indigo-900">
                      <span className="font-semibold text-indigo-600 text-[10px] uppercase block">Admin Note:</span>
                      <p>{rep.admin_notes}</p>
                    </div>
                  )}
                </div>

                {/* Submitter & Date Footer */}
                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 pt-2 border-t border-slate-100">
                  <div className="flex items-center space-x-2">
                    <span>Submitted by: <strong className="text-slate-600">{rep.user_id || 'Guest'}</strong></span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(rep.created_at).toLocaleString()}</span>
                    </span>
                  </div>

                  {/* Actions Bar */}
                  <div className="flex items-center space-x-2">
                    <button
                      disabled={updatingId === rep.id || rep.status === 'Reviewed'}
                      onClick={() => handleStatusChange(rep.id, 'Reviewed')}
                      className="px-2.5 py-1 rounded-lg border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-[10px] transition disabled:opacity-40"
                    >
                      Mark Reviewed
                    </button>
                    <button
                      disabled={updatingId === rep.id || rep.status === 'Resolved'}
                      onClick={() => handleStatusChange(rep.id, 'Resolved')}
                      className="px-2.5 py-1 rounded-lg border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-[10px] transition disabled:opacity-40"
                    >
                      Resolve
                    </button>
                    <button
                      disabled={updatingId === rep.id || rep.status === 'Rejected'}
                      onClick={() => handleStatusChange(rep.id, 'Rejected')}
                      className="px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-600 font-bold text-[10px] transition disabled:opacity-40"
                    >
                      Reject
                    </button>
                    {rep.report_type === 'coupon' && !isCouponDisabled && (
                      <button
                        disabled={updatingId === rep.id}
                        onClick={() => handleStatusChange(rep.id, 'Resolved', true)}
                        className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-bold text-[10px] transition flex items-center space-x-1 shadow-xs disabled:opacity-40"
                        title="Deactivate this coupon so it no longer appears in offers"
                      >
                        <Ban className="w-3 h-3" />
                        <span>Disable Coupon</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
