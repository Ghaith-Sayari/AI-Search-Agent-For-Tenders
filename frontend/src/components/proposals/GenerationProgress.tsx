import React from 'react';
import { Sparkles, CheckCircle2, ShieldCheck } from 'lucide-react';

interface GenerationProgressProps {
  currentStage: string;
  progressPercent: number;
}

export const GenerationProgress: React.FC<GenerationProgressProps> = ({
  currentStage,
  progressPercent,
}) => {
  const stages = [
    { label: 'Preparing tender information', minProgress: 15 },
    { label: 'Preparing opportunity analysis', minProgress: 35 },
    { label: 'Preparing company profile', minProgress: 55 },
    { label: 'Generating proposal', minProgress: 75 },
    { label: 'Validating draft', minProgress: 90 },
    { label: 'Proposal ready', minProgress: 100 },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 space-y-5 shadow-2xl animate-fade-in">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
          <div className="w-10 h-10 rounded-full bg-[#111827] text-[#86BC25] flex items-center justify-center shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-slate-900">
              Generating Proposal Draft
            </h3>
            <p className="text-xs text-slate-500 font-mono">
              Enterprise AI Proposal Engine
            </p>
          </div>
        </div>

        {/* Progress Bar & Stage Title */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-mono font-bold text-slate-800">
            <span>{currentStage || 'Initializing generation...'}</span>
            <span className="text-[#007629]">{progressPercent}%</span>
          </div>
          <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className="h-full bg-[#007629] transition-all duration-300 rounded-full"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Stage Checklist */}
        <ul className="space-y-2 text-xs font-mono text-slate-600 border-t border-slate-100 pt-3">
          {stages.map((stg) => {
            const isDone = progressPercent >= stg.minProgress;
            const isCurrent =
              progressPercent < stg.minProgress &&
              progressPercent >= stg.minProgress - 20;

            return (
              <li key={stg.label} className="flex items-center gap-2.5">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : isCurrent ? (
                  <div className="w-4 h-4 rounded-full border-2 border-[#86BC25] border-t-transparent animate-spin shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-300 shrink-0" />
                )}
                <span
                  className={
                    isDone
                      ? 'text-slate-900 font-bold'
                      : isCurrent
                      ? 'text-[#007629] font-bold'
                      : 'text-slate-400'
                  }
                >
                  {stg.label}
                </span>
              </li>
            );
          })}
        </ul>

        {/* Human Review Reminder Footer */}
        <div className="p-3 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-900 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            AI-generated content requires human review before submission.
          </span>
        </div>
      </div>
    </div>
  );
};
