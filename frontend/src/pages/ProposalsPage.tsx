import React, { useState, useEffect } from 'react';
import { Proposal, Opportunity, CompanyProfile } from '../types';
import { ProposalGeneratorPage } from './proposals/ProposalGeneratorPage';
import { ProposalEditorPage } from './proposals/ProposalEditorPage';
import { ProposalStatusBadge } from '../components/proposals/ProposalStatus';
import { proposalService } from '../services/proposalService';
import {
  FileText,
  Plus,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ChevronRight,
  Globe,
  Building2,
  Calendar,
  Layers,
  Award,
  X,
  AlertCircle,
} from 'lucide-react';

interface ProposalsPageProps {
  opportunities: Opportunity[];
  companyProfile: CompanyProfile;
  initialOpportunityId?: string | null;
  onNavigateToOpportunity?: (id: string) => void;
}

export const ProposalsPage: React.FC<ProposalsPageProps> = ({
  opportunities,
  companyProfile,
  initialOpportunityId,
  onNavigateToOpportunity,
}) => {
  // Navigation sub-views: 'hub' | 'new' | 'editor'
  const [activeTab, setActiveTab] = useState<'hub' | 'new' | 'editor'>(
    initialOpportunityId ? 'new' : 'hub'
  );

  // Data Stores
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [activeProposal, setActiveProposal] = useState<Proposal | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filters & Search for Hub
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Unsaved Changes Confirmation Modal State
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [pendingTabSwitch, setPendingTabSwitch] = useState<'hub' | 'new' | 'editor' | null>(null);
  const [showUnsavedModal, setShowUnsavedModal] = useState(false);

  // Load existing proposals on mount
  const loadProposals = async () => {
    setIsLoading(true);
    try {
      const data = await proposalService.getProposals();
      setProposals(data);
      if (data.length > 0 && !activeProposal) {
        setActiveProposal(data[0]);
      }
    } catch (err) {
      console.error('Error loading proposals:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProposals();
  }, []);

  // Handle navigating away safely
  const handleTabSwitch = (targetTab: 'hub' | 'new' | 'editor') => {
    if (hasUnsavedChanges) {
      setPendingTabSwitch(targetTab);
      setShowUnsavedModal(true);
    } else {
      setActiveTab(targetTab);
    }
  };

  const confirmDiscardAndSwitch = () => {
    setHasUnsavedChanges(false);
    setShowUnsavedModal(false);
    if (pendingTabSwitch) {
      setActiveTab(pendingTabSwitch);
      setPendingTabSwitch(null);
    }
  };

  const handleProposalCreated = (newProposal: Proposal) => {
    setProposals((prev) => [newProposal, ...prev]);
    setActiveProposal(newProposal);
    setHasUnsavedChanges(false);
    setActiveTab('editor');
  };

  const handleUpdateProposal = (updated: Proposal) => {
    setActiveProposal(updated);
    setProposals((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    setHasUnsavedChanges(true);
  };

  // Filtered proposals for Hub list
  const filteredProposals = proposals.filter((p) => {
    const matchesSearch =
      p.config.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.opportunityTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || p.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Sub-navigation Sub-Header Tabs */}
      <div className="bg-white rounded-lg border border-slate-200 p-2 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-1 font-mono text-xs font-bold">
          <button
            onClick={() => handleTabSwitch('hub')}
            className={`px-3.5 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
              activeTab === 'hub'
                ? 'bg-[#111827] text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Proposal Drafts Hub ({proposals.length})</span>
          </button>

          <button
            onClick={() => handleTabSwitch('new')}
            className={`px-3.5 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
              activeTab === 'new'
                ? 'bg-[#111827] text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Plus className="w-3.5 h-3.5 text-[#86BC25]" />
            <span>Configure New Proposal</span>
          </button>

          {activeProposal && (
            <button
              onClick={() => handleTabSwitch('editor')}
              className={`px-3.5 py-1.5 rounded transition-colors flex items-center gap-1.5 ${
                activeTab === 'editor'
                  ? 'bg-[#111827] text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              <span>Editor Workspace [{activeProposal.id}]</span>
            </button>
          )}
        </div>

        {activeTab === 'hub' && (
          <button
            onClick={() => handleTabSwitch('new')}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-[#007629] hover:bg-[#005f20] rounded shadow-xs transition-all active:scale-98"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#86BC25]" />
            <span>Generate Proposal Draft</span>
          </button>
        )}
      </div>

      {/* VIEW 1: Proposal Generator Wizard */}
      {activeTab === 'new' && (
        <ProposalGeneratorPage
          opportunities={opportunities}
          companyProfile={companyProfile}
          initialOpportunityId={initialOpportunityId}
          onProposalCreated={handleProposalCreated}
          onNavigateToOpportunity={(id) => onNavigateToOpportunity && onNavigateToOpportunity(id)}
          onBackToHub={() => handleTabSwitch('hub')}
        />
      )}

      {/* VIEW 2: Proposal Editor Workspace */}
      {activeTab === 'editor' && activeProposal && (
        <ProposalEditorPage
          proposal={activeProposal}
          onUpdateProposal={handleUpdateProposal}
          onBackToHub={() => handleTabSwitch('hub')}
          onNavigateToOpportunity={(id) => onNavigateToOpportunity && onNavigateToOpportunity(id)}
        />
      )}

      {/* VIEW 3: Proposal Hub / List View */}
      {activeTab === 'hub' && (
        <div className="space-y-6">
          {/* Header Banner */}
          <div className="bg-[#111827] text-white rounded-lg p-5 shadow-xs flex flex-wrap items-center justify-between gap-4 border-l-4 border-[#86BC25]">
            <div className="space-y-1">
              <h1 className="text-xl font-extrabold tracking-tight flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#86BC25]" />
                <span>Proposal Drafts Hub</span>
              </h1>
              <p className="text-xs text-slate-300 font-mono">
                Manage AI-Assisted Proposal Drafts, Review Quality Metrics & Export Final Submissions
              </p>
            </div>

            <button
              onClick={() => handleTabSwitch('new')}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-slate-900 bg-[#86BC25] hover:bg-[#78a821] rounded shadow-xs transition-all active:scale-98"
            >
              <Plus className="w-4 h-4" />
              <span>Create New Proposal</span>
            </button>
          </div>

          {/* Search & Filter Bar */}
          <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search proposal drafts by title, tender name, or ID..."
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>

            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-slate-500 font-bold">Status Filter:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-[#F5F6F7] border border-slate-200 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              >
                <option value="ALL">All Statuses</option>
                <option value="DRAFT">DRAFT</option>
                <option value="READY_FOR_REVIEW">READY FOR REVIEW</option>
                <option value="IN_REVIEW">IN REVIEW</option>
                <option value="APPROVED">APPROVED</option>
                <option value="EXPORTED">EXPORTED</option>
              </select>
            </div>
          </div>

          {/* Proposals List Grid */}
          {isLoading ? (
            <div className="p-12 text-center bg-white rounded-lg border border-slate-200 font-mono text-xs text-slate-500">
              <div className="w-6 h-6 border-2 border-slate-300 border-t-[#86BC25] rounded-full animate-spin mx-auto mb-2" />
              <span>Loading Proposal Repository...</span>
            </div>
          ) : filteredProposals.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredProposals.map((prop) => (
                <div
                  key={prop.id}
                  className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition-all flex flex-col justify-between space-y-4 relative overflow-hidden group"
                >
                  <div className="absolute top-0 left-0 bottom-0 w-1 bg-[#86BC25]" />

                  <div className="space-y-2">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                      <span className="font-mono text-xs font-bold text-slate-500">
                        {prop.id}
                      </span>
                      <ProposalStatusBadge status={prop.status} />
                    </div>

                    <h3 className="text-sm font-extrabold text-slate-900 leading-snug group-hover:text-[#007629] transition-colors">
                      {prop.config.title}
                    </h3>

                    <p className="text-xs text-slate-500 font-mono line-clamp-1">
                      Tender: <strong>{prop.opportunityTitle}</strong>
                    </p>
                  </div>

                  {/* Metrics Badge Chips */}
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono bg-[#F5F6F7] p-2.5 rounded border border-slate-200/80">
                    <div>
                      <span className="text-[9px] uppercase text-slate-400 font-sans font-bold">Alignment</span>
                      <div className="font-bold text-slate-800">{prop.qualityMetrics.tenderAlignment}%</div>
                    </div>
                    <div>
                      <span className="text-[9px] uppercase text-slate-400 font-sans font-bold">Coverage</span>
                      <div className="font-bold text-slate-800">{prop.qualityMetrics.requirementCoverage}%</div>
                    </div>
                    <div>
                      <span className="text-[9px] uppercase text-slate-400 font-sans font-bold">Sections</span>
                      <div className="font-bold text-slate-800">{prop.sections.length} Sections</div>
                    </div>
                  </div>

                  {/* Card Action Footer */}
                  <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-xs">
                    <span className="text-[11px] text-slate-400 font-mono">
                      Updated: {prop.updatedAt}
                    </span>

                    <button
                      onClick={() => {
                        setActiveProposal(prop);
                        setActiveTab('editor');
                      }}
                      className="inline-flex items-center gap-1 font-bold text-[#007629] hover:text-[#005f20] hover:underline"
                    >
                      <span>Open Workspace</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center bg-white rounded-lg border border-slate-200 space-y-3">
              <FileText className="w-10 h-10 text-slate-300 mx-auto" />
              <div className="space-y-1">
                <p className="text-sm font-bold text-slate-800">No Proposals Found</p>
                <p className="text-xs text-slate-500">
                  No proposal drafts match your search filters or exist yet.
                </p>
              </div>
              <button
                onClick={() => handleTabSwitch('new')}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-[#007629] hover:bg-[#005f20] rounded shadow-xs"
              >
                <Plus className="w-4 h-4 text-[#86BC25]" />
                <span>Configure First Proposal</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Unsaved Changes Protection Modal */}
      {showUnsavedModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-sm w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-2.5 text-amber-600">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <h3 className="text-sm font-extrabold text-slate-900">Unsaved Changes</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              You have unsaved changes in the current proposal workspace. Navigating away without saving may cause loss of edits.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setShowUnsavedModal(false)}
                className="px-3 py-1.5 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded"
              >
                Keep Editing
              </button>
              <button
                onClick={confirmDiscardAndSwitch}
                className="px-3 py-1.5 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded"
              >
                Discard & Leave
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
