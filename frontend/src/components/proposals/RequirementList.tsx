import React from 'react';
import { Opportunity } from '../../types';
import { CheckCircle2, ShieldCheck, Package, Calendar, Award } from 'lucide-react';

interface RequirementListProps {
  opportunity: Opportunity;
}

export const RequirementList: React.FC<RequirementListProps> = ({ opportunity }) => {
  const hasRequirements = opportunity.requirements && opportunity.requirements.length > 0;
  const hasEligibility = opportunity.eligibilityCriteria && opportunity.eligibilityCriteria.length > 0;

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-[#86BC25]" />
          <span>Extracted Tender Requirements & Deliverables</span>
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
        {/* Key Requirements */}
        <div className="space-y-2 bg-[#F5F6F7] p-3.5 rounded border border-slate-200/80">
          <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Key Requirements</span>
          </h4>
          {hasRequirements ? (
            <ul className="space-y-2 text-slate-700">
              {opportunity.requirements.map((req, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#86BC25] mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{req}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400 italic">Information not available</p>
          )}
        </div>

        {/* Eligibility Requirements */}
        <div className="space-y-2 bg-[#F5F6F7] p-3.5 rounded border border-slate-200/80">
          <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-blue-600" />
            <span>Eligibility Requirements</span>
          </h4>
          {hasEligibility ? (
            <ul className="space-y-2 text-slate-700">
              {opportunity.eligibilityCriteria.map((elig, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                  <span className="leading-relaxed">{elig}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400 italic">Information not available</p>
          )}
        </div>

        {/* Deliverables */}
        <div className="space-y-2 bg-[#F5F6F7] p-3.5 rounded border border-slate-200/80">
          <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] flex items-center gap-1.5">
            <Package className="w-3.5 h-3.5 text-purple-600" />
            <span>Scope Deliverables</span>
          </h4>
          <ul className="space-y-2 text-slate-700">
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shrink-0" />
              <span>Technical Solution & Architecture Specification Blueprint</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shrink-0" />
              <span>Full System Implementation & Source Code Migration Playbook</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shrink-0" />
              <span>Security Governance, Compliance & SLA Support Documentation</span>
            </li>
          </ul>
        </div>

        {/* Evaluation Criteria & Important Dates */}
        <div className="space-y-2 bg-[#F5F6F7] p-3.5 rounded border border-slate-200/80">
          <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-amber-600" />
            <span>Important Schedule & Evaluation</span>
          </h4>
          <div className="space-y-2 text-slate-700">
            <div>
              <span className="font-bold text-slate-900">Submission Deadline: </span>
              <span className="font-mono text-slate-800">{opportunity.deadline}</span>
            </div>
            <div>
              <span className="font-bold text-slate-900">Evaluation Weights: </span>
              <span className="text-slate-600">Technical Merit (50%), Implementation (30%), Price (20%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
