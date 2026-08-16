import {
  Proposal,
  CreateProposalPayload,
  ProposalSection,
  ProposalQualityMetrics,
} from '../types/proposal';
import { apiService } from './api';

export const proposalService = {
  /**
   * GET /v1/proposals
   */
  async getProposals(): Promise<Proposal[]> {
    return apiService.getProposals();
  },

  /**
   * GET /v1/proposals/{proposal_id}
   */
  async getProposalById(proposalId: string): Promise<Proposal | null> {
    return apiService.getProposalById(proposalId);
  },

  /**
   * Legacy frontend workflow helper:
   * 1) POST /v1/proposals (create draft)
   * 2) POST /v1/proposals/{id}/generate
   */
  async generateProposal(
    payload: CreateProposalPayload,
    onProgress?: (stage: string, progressPercent: number) => void
  ): Promise<Proposal> {
    const draft = await apiService.createProposal(payload);
    return apiService.generateProposal(draft.id, onProgress);
  },

  /**
   * PATCH /v1/proposals/{proposal_id}
   */
  async updateProposal(proposalId: string, updates: Partial<Proposal>): Promise<Proposal> {
    return apiService.updateProposal(proposalId, updates);
  },

  /**
   * POST /v1/proposals/{proposal_id}/sections/{section_id}/regenerate
   */
  async regenerateSection(
    proposalId: string,
    sectionId: string,
    action: 'Regenerate' | 'Improve' | 'Shorten' | 'Expand'
  ): Promise<ProposalSection> {
    return apiService.regenerateSection(proposalId, sectionId, action);
  },

  /**
   * GET /v1/proposals/{proposal_id}/quality
   */
  async getProposalQuality(proposalId: string): Promise<ProposalQualityMetrics> {
    return apiService.getProposalQuality(proposalId);
  },

  /**
   * POST /v1/proposals/{proposal_id}/export
   * Keeps backward-compatible `downloadUrl` alias.
   */
  async exportProposal(
    proposalId: string,
    format: 'pdf' | 'docx' | 'markdown'
  ): Promise<{ fileName: string; downloadUrl: string }> {
    const res = await apiService.exportProposal(proposalId, format);
    return {
      fileName: res.fileName,
      downloadUrl: res.fileUrl,
    };
  },
};
