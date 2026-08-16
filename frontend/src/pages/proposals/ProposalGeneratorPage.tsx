import React, { useState } from 'react';
import { Opportunity, CompanyProfile } from '../../types';
import { Proposal, CreateProposalPayload } from '../../types/proposal';
import { TenderSummary } from '../../components/proposals/TenderSummary';
import { RequirementList } from '../../components/proposals/RequirementList';
import { ProposalConfiguration } from '../../components/proposals/ProposalConfiguration';
import { GenerationProgress } from '../../components/proposals/GenerationProgress';
import { proposalService } from '../../services/proposalService';
import { ArrowLeft, Sparkles, AlertTriangle } from 'lucide-react';

interface ProposalGeneratorPageProps {
  opportunities: Opportunity[];
  companyProfile: CompanyProfile;
  initialOpportunityId?: string | null;
  onProposalCreated: (proposal: Proposal) => void;
  onNavigateToOpportunity: (oppId: string) => void;
  onBackToHub: () => void;
}

export const ProposalGeneratorPage: React.FC<ProposalGeneratorPageProps> = ({
  opportunities,
  companyProfile,
  initialOpportunityId,
  onProposalCreated,
  onNavigateToOpportunity,
  onBackToHub,
}) => {
  // Filter opportunities to valid candidates (or default to first GOOD_FIT / NEEDS_REVIEW)
  const validOpportunities = opportunities.filter((o) => o.decision !== 'FAILED');

  const [selectedOppId, setSelectedOppId] = useState<string>(
    initialOpportunityId || validOpportunities[0]?.id || ''
  );

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStage, setGenerationStage] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const [generationError, setGenerationError] = useState<string | null>(null);

  const currentOpportunity =
    opportunities.find((o) => o.id === selectedOppId) || validOpportunities[0] || null;

  const isNotFit = currentOpportunity?.decision === 'NOT_FIT';

  const handleGenerateProposal = async (payload: CreateProposalPayload) => {
    if (!currentOpportunity || isNotFit) return;

    setIsGenerating(true);
    setGenerationError(null);
    setGenerationStage('Preparing tender information');
    setProgressPercent(10);

    try {
      const proposal = await proposalService.generateProposal(
        {
          ...payload,
          opportunityId: currentOpportunity.id,
        },
        (stage, pct) => {
          setGenerationStage(stage);
          setProgressPercent(pct);
        }
      );

      onProposalCreated(proposal);
    } catch (err) {
      console.error('Error generating proposal:', err);
      setGenerationError(err instanceof Error ? err.message : 'Proposal generation failed. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation Bar */}
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
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#86BC25]" />
              <span>Configure Proposal Draft</span>
            </h1>
            <p className="text-xs text-slate-500 font-mono">
              Step 1: Review Tender Context & Configure LLM Draft Parameters
            </p>
          </div>
        </div>

        {/* Opportunity Selector Dropdown */}
        <div className="flex items-center gap-2 bg-white p-1.5 rounded-md border border-slate-200">
          <label className="text-xs font-bold text-slate-700 font-mono pl-1">
            Target Tender:
          </label>
          <select
            value={selectedOppId}
            onChange={(e) => setSelectedOppId(e.target.value)}
            disabled={isGenerating}
            className="text-xs font-sans bg-[#F5F6F7] border border-slate-200 rounded px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-[#86BC25] max-w-xs"
          >
            {opportunities.map((opp) => (
              <option key={opp.id} value={opp.id}>
                [{opp.externalId}] {opp.title.substring(0, 45)}... ({opp.decision})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main 3-Column Workspace Grid */}
      {currentOpportunity ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Column 1: Tender Summary */}
          <div className="space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
              1. Tender Information
            </h2>
            <TenderSummary
              opportunity={currentOpportunity}
              onViewOpportunity={() => onNavigateToOpportunity(currentOpportunity.id)}
            />
          </div>

          {/* Column 2: Extracted Requirements */}
          <div className="space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
              2. Tender Requirements
            </h2>
            <RequirementList opportunity={currentOpportunity} />
          </div>

          {/* Column 3: Configuration & Trigger Form */}
          <div className="space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-mono">
              3. Configure Proposal
            </h2>
            <ProposalConfiguration
              initialTitle={`Technical Proposal: ${currentOpportunity.title}`}
              companyProfile={companyProfile}
              onSubmit={handleGenerateProposal}
              isGenerating={isGenerating}
              disabled={isNotFit}
            />
          </div>
        </div>
      ) : (
        <div className="p-12 text-center bg-white rounded-lg border border-slate-200">
          <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
          <p className="text-sm font-bold text-slate-800">No Opportunity Selected</p>
          <p className="text-xs text-slate-500 mt-1">
            Select a tender opportunity from the top dropdown or navigate from the Opportunities page.
          </p>
        </div>
      )}

      {generationError && (
        <div className="p-3 text-sm bg-red-50 border border-red-200 text-red-800 rounded-md">
          {generationError}
        </div>
      )}

      {/* Generation Progress Modal */}
      {isGenerating && (
        <GenerationProgress
          currentStage={generationStage}
          progressPercent={progressPercent}
        />
      )}
    </div>
  );
};
