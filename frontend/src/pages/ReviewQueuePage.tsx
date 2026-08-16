import React, { useState } from 'react';
import { ReviewItem, Opportunity } from '../types';
import { ScoreIndicator } from '../components/common/ScoreIndicator';
import { DecisionBadge } from '../components/common/DecisionBadge';
import { ScoreBreakdownBars } from '../components/common/ScoreBreakdownBars';
import {
  Inbox,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RotateCcw,
  ArrowRight,
  UserCheck,
  Clock,
  ShieldAlert,
  FileText,
  X,
  History,
  Send,
  Sparkles,
} from 'lucide-react';

interface ReviewQueuePageProps {
  reviews: ReviewItem[];
  opportunities: Opportunity[];
  onResolveReview: (
    reviewId: string,
    action: 'APPROVE' | 'REJECT' | 'SEND_BACK',
    overrideReason: string
  ) => void;
  onSelectOpportunity: (id: string) => void;
}

export const ReviewQueuePage: React.FC<ReviewQueuePageProps> = ({
  reviews,
  opportunities,
  onResolveReview,
  onSelectOpportunity,
}) => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'GATEKEEPER' | 'OPPORTUNITY_ANALYSIS'>('ALL');
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(
    reviews.length > 0 ? reviews[0].id : null
  );

  const [overrideReasonInput, setOverrideReasonInput] = useState('');
  const [actionError, setActionError] = useState('');

  const filteredReviews = reviews.filter((r) => {
    if (activeTab === 'GATEKEEPER') return r.reviewType === 'GATEKEEPER';
    if (activeTab === 'OPPORTUNITY_ANALYSIS') return r.reviewType === 'OPPORTUNITY_ANALYSIS';
    return true;
  });

  const currentReview = reviews.find((r) => r.id === selectedReviewId) || null;
  const currentOpp = currentReview
    ? opportunities.find((o) => o.id === currentReview.opportunityId) || null
    : null;

  const handleAction = (action: 'APPROVE' | 'REJECT' | 'SEND_BACK') => {
    if (!overrideReasonInput.trim()) {
      setActionError('A manual justification reason is required for audit logs.');
      return;
    }
    setActionError('');
    if (currentReview) {
      onResolveReview(currentReview.id, action, overrideReasonInput);
      setOverrideReasonInput('');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Human In The Loop Review Queue
            </h2>
            <span className="text-xs bg-amber-100 text-amber-900 border border-amber-300 font-mono font-bold px-2 py-0.5 rounded">
              {reviews.filter((r) => r.status === 'OPEN').length} Open Items
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Manual override governance for tenders flagged by AI Gatekeeper or with confidence below threshold.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center bg-slate-100 p-1 rounded-md border border-slate-200 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('ALL')}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === 'ALL' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Reviews
          </button>
          <button
            onClick={() => setActiveTab('GATEKEEPER')}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === 'GATEKEEPER' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Gatekeeper Flagged
          </button>
          <button
            onClick={() => setActiveTab('OPPORTUNITY_ANALYSIS')}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === 'OPPORTUNITY_ANALYSIS' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Low Confidence Analysis
          </button>
        </div>
      </div>

      {/* Main Review Queue Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-3 px-3">Opportunity</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">AI Decision</th>
                <th className="py-3 px-3">Score</th>
                <th className="py-3 px-3">Priority</th>
                <th className="py-3 px-3">Assignee</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredReviews.map((r) => {
                const isSelected = r.id === selectedReviewId;
                return (
                  <tr
                    key={r.id}
                    onClick={() => setSelectedReviewId(r.id)}
                    className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                      isSelected ? 'bg-emerald-50/50 border-l-4 border-l-[#86BC25]' : ''
                    }`}
                  >
                    <td className="py-3 px-3 max-w-[260px]">
                      <div className="font-bold text-slate-900 truncate">{r.opportunityTitle}</div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {r.country} • {r.source}
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] uppercase font-semibold text-slate-600">
                      {r.reviewType.replace('_', ' ')}
                    </td>
                    <td className="py-3 px-3">
                      <DecisionBadge decision={r.aiDecision} size="sm" />
                    </td>
                    <td className="py-3 px-3">
                      <ScoreIndicator score={r.score} size="sm" />
                    </td>
                    <td className="py-3 px-3 font-mono">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.priority === 'HIGH'
                            ? 'bg-red-100 text-red-800'
                            : r.priority === 'MEDIUM'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {r.priority}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-700">
                      {r.assignee || <span className="text-slate-400 italic">Unassigned</span>}
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-[11px]">
                      {r.status === 'OPEN' ? (
                        <span className="text-amber-600 flex items-center gap-1">
                          ● Open
                        </span>
                      ) : (
                        <span className="text-emerald-700 flex items-center gap-1">
                          ✓ Resolved
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => setSelectedReviewId(r.id)}
                        className="px-2.5 py-1 text-xs font-bold text-white bg-slate-900 hover:bg-[#007629] rounded"
                      >
                        Review Workspace
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3-Pane Interactive Review Workspace Drawer/Panel */}
      {currentReview && (
        <div className="bg-white rounded-lg border-2 border-slate-300 shadow-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold bg-slate-900 text-white px-2 py-0.5 rounded">
                  {currentReview.id}
                </span>
                <span className="text-xs font-semibold text-slate-500">
                  Created: {currentReview.createdAt}
                </span>
              </div>
              <h3 className="text-lg font-extrabold text-slate-900 mt-1">
                Review Workspace: {currentReview.opportunityTitle}
              </h3>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-500 block font-mono">Current Status</span>
              <span className="text-sm font-extrabold text-slate-900 font-mono">
                {currentReview.status}
              </span>
            </div>
          </div>

          {/* 3-PANE GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* PANE 1 (LEFT): Tender Information */}
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-3">
              <div className="flex items-center gap-1.5 font-bold text-xs uppercase text-slate-700 tracking-wider">
                <FileText className="w-4 h-4 text-slate-600" />
                <span>1. Original Tender Metadata</span>
              </div>

              {currentOpp ? (
                <div className="space-y-2 text-xs text-slate-800 font-sans">
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">Title & ID</span>
                    <strong className="text-slate-900">{currentOpp.title}</strong>
                    <div className="font-mono text-[10px] text-slate-500">{currentOpp.externalId}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">Source & Country</span>
                    <p className="font-medium">{currentOpp.source} • {currentOpp.country}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">Estimated Value</span>
                    <p className="font-mono font-bold text-slate-900">{currentOpp.estimatedValue}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">Description Excerpt</span>
                    <p className="text-slate-700 bg-white p-2.5 rounded border border-slate-200 text-[11px] leading-relaxed line-clamp-4">
                      {currentOpp.description}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500">Tender information loaded.</p>
              )}
            </div>

            {/* PANE 2 (CENTER): AI Analysis & Reasoning */}
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-3">
              <div className="flex items-center gap-1.5 font-bold text-xs uppercase text-slate-700 tracking-wider">
                <Sparkles className="w-4 h-4 text-[#86BC25]" />
                <span>2. AI Evaluation & Reasoning</span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between bg-white p-2.5 rounded border border-slate-200">
                  <div>
                    <span className="text-slate-400 text-[10px] block font-mono">AI Assigned Decision</span>
                    <DecisionBadge decision={currentReview.aiDecision} />
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 text-[10px] block font-mono">Fit Score</span>
                    <ScoreIndicator score={currentReview.score} size="sm" showLabel />
                  </div>
                </div>

                <div className="bg-amber-50 p-2.5 rounded border border-amber-200 text-amber-900 text-xs space-y-1">
                  <span className="font-bold text-[11px] flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Flag Reason
                  </span>
                  <p className="text-slate-800 text-[11px] leading-relaxed">
                    {currentReview.reason}
                  </p>
                </div>

                {currentOpp && (
                  <div className="bg-white p-2.5 rounded border border-slate-200">
                    <span className="text-slate-500 text-[10px] font-mono block mb-2">
                      Multidimensional Breakdown
                    </span>
                    <ScoreBreakdownBars scoreBreakdown={currentOpp.scoreBreakdown} compact />
                  </div>
                )}
              </div>
            </div>

            {/* PANE 3 (RIGHT): Human Decision Form */}
            <div className="bg-white rounded-lg p-4 border-2 border-slate-900 space-y-3 shadow-xs">
              <div className="flex items-center gap-1.5 font-bold text-xs uppercase text-slate-900 tracking-wider">
                <UserCheck className="w-4 h-4 text-[#007629]" />
                <span>3. Human Decision Override</span>
              </div>

              {currentReview.status !== 'OPEN' ? (
                <div className="p-3 bg-emerald-50 rounded border border-emerald-200 text-emerald-900 text-xs space-y-2">
                  <div className="font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Resolved: {currentReview.status}
                  </div>
                  <p className="text-slate-700 text-[11px]">
                    Resolved at <strong>{currentReview.resolvedAt}</strong> by <strong>{currentReview.resolvedBy}</strong>.
                  </p>
                  {currentReview.overrideReason && (
                    <div className="bg-white p-2 rounded border border-emerald-200 font-mono text-[11px]">
                      "{currentReview.overrideReason}"
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-slate-600">
                    Review the AI analysis and select an authoritative manual resolution for this tender opportunity.
                  </p>

                  <div>
                    <label className="block text-xs font-bold text-slate-800 mb-1">
                      Override Justification Reason <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Explain why you are approving, rejecting, or returning this item..."
                      value={overrideReasonInput}
                      onChange={(e) => {
                        setOverrideReasonInput(e.target.value);
                        setActionError('');
                      }}
                      className="w-full text-xs p-2.5 bg-slate-50 border border-slate-300 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
                    />
                    {actionError && (
                      <p className="text-[11px] font-semibold text-red-600 mt-1">{actionError}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    <button
                      onClick={() => handleAction('APPROVE')}
                      className="py-2 px-2 bg-[#007629] hover:bg-emerald-700 text-white font-bold text-xs rounded-md shadow-xs flex flex-col items-center justify-center gap-0.5"
                    >
                      <CheckCircle2 className="w-4 h-4 text-[#86BC25]" />
                      <span>Approve</span>
                    </button>

                    <button
                      onClick={() => handleAction('REJECT')}
                      className="py-2 px-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-md shadow-xs flex flex-col items-center justify-center gap-0.5"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject</span>
                    </button>

                    <button
                      onClick={() => handleAction('SEND_BACK')}
                      className="py-2 px-2 bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs rounded-md shadow-xs flex flex-col items-center justify-center gap-0.5"
                    >
                      <RotateCcw className="w-4 h-4 text-amber-400" />
                      <span>Keep/Return</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Audit History Log */}
              <div className="pt-3 border-t border-slate-200">
                <span className="text-[10px] uppercase font-bold text-slate-400 font-mono block mb-1">
                  Audit History Log
                </span>
                <div className="space-y-1.5 max-h-32 overflow-y-auto">
                  {currentReview.auditTrail.map((log, idx) => (
                    <div key={idx} className="text-[10px] font-mono bg-slate-50 p-1.5 rounded border border-slate-200">
                      <div className="flex items-center justify-between text-slate-500">
                        <span>{log.actor}</span>
                        <span>{log.timestamp}</span>
                      </div>
                      <div className="font-bold text-slate-800">{log.action}</div>
                      {log.notes && <div className="text-slate-600">{log.notes}</div>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
