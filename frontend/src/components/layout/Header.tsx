import React from 'react';
import { NavRoute } from './Sidebar';
import {
  Bell,
  Play,
  RotateCw,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';

interface HeaderProps {
  currentRoute: NavRoute;
  selectedOpportunityId?: string | null;
  onNavigate: (route: NavRoute) => void;
  onTriggerRun: () => void;
  isRunExecuting?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentRoute,
  selectedOpportunityId,
  onNavigate,
  onTriggerRun,
  isRunExecuting = false,
}) => {
  const getBreadcrumb = () => {
    switch (currentRoute) {
      case 'dashboard':
        return 'Dashboard Overview';
      case 'opportunities':
        return selectedOpportunityId ? `Opportunities / ${selectedOpportunityId}` : 'Opportunities';
      case 'proposals':
        return 'Proposal Generator Workspace';
      case 'analyses':
        return 'Opportunity Fit Analyses';
      case 'reviews':
        return 'Human Review Queue';
      case 'runs':
        return 'Pipeline Execution Runs';
      case 'system':
        return 'System Health & Agents';
      case 'cost':
        return 'AI Cost & Token Usage';
      case 'settings':
        return 'Company Profile & AI Settings';
      default:
        return 'Platform';
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Breadcrumbs & Title */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold uppercase text-slate-400 tracking-wider font-mono">
          TenderIntel
        </span>
        <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
        <h1 className="text-sm font-bold text-slate-900 tracking-tight">
          {getBreadcrumb()}
        </h1>
      </div>

      {/* Header Actions & Quick Status */}
      <div className="flex items-center gap-3">
        {/* Live Agent Status Badge */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-md text-xs font-medium text-slate-700">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#86BC25] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#007629]"></span>
          </span>
          <span>Agent Pipeline: <strong>Active</strong></span>
        </div>

        {/* Trigger Run Button */}
        <button
          onClick={onTriggerRun}
          disabled={isRunExecuting}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white rounded-md transition-all shadow-xs ${
            isRunExecuting
              ? 'bg-slate-400 cursor-not-allowed'
              : 'bg-[#111827] hover:bg-[#007629] active:scale-98'
          }`}
        >
          {isRunExecuting ? (
            <RotateCw className="w-3.5 h-3.5 animate-spin text-[#86BC25]" />
          ) : (
            <Play className="w-3.5 h-3.5 text-[#86BC25] fill-[#86BC25]" />
          )}
          <span>{isRunExecuting ? 'Processing Pipeline...' : 'Run Pipeline'}</span>
        </button>

        {/* Notification Bell */}
        <button
          onClick={() => onNavigate('reviews')}
          className="relative p-2 text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md"
          title="Review Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-amber-500 ring-2 ring-white" />
        </button>
      </div>
    </header>
  );
};
