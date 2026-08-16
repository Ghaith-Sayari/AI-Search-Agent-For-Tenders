import React from 'react';
import {
  LayoutDashboard,
  Target,
  BarChart3,
  Inbox,
  GitBranch,
  Activity,
  DollarSign,
  Settings,
  ShieldCheck,
  LogOut,
  FileText,
} from 'lucide-react';

export type NavRoute =
  | 'dashboard'
  | 'opportunities'
  | 'proposals'
  | 'analyses'
  | 'reviews'
  | 'runs'
  | 'system'
  | 'cost'
  | 'settings';

interface SidebarProps {
  currentRoute: NavRoute;
  onNavigate: (route: NavRoute) => void;
  reviewCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onNavigate,
  reviewCount = 3,
}) => {
  const navItems = [
    { id: 'dashboard' as NavRoute, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'opportunities' as NavRoute, label: 'Opportunities', icon: Target },
    { id: 'proposals' as NavRoute, label: 'Proposal Generator', icon: FileText },
    { id: 'analyses' as NavRoute, label: 'Analyses', icon: BarChart3 },
    {
      id: 'reviews' as NavRoute,
      label: 'Review Queue',
      icon: Inbox,
      badge: reviewCount > 0 ? reviewCount : undefined,
    },
    { id: 'runs' as NavRoute, label: 'Pipeline Runs', icon: GitBranch },
    { id: 'system' as NavRoute, label: 'System Health', icon: Activity },
    { id: 'cost' as NavRoute, label: 'Cost & Usage', icon: DollarSign },
    { id: 'settings' as NavRoute, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#111827] text-slate-300 flex flex-col justify-between shrink-0 border-r border-slate-800 select-none h-screen sticky top-0 overflow-y-auto">
      {/* Top Header & Brand Identity */}
      <div>
        <div className="h-16 px-6 flex items-center gap-2.5 border-b border-slate-800">
          <div className="w-7 h-7 bg-white text-slate-950 font-black rounded flex items-center justify-center font-mono text-sm relative">
            T
            <span className="w-2 h-2 rounded-full bg-[#86BC25] absolute -top-0.5 -right-0.5" />
          </div>
          <div>
            <div className="flex items-center gap-1">
              <span className="text-white font-bold tracking-tight text-sm">TenderIntel</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#86BC25]" title="Deloitte Visual Standard" />
            </div>
            <p className="text-[10px] uppercase tracking-widest text-slate-400 font-mono">
              AI Opportunity Intel
            </p>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="px-3 py-4 space-y-1">
          <p className="px-3 text-[10px] uppercase tracking-wider font-semibold text-slate-500 mb-2">
            Main Platform
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentRoute === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-semibold transition-colors ${
                  isActive
                    ? 'bg-slate-800 text-white border-l-2 border-[#86BC25] pl-2.5'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#86BC25]' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-mono px-1.5 py-0.2 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>


      </div>

      {/* User Profile & Role Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60">
        <div className="flex items-center justify-between px-2 py-1.5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-[#86BC25]">
              GS
            </div>
            <div className="text-left">
              <div className="text-xs font-bold text-slate-100 leading-tight">Ghaith Sayari</div>
              <div className="text-[10px] text-slate-400 font-medium">Senior Partner • EMEA Advisory</div>
            </div>
          </div>
          <button
            title="Account Security"
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </button>
        </div>
      </div>
    </aside>
  );
};
