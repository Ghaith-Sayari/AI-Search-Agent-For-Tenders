import React from 'react';
import { Opportunity } from '../../types';
import { ScoreIndicator } from '../common/ScoreIndicator';
import { DecisionBadge } from '../common/DecisionBadge';
import { Globe, Building2, Calendar, DollarSign, Eye, AlertOctagon, FileSearch } from 'lucide-react';

interface TenderSummaryProps {
  opportunity: Opportunity;
  onViewOpportunity?: () => void;
  onViewAnalysis?: () => void;
  compact?: boolean;
}

export const TenderSummary: React.FC<TenderSummaryProps> = ({
  opportunity,
  onViewOpportunity,
  onViewAnalysis,
  compact = false,
}) => {
  const isNotFit = opportunity.decision === 'NOT_FIT' || opportunity.decision === 'FAILED';

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4 relative overflow-hidden">
      {/* Deloitte Green Accent Bar */}
      <div
        className={`absolute top-0 left-0 bottom-0 w-1.5 ${
          isNotFit ? 'bg-red-500' : 'bg-[#86BC25]'
        }`}
      />

      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
            {opportunity.externalId}
          </span>
          <DecisionBadge decision={opportunity.decision} />
        </div>

        <div className="flex items-center gap-2">
          {onViewOpportunity && (
            <button
              onClick={onViewOpportunity}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded border border-slate-300 transition-colors"
            >
              <Eye className="w-3.5 h-3.5 text-slate-500" />
              <span>View Opportunity</span>
            </button>
          )}

          {onViewAnalysis && (
            <button
              onClick={onViewAnalysis}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded border border-slate-300 transition-colors"
            >
              <FileSearch className="w-3.5 h-3.5 text-slate-500" />
              <span>View Analysis</span>
            </button>
          )}
        </div>
      </div>

      {/* Title & Metadata */}
      <div className="space-y-2">
        <h2 className="text-base font-extrabold text-slate-900 leading-snug tracking-tight">
          {opportunity.title}
        </h2>

        <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
          {opportunity.description}
        </p>
      </div>

      {/* Metadata Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 border-t border-slate-100 text-xs font-mono">
        <div className="bg-[#F5F6F7] p-2.5 rounded border border-slate-200/60">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold">Country</span>
          <div className="flex items-center gap-1 mt-0.5 font-bold text-slate-800">
            <Globe className="w-3.5 h-3.5 text-slate-500" />
            <span>{opportunity.country}</span>
          </div>
        </div>

        <div className="bg-[#F5F6F7] p-2.5 rounded border border-slate-200/60">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold">Source</span>
          <div className="flex items-center gap-1 mt-0.5 font-bold text-slate-800 truncate">
            <Building2 className="w-3.5 h-3.5 text-slate-500" />
            <span className="truncate">{opportunity.source}</span>
          </div>
        </div>

        <div className="bg-[#F5F6F7] p-2.5 rounded border border-slate-200/60">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold">Deadline</span>
          <div className="flex items-center gap-1 mt-0.5 font-bold text-slate-800">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>{opportunity.deadline}</span>
          </div>
        </div>

        <div className="bg-[#F5F6F7] p-2.5 rounded border border-slate-200/60">
          <span className="text-[10px] text-slate-400 uppercase font-sans font-bold">Score & Confidence</span>
          <div className="flex items-center gap-1.5 mt-0.5 font-bold text-slate-900">
            <ScoreIndicator score={opportunity.overallScore} size="sm" />
            <span>({opportunity.confidence}% Conf)</span>
          </div>
        </div>
      </div>

      {/* NOT FIT Alert Callout */}
      {isNotFit && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-xs text-red-900 flex items-start gap-2.5">
          <AlertOctagon className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold">Not Fit for Proposal Generation</p>
            <p className="leading-relaxed">
              This opportunity has been classified as Not Fit. Please review the opportunity analysis before generating a proposal.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
