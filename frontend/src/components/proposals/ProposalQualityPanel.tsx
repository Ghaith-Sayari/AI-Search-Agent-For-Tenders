import React from 'react';
import { ProposalQualityMetrics } from '../../types/proposal';
import { Award, ShieldCheck } from 'lucide-react';

interface ProposalQualityPanelProps {
  metrics: ProposalQualityMetrics;
}

export const ProposalQualityPanel: React.FC<ProposalQualityPanelProps> = ({ metrics }) => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-1.5">
          <Award className="w-3.5 h-3.5 text-[#86BC25]" />
          <span>Proposal Quality</span>
        </h3>
        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
          {metrics.aiConfidence} Confidence
        </span>
      </div>

      <div className="space-y-3 text-xs font-sans">
        <div>
          <div className="flex justify-between text-slate-700 font-medium mb-1">
            <span>Tender Alignment</span>
            <span className="font-bold font-mono">{metrics.tenderAlignment}%</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-[#007629] rounded-full transition-all duration-300"
              style={{ width: `${metrics.tenderAlignment}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-700 font-medium mb-1">
            <span>Requirement Coverage</span>
            <span className="font-bold font-mono">{metrics.requirementCoverage}%</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-300"
              style={{ width: `${metrics.requirementCoverage}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-700 font-medium mb-1">
            <span>Company Capability Alignment</span>
            <span className="font-bold font-mono">{metrics.companyCapabilityAlignment}%</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all duration-300"
              style={{ width: `${metrics.companyCapabilityAlignment}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-slate-700 font-medium mb-1">
            <span>Completeness Score</span>
            <span className="font-bold font-mono">{metrics.completeness ?? 90}%</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-indigo-600 rounded-full transition-all duration-300"
              style={{ width: `${metrics.completeness ?? 90}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
