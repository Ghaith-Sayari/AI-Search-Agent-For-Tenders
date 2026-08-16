import React, { useState } from 'react';
import { Sidebar, NavRoute } from './Sidebar';
import { Header } from './Header';
import { Menu, X } from 'lucide-react';

interface AppShellProps {
  currentRoute: NavRoute;
  selectedOpportunityId?: string | null;
  onNavigate: (route: NavRoute) => void;
  onTriggerRun: () => void;
  isRunExecuting?: boolean;
  reviewCount?: number;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentRoute,
  selectedOpportunityId,
  onNavigate,
  onTriggerRun,
  isRunExecuting,
  reviewCount = 3,
  children,
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-slate-900 flex flex-col md:flex-row font-sans antialiased">
      {/* Desktop Sidebar */}
      <div className="hidden md:block sticky top-0 h-screen z-20 shrink-0">
        <Sidebar
          currentRoute={currentRoute}
          onNavigate={(route) => {
            onNavigate(route);
          }}
          reviewCount={reviewCount}
        />
      </div>

      {/* Mobile Drawer Navigation Header */}
      <div className="md:hidden bg-[#111827] text-white p-3 flex items-center justify-between sticky top-0 z-30 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-white text-slate-950 font-bold text-xs rounded flex items-center justify-center font-mono">
            T
          </div>
          <span className="font-bold text-sm tracking-tight">TenderIntel</span>
          <span className="w-2 h-2 rounded-full bg-[#86BC25]" />
        </div>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-300"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Slideout Drawer */}
      {isMobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-xs flex">
          <div className="w-72 bg-[#111827] h-full flex flex-col">
            <Sidebar
              currentRoute={currentRoute}
              onNavigate={(route) => {
                onNavigate(route);
                setIsMobileMenuOpen(false);
              }}
              reviewCount={reviewCount}
            />
          </div>
          <div className="flex-1" onClick={() => setIsMobileMenuOpen(false)} />
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <Header
          currentRoute={currentRoute}
          selectedOpportunityId={selectedOpportunityId}
          onNavigate={onNavigate}
          onTriggerRun={onTriggerRun}
          isRunExecuting={isRunExecuting}
        />
        <main className="flex-1 p-4 md:p-6 max-w-7xl w-full mx-auto space-y-6 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  );
};
