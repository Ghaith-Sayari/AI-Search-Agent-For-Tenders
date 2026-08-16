import React from 'react';
import { DecisionStatus } from '../../types';
import { CheckCircle2, AlertTriangle, XCircle, AlertOctagon } from 'lucide-react';

interface DecisionBadgeProps {
  decision: DecisionStatus;
  size?: 'sm' | 'md';
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({ decision, size = 'md' }) => {
  const isSm = size === 'sm';

  switch (decision) {
    case 'GOOD_FIT':
      return (
        <span
          className={`inline-flex items-center gap-1 font-semibold text-emerald-900 bg-emerald-50 border border-emerald-300 rounded ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
          } uppercase tracking-wider font-mono`}
        >
          <CheckCircle2 className={`${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-[#007629]`} />
          Good Fit
        </span>
      );
    case 'NEEDS_REVIEW':
      return (
        <span
          className={`inline-flex items-center gap-1 font-semibold text-amber-900 bg-amber-50 border border-amber-300 rounded ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
          } uppercase tracking-wider font-mono`}
        >
          <AlertTriangle className={`${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-amber-600`} />
          Needs Review
        </span>
      );
    case 'NOT_FIT':
      return (
        <span
          className={`inline-flex items-center gap-1 font-medium text-slate-700 bg-slate-100 border border-slate-300 rounded ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
          } uppercase tracking-wider font-mono`}
        >
          <XCircle className={`${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-slate-500`} />
          Not Fit
        </span>
      );
    case 'FAILED':
      return (
        <span
          className={`inline-flex items-center gap-1 font-semibold text-red-900 bg-red-50 border border-red-300 rounded ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
          } uppercase tracking-wider font-mono`}
        >
          <AlertOctagon className={`${isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} text-red-600`} />
          Failed
        </span>
      );
    default:
      return null;
  }
};
