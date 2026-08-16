import React from 'react';
import { ProposalSection } from '../../types/proposal';
import { Check, Edit3, Layers } from 'lucide-react';

interface ProposalSectionListProps {
  sections: ProposalSection[];
  activeSectionId: string;
  onSelectSection: (sectionId: string) => void;
}

export const ProposalSectionList: React.FC<ProposalSectionListProps> = ({
  sections,
  activeSectionId,
  onSelectSection,
}) => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-xs space-y-2">
      <div className="px-2 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono border-b border-slate-100 flex items-center gap-1.5">
        <Layers className="w-3.5 h-3.5 text-slate-400" />
        <span>Proposal Sections ({sections.length})</span>
      </div>

      <div className="space-y-1 max-h-[620px] overflow-y-auto pr-0.5">
        {sections.map((sec, idx) => {
          const isActive = sec.id === activeSectionId;
          return (
            <button
              key={sec.id}
              onClick={() => onSelectSection(sec.id)}
              className={`w-full flex items-center justify-between text-left px-3 py-2 rounded text-xs transition-all ${
                isActive
                  ? 'bg-[#111827] text-white font-bold border-l-2 border-[#86BC25] shadow-xs'
                  : 'text-slate-700 hover:bg-slate-100 font-medium'
              }`}
            >
              <span className="truncate pr-1">
                {idx + 1}. {sec.title}
              </span>

              <div className="flex items-center gap-1 shrink-0">
                {sec.status === 'EDITED' && (
                  <span
                    className="inline-flex items-center gap-0.5 text-[10px] font-mono bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded"
                    title="User Edited"
                  >
                    <Edit3 className="w-2.5 h-2.5" />
                  </span>
                )}
                {sec.status === 'GENERATED' && (
                  <Check className={`w-3.5 h-3.5 ${isActive ? 'text-[#86BC25]' : 'text-slate-400'}`} />
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
