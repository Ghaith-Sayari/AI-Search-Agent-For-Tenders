import React from 'react';
import { ScoreBreakdown } from '../../types';

interface ScoreBreakdownBarsProps {
  scoreBreakdown: ScoreBreakdown;
  compact?: boolean;
}

export const ScoreBreakdownBars: React.FC<ScoreBreakdownBarsProps> = ({
  scoreBreakdown,
  compact = false,
}) => {
  const categories = [
    { key: 'sectorRelevance', label: 'Sector Relevance', score: scoreBreakdown.sectorRelevance },
    { key: 'servicesRelevance', label: 'Services Relevance', score: scoreBreakdown.servicesRelevance },
    { key: 'geographyRelevance', label: 'Geography Relevance', score: scoreBreakdown.geographyRelevance },
    { key: 'eligibilityFit', label: 'Eligibility Fit', score: scoreBreakdown.eligibilityFit },
    { key: 'strategicFit', label: 'Strategic Fit', score: scoreBreakdown.strategicFit },
  ];

  const getBarColor = (val: number) => {
    if (val >= 80) return 'bg-[#86BC25]'; // Deloitte bright green
    if (val >= 60) return 'bg-amber-500';
    if (val >= 40) return 'bg-slate-400';
    return 'bg-red-500';
  };

  return (
    <div className={`space-y-${compact ? '2' : '3.5'}`}>
      {categories.map((cat) => (
        <div key={cat.key} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-700">{cat.label}</span>
            <span className="font-mono font-bold text-slate-900">{cat.score} / 100</span>
          </div>
          <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-300 ${getBarColor(
                cat.score
              )}`}
              style={{ width: `${Math.min(100, Math.max(0, cat.score))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};
