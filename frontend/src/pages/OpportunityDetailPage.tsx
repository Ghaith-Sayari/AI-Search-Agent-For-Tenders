import React from 'react';
import { Opportunity } from '../types';
import { ScoreIndicator } from '../components/common/ScoreIndicator';
import { DecisionBadge } from '../components/common/DecisionBadge';
import { ScoreBreakdownBars } from '../components/common/ScoreBreakdownBars';
import {
  ArrowLeft,
  ExternalLink,
  Calendar,
  Globe,
  Building2,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ShieldCheck,
  Award,
  Sparkles,
  DollarSign,
  Briefcase,
  FileText,
} from 'lucide-react';

interface OpportunityDetailPageProps {
  opportunity: Opportunity;
  onBack: () => void;
  onNavigateToReviews: () => void;
  onGenerateProposal?: (opportunityId: string) => void;
}

export const OpportunityDetailPage: React.FC<OpportunityDetailPageProps> = ({
  opportunity,
  onBack,
  onNavigateToReviews,
  onGenerateProposal,
}) => {
  return (
    <div className="space-y-6">
      {/* Top Navigation Back Action */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 shadow-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Opportunities</span>
        </button>

        <div className="flex items-center gap-2">
          {onGenerateProposal && (opportunity.decision === 'GOOD_FIT' || opportunity.decision === 'NEEDS_REVIEW') && (
            <button
              onClick={() => onGenerateProposal(opportunity.id)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-[#007629] hover:bg-[#005f20] active:scale-98 rounded-md shadow-xs transition-all"
            >
              <FileText className="w-3.5 h-3.5 text-[#86BC25]" />
              <span>Generate Proposal Draft</span>
            </button>
          )}

          {opportunity.decision === 'NEEDS_REVIEW' && (
            <button
              onClick={onNavigateToReviews}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-md shadow-xs"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Resolve in Review Queue</span>
            </button>
          )}

          <a
            href={opportunity.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-md"
          >
            <span>External Notice</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          </a>
        </div>
      </div>

      {/* Main Opportunity Title Banner */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 relative overflow-hidden">
        <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-[#86BC25]" />
        
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2 max-w-3xl">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                {opportunity.externalId}
              </span>
              <span className="text-xs font-semibold text-slate-500">
                {opportunity.sector}
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs font-semibold text-slate-600">
                Profile: {opportunity.profileName}
              </span>
            </div>

            <h1 className="text-xl font-extrabold text-slate-900 leading-snug tracking-tight">
              {opportunity.title}
            </h1>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 pt-1 font-mono">
              <div className="flex items-center gap-1">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <span>{opportunity.country} ({opportunity.countryCode})</span>
              </div>
              <div className="flex items-center gap-1">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                <span>{opportunity.source}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Deadline: <strong>{opportunity.deadline}</strong></span>
              </div>
              <div className="flex items-center gap-1 text-slate-900 font-bold">
                <DollarSign className="w-3.5 h-3.5 text-emerald-600" />
                <span>{opportunity.estimatedValue}</span>
              </div>
            </div>
          </div>

          {/* Top Score Banner Badge */}
          <div className="flex flex-col items-end gap-2 shrink-0 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider font-mono">
              AI Decision & Fit
            </div>
            <div className="flex items-center gap-2">
              <ScoreIndicator score={opportunity.overallScore} size="lg" showLabel />
              <DecisionBadge decision={opportunity.decision} />
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Confidence: <strong>{opportunity.confidence}%</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Two-Column Detail View Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Tender Information & Description */}
        <div className="lg:col-span-2 space-y-6">
          {/* Executive Summary & Description */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase text-slate-700 tracking-wider border-b border-slate-100 pb-2">
              Tender Description & Scope
            </h2>
            <p className="text-sm text-slate-800 leading-relaxed font-sans">
              {opportunity.description}
            </p>
          </div>

          {/* Technical Requirements & Scope Deliverables */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase text-slate-700 tracking-wider border-b border-slate-100 pb-2">
              Core Technical Requirements
            </h2>
            <ul className="space-y-2 text-xs text-slate-700">
              {opportunity.requirements.map((req, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#86BC25] mt-1.5 shrink-0" />
                  <span>{req}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Mandatory Eligibility & Minimum Turnover Criteria */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase text-slate-700 tracking-wider border-b border-slate-100 pb-2">
              Eligibility & Prequalification Criteria
            </h2>
            <ul className="space-y-2 text-xs text-slate-700">
              {opportunity.eligibilityCriteria.map((elig, idx) => (
                <li key={idx} className="flex items-start gap-2 bg-slate-50 p-2 rounded border border-slate-200 font-mono">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{elig}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Column (1 Col): Multidimensional Score Breakdown & AI Reasoning */}
        <div className="space-y-6">
          {/* Multidimensional Score Breakdown Card */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h2 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
                Opportunity Fit Breakdown
              </h2>
              <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                Score: {opportunity.overallScore} / 100
              </span>
            </div>

            <ScoreBreakdownBars scoreBreakdown={opportunity.scoreBreakdown} />
          </div>

          {/* Structured AI Reasoning Card ("Why this opportunity?") */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
              <Sparkles className="w-4 h-4 text-[#86BC25]" />
              <h2 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
                Why This Opportunity? (AI Analysis)
              </h2>
            </div>

            {/* Matched Strengths */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-900 uppercase tracking-wider font-mono">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Matched Fit Factors</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700 bg-emerald-50/50 p-3 rounded-md border border-emerald-200/80">
                {opportunity.aiReasoning.matched.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Missing or Risk Factors */}
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 uppercase tracking-wider font-mono">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Missing / Risk Factors</span>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-700 bg-amber-50/50 p-3 rounded-md border border-amber-200/80">
                {opportunity.aiReasoning.missingOrRisk.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Strategic Recommendation */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
                <Lightbulb className="w-3.5 h-3.5 text-[#86BC25]" />
                <span>AI Gatekeeper Recommendation</span>
              </div>
              <p className="text-xs text-slate-800 bg-slate-50 p-3 rounded-md border border-slate-200 leading-relaxed font-sans font-medium">
                {opportunity.aiReasoning.recommendation}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
