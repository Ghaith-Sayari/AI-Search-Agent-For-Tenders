import React from 'react';
import { ProposalStatus as StatusType } from '../../types/proposal';

interface ProposalStatusProps {
  status: StatusType;
  className?: string;
}

export const ProposalStatusBadge: React.FC<ProposalStatusProps> = ({ status, className = '' }) => {
  const getStyles = () => {
    switch (status) {
      case 'DRAFT':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'GENERATING':
        return 'bg-amber-50 text-amber-800 border-amber-300 animate-pulse';
      case 'READY_FOR_REVIEW':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'IN_REVIEW':
        return 'bg-purple-50 text-purple-800 border-purple-200';
      case 'APPROVED':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300';
      case 'EXPORTED':
        return 'bg-teal-50 text-teal-800 border-teal-300';
      case 'FAILED':
        return 'bg-red-50 text-red-800 border-red-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getLabel = () => {
    switch (status) {
      case 'READY_FOR_REVIEW':
        return 'READY FOR REVIEW';
      case 'IN_REVIEW':
        return 'IN REVIEW';
      default:
        return status.replace(/_/g, ' ');
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded font-mono text-[10px] font-bold uppercase tracking-wide border ${getStyles()} ${className}`}
    >
      {getLabel()}
    </span>
  );
};
