import { DecisionStatus } from './index';

export type ProposalStatus =
  | 'DRAFT'
  | 'GENERATING'
  | 'READY_FOR_REVIEW'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'EXPORTED'
  | 'FAILED';

export type ProposalType = 'Technical Proposal' | 'Commercial Proposal' | 'Full Proposal';

export type ProposalTone = 'Professional' | 'Formal' | 'Executive' | 'Technical';

export type ProposalLanguage = 'English' | 'French' | 'Arabic';

export interface ProposalSection {
  id: string;
  title: string;
  content: string;
  status: 'GENERATED' | 'EDITED' | 'REGENERATING';
  lastUpdated: string;
}

export interface ProposalQualityMetrics {
  tenderAlignment: number; // 0-100%
  requirementCoverage: number; // 0-100%
  companyCapabilityAlignment: number; // 0-100%
  completeness?: number; // 0-100%
  missingInformation: string[];
  aiConfidence: 'High' | 'Medium' | 'Low';
}

export interface ProposalConfig {
  title: string;
  companyProfileId: string;
  companyProfileName: string;
  language: ProposalLanguage;
  proposalType: ProposalType;
  tone: ProposalTone;
  additionalInstructions: string;
}

export interface RequirementsSummary {
  keyRequirements: string[];
  eligibilityRequirements: string[];
  deliverables: string[];
  evaluationCriteria?: string[];
  importantDates: {
    submissionDeadline: string;
    clarificationDeadline: string;
  };
}

export interface Proposal {
  id: string;
  opportunityId: string;
  opportunityTitle: string;
  country: string;
  source: string;
  deadline: string;
  overallScore: number;
  decision: DecisionStatus;
  confidence?: number;
  status: ProposalStatus;
  createdAt: string;
  updatedAt: string;
  config: ProposalConfig;
  sections: ProposalSection[];
  qualityMetrics: ProposalQualityMetrics;
  requirementsSummary: RequirementsSummary;
}

export interface CreateProposalPayload {
  opportunityId: string;
  proposalTitle: string;
  companyProfileId: string;
  companyProfileName: string;
  language: ProposalLanguage;
  proposalType: ProposalType;
  tone: ProposalTone;
  additionalInstructions?: string;
}
