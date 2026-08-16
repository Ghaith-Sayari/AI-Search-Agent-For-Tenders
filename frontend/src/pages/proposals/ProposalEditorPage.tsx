import React, { useState } from 'react';
import { Proposal, ProposalSection } from '../../types/proposal';
import { ProposalSectionList } from '../../components/proposals/ProposalSectionList';
import { ProposalEditor } from '../../components/proposals/ProposalEditor';
import { ProposalQualityPanel } from '../../components/proposals/ProposalQualityPanel';
import { MissingInformation } from '../../components/proposals/MissingInformation';
import { ProposalExport } from '../../components/proposals/ProposalExport';
import { ProposalStatusBadge } from '../../components/proposals/ProposalStatus';
import { proposalService } from '../../services/proposalService';
import {
  ArrowLeft,
  Save,
  CheckCircle,
  FileText,
  Clock,
  Sparkles,
  ExternalLink,
} from 'lucide-react';

interface ProposalEditorPageProps {
  proposal: Proposal;
  onUpdateProposal: (updated: Proposal) => void;
  onBackToHub: () => void;
  onNavigateToOpportunity?: (oppId: string) => void;
}

export const ProposalEditorPage: React.FC<ProposalEditorPageProps> = ({
  proposal,
  onUpdateProposal,
  onBackToHub,
  onNavigateToOpportunity,
}) => {
  const [activeSectionId, setActiveSectionId] = useState<string>(
    proposal.sections[0]?.id || ''
  );
  const [isRegenerating, setIsRegenerating] = useState<string | null>(null);
  const [autosaveStatus, setAutosaveStatus] = useState<'Saved' | 'Saving...' | 'Unsaved changes'>(
    'Saved'
  );

  const activeSection =
    proposal.sections.find((s) => s.id === activeSectionId) || proposal.sections[0];

  const handleSectionContentChange = (newContent: string) => {
    setAutosaveStatus('Unsaved changes');
    const updatedSections = proposal.sections.map((sec) =>
      sec.id === activeSectionId
        ? {
            ...sec,
            content: newContent,
            status: 'EDITED' as const,
            lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
          }
        : sec
    );

    onUpdateProposal({
      ...proposal,
      sections: updatedSections,
    });
  };

  const handleSaveSection = async () => {
    setAutosaveStatus('Saving...');
    try {
      const saved = await proposalService.updateProposal(proposal.id, {
        sections: proposal.sections,
      });
      onUpdateProposal(saved);
      setAutosaveStatus('Saved');
    } catch (err) {
      console.error('Save error:', err);
      setAutosaveStatus('Unsaved changes');
    }
  };

  const handleSectionAiAction = async (
    action: 'Regenerate' | 'Improve' | 'Shorten' | 'Expand'
  ) => {
    if (!activeSection) return;
    setIsRegenerating(action);

    try {
      const updatedSection = await proposalService.regenerateSection(
        proposal.id,
        activeSection.id,
        action
      );

      const updatedSections = proposal.sections.map((s) =>
        s.id === activeSection.id ? updatedSection : s
      );

      onUpdateProposal({
        ...proposal,
        sections: updatedSections,
      });
      setAutosaveStatus('Saved');
    } catch (err) {
      console.error('Error running section AI action:', err);
    } finally {
      setIsRegenerating(null);
    }
  };

  const handleStatusChange = async (newStatus: Proposal['status']) => {
    try {
      const updated = await proposalService.updateProposal(proposal.id, {
        status: newStatus,
      });
      onUpdateProposal(updated);
    } catch (err) {
      console.error('Error updating status:', err);
    }
  };

  const handleExport = async (format: 'pdf' | 'docx' | 'markdown') => {
    const res = await proposalService.exportProposal(proposal.id, format);
    // Refresh proposal state to reflect EXPORTED status
    const updated = await proposalService.getProposalById(proposal.id);
    if (updated) onUpdateProposal(updated);
    return res;
  };

  return (
    <div className="space-y-6">
      {/* Top Header Workspace Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToHub}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50 shadow-xs transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Proposals Hub</span>
          </button>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-500">
                {proposal.id}
              </span>
              <ProposalStatusBadge status={proposal.status} />
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {proposal.config.title}
            </h1>
          </div>
        </div>

        {/* Action Controls & Status Transition Bar */}
        <div className="flex items-center gap-2">
          {onNavigateToOpportunity && (
            <button
              onClick={() => onNavigateToOpportunity(proposal.opportunityId)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded border border-slate-300 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
              <span>Target Opportunity</span>
            </button>
          )}

          {proposal.status !== 'APPROVED' && proposal.status !== 'EXPORTED' && (
            <button
              onClick={() => handleStatusChange('APPROVED')}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-emerald-700 hover:bg-emerald-800 rounded shadow-xs transition-all"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Mark Approved</span>
            </button>
          )}

          <button
            onClick={handleSaveSection}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-[#007629] hover:bg-[#005f20] rounded shadow-xs transition-all"
          >
            <Save className="w-3.5 h-3.5 text-[#86BC25]" />
            <span>Save All Draft Changes</span>
          </button>
        </div>
      </div>

      {/* Main 3-Column Proposal Editor Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (3 cols): Section Navigator Sidebar */}
        <div className="lg:col-span-3 space-y-4">
          <ProposalSectionList
            sections={proposal.sections}
            activeSectionId={activeSectionId}
            onSelectSection={(id) => setActiveSectionId(id)}
          />

          {/* Proposal Config Card */}
          <div className="bg-white rounded-lg border border-slate-200 p-3.5 shadow-xs text-xs space-y-2">
            <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[10px] font-mono border-b border-slate-100 pb-1">
              Configuration Snapshot
            </h4>
            <div className="space-y-1 text-slate-600 font-mono text-[11px]">
              <div>Profile: <strong>{proposal.config.companyProfileName}</strong></div>
              <div>Language: <strong>{proposal.config.language}</strong></div>
              <div>Type: <strong>{proposal.config.proposalType}</strong></div>
              <div>Tone: <strong>{proposal.config.tone}</strong></div>
            </div>
          </div>
        </div>

        {/* Center Column (6 cols): Document Editor Workspace */}
        <div className="lg:col-span-6 space-y-4">
          {activeSection ? (
            <ProposalEditor
              section={activeSection}
              onContentChange={handleSectionContentChange}
              onSaveSection={handleSaveSection}
              onSectionAiAction={handleSectionAiAction}
              isRegenerating={isRegenerating}
              autosaveStatus={autosaveStatus}
            />
          ) : (
            <div className="p-12 text-center bg-white rounded-lg border border-slate-200 text-slate-500">
              Select a section to begin editing.
            </div>
          )}
        </div>

        {/* Right Column (3 cols): Quality, Missing Info & Export Options */}
        <div className="lg:col-span-3 space-y-5">
          <ProposalQualityPanel metrics={proposal.qualityMetrics} />
          <MissingInformation items={proposal.qualityMetrics.missingInformation} />
          <ProposalExport
            proposalId={proposal.id}
            onExport={handleExport}
          />
        </div>
      </div>
    </div>
  );
};
