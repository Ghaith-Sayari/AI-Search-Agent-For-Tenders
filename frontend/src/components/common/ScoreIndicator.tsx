import React from 'react';

interface ScoreIndicatorProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ScoreIndicator: React.FC<ScoreIndicatorProps> = ({
  score,
  size = 'md',
  showLabel = false,
}) => {
  // Deloitte color tier logic
  let bgClass = 'bg-emerald-50 text-emerald-800 border-emerald-300';
  let badgeFill = 'bg-emerald-600';
  if (score >= 80) {
    bgClass = 'bg-emerald-50 text-emerald-900 border-emerald-300';
    badgeFill = 'bg-[#86BC25]'; // Deloitte bright green
  } else if (score >= 60) {
    bgClass = 'bg-amber-50 text-amber-900 border-amber-300';
    badgeFill = 'bg-amber-500';
  } else if (score >= 40) {
    bgClass = 'bg-slate-100 text-slate-700 border-slate-300';
    badgeFill = 'bg-slate-400';
  } else {
    bgClass = 'bg-red-50 text-red-900 border-red-300';
    badgeFill = 'bg-red-500';
  }

  const dimensions = {
    sm: 'text-xs px-2 py-0.5 font-semibold',
    md: 'text-sm px-2.5 py-1 font-bold',
    lg: 'text-base px-3.5 py-1.5 font-extrabold',
  }[size];

  return (
    <div className="inline-flex items-center gap-1.5">
      <span
        className={`inline-flex items-center gap-1.5 rounded-md border ${bgClass} ${dimensions} tracking-tight font-mono`}
      >
        <span className={`w-2 h-2 rounded-full ${badgeFill}`} />
        {score}
        {showLabel && <span className="font-sans font-normal text-xs text-slate-500">/100</span>}
      </span>
    </div>
  );
};
