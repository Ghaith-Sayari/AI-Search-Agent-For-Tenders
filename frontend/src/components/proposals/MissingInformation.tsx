import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

interface MissingInformationProps {
  items: string[];
}

export const MissingInformation: React.FC<MissingInformationProps> = ({ items }) => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-3">
      <div className="flex items-center gap-1.5 border-b border-slate-100 pb-2">
        <AlertTriangle className="w-4 h-4 text-amber-600" />
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
          Missing Information & Warnings
        </h3>
      </div>

      {/* Missing Information Items List */}
      {items && items.length > 0 ? (
        <ul className="space-y-1.5 text-xs font-sans text-slate-700">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-2 bg-amber-50/50 p-2 rounded border border-amber-100">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
              <span className="leading-relaxed">{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-slate-400 italic font-mono">No critical missing information flagged.</p>
      )}

      {/* Anti-Hallucination Notice */}
      <div className="p-3 bg-slate-900 rounded-md border border-slate-800 text-slate-200 space-y-1">
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#86BC25]">
          <ShieldAlert className="w-4 h-4" />
          <span>Anti-Hallucination Verification Notice</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-300">
          AI-generated content may contain inaccuracies. Verify all factual, technical, financial, legal, and compliance information before submission.
        </p>
      </div>
    </div>
  );
};
