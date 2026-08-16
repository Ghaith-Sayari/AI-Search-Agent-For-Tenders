import {
  Opportunity,
  ReviewItem,
  PipelineRun,
  SystemService,
  SystemIncident,
  CostMetrics,
  CompanyProfile,
  DecisionStatus,
  Proposal,
  CreateProposalPayload,
  ProposalSection,
  ProposalQualityMetrics,
} from '../types';

import {
  INITIAL_COMPANY_PROFILE,
  INITIAL_OPPORTUNITIES,
  INITIAL_REVIEWS,
  INITIAL_RUNS,
  INITIAL_SYSTEM_SERVICES,
  INITIAL_SYSTEM_INCIDENTS,
  INITIAL_COST_METRICS,
  INITIAL_PROPOSALS,
} from './mockData';

// Persistent in-memory reactive mock storage
let opportunitiesStore: Opportunity[] = [...INITIAL_OPPORTUNITIES];
let reviewsStore: ReviewItem[] = [...INITIAL_REVIEWS];
let runsStore: PipelineRun[] = [...INITIAL_RUNS];
let systemServicesStore: SystemService[] = [...INITIAL_SYSTEM_SERVICES];
let incidentsStore: SystemIncident[] = [...INITIAL_SYSTEM_INCIDENTS];
let costMetricsStore: CostMetrics = { ...INITIAL_COST_METRICS };
let companyProfileStore: CompanyProfile = { ...INITIAL_COMPANY_PROFILE };
let proposalsStore: Proposal[] = [...INITIAL_PROPOSALS];

export interface FetchOpportunitiesParams {
  search?: string;
  country?: string;
  source?: string;
  decision?: string;
  minScore?: number;
  maxScore?: number;
  sortBy?: 'score' | 'deadline' | 'published';
  sortOrder?: 'asc' | 'desc';
}

export const apiService = {
  // Opportunities REST API Abstraction: GET /v1/opportunities
  async getOpportunities(params?: FetchOpportunitiesParams): Promise<Opportunity[]> {
    await new Promise((resolve) => setTimeout(resolve, 150)); // simulate slight network latency
    let result = [...opportunitiesStore];

    if (params?.search) {
      const q = params.search.toLowerCase();
      result = result.filter(
        (o) =>
          o.title.toLowerCase().includes(q) ||
          o.description.toLowerCase().includes(q) ||
          o.sector.toLowerCase().includes(q) ||
          o.externalId.toLowerCase().includes(q)
      );
    }

    if (params?.country && params.country !== 'ALL') {
      result = result.filter((o) => o.country === params.country || o.countryCode === params.country);
    }

    if (params?.source && params.source !== 'ALL') {
      result = result.filter((o) => o.source.toLowerCase().includes(params.source!.toLowerCase()));
    }

    if (params?.decision && params.decision !== 'ALL') {
      result = result.filter((o) => o.decision === params.decision);
    }

    if (params?.minScore !== undefined) {
      result = result.filter((o) => o.overallScore >= params.minScore!);
    }

    if (params?.maxScore !== undefined) {
      result = result.filter((o) => o.overallScore <= params.maxScore!);
    }

    if (params?.sortBy) {
      result.sort((a, b) => {
        let valA: number | string = 0;
        let valB: number | string = 0;
        if (params.sortBy === 'score') {
          valA = a.overallScore;
          valB = b.overallScore;
        } else if (params.sortBy === 'deadline') {
          valA = a.deadline;
          valB = b.deadline;
        } else if (params.sortBy === 'published') {
          valA = a.publishedDate;
          valB = b.publishedDate;
        }
        if (valA < valB) return params.sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return params.sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  },

  // GET /v1/opportunities/:opportunity_id
  async getOpportunityById(id: string): Promise<Opportunity | null> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return opportunitiesStore.find((o) => o.id === id) || null;
  },

  // POST /v1/opportunities/:opportunity_id/analyze
  async runOpportunityAnalysis(id: string): Promise<Opportunity> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    const index = opportunitiesStore.findIndex((o) => o.id === id);
    if (index === -1) throw new Error('Opportunity not found');

    const updated = {
      ...opportunitiesStore[index],
      lastAnalyzedAt: new Date().toISOString().replace('T', ' ').substring(0, 19),
      analysisStatus: 'COMPLETED' as const,
    };
    opportunitiesStore[index] = updated;
    return updated;
  },

  // GET /v1/analyses
  async getAnalyses(params?: FetchOpportunitiesParams): Promise<Opportunity[]> {
    return this.getOpportunities(params);
  },

  // GET /v1/reviews
  async getReviews(): Promise<ReviewItem[]> {
    await new Promise((resolve) => setTimeout(resolve, 120));
    return [...reviewsStore];
  },

  // POST /v1/reviews/:review_id/resolve
  async resolveReview(
    reviewId: string,
    action: 'APPROVE' | 'REJECT' | 'SEND_BACK',
    overrideReason: string,
    actorName: string = 'Current User'
  ): Promise<ReviewItem> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    const index = reviewsStore.findIndex((r) => r.id === reviewId);
    if (index === -1) throw new Error('Review item not found');

    const current = reviewsStore[index];
    const statusMap = {
      APPROVE: 'RESOLVED_APPROVED' as const,
      REJECT: 'RESOLVED_REJECTED' as const,
      SEND_BACK: 'RESOLVED_SENT_BACK' as const,
    };

    const newStatus = statusMap[action];
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);

    const updatedReview: ReviewItem = {
      ...current,
      status: newStatus,
      resolvedAt: timestamp,
      resolvedBy: actorName,
      overrideReason,
      auditTrail: [
        ...current.auditTrail,
        {
          timestamp,
          action: `Human Resolution: ${action}`,
          actor: actorName,
          notes: `Reason provided: ${overrideReason}`,
        },
      ],
    };

    reviewsStore[index] = updatedReview;

    // Update corresponding opportunity decision in store if approved or rejected
    const oppIndex = opportunitiesStore.findIndex((o) => o.id === current.opportunityId);
    if (oppIndex !== -1) {
      let newDecision: DecisionStatus = opportunitiesStore[oppIndex].decision;
      if (action === 'APPROVE') newDecision = 'GOOD_FIT';
      if (action === 'REJECT') newDecision = 'NOT_FIT';
      opportunitiesStore[oppIndex] = {
        ...opportunitiesStore[oppIndex],
        decision: newDecision,
      };
    }

    return updatedReview;
  },

  // GET /v1/runs
  async getPipelineRuns(): Promise<PipelineRun[]> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return [...runsStore];
  },

  // GET /v1/runs/:run_id
  async getRunById(id: string): Promise<PipelineRun | null> {
    await new Promise((resolve) => setTimeout(resolve, 80));
    return runsStore.find((r) => r.id === id) || null;
  },

  // POST /v1/runs
  async triggerPipelineRun(triggerName: string = 'Manual Dashboard Trigger'): Promise<PipelineRun> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const newId = `run-${Date.now().toString().slice(-6)}`;
    const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);

    const newRun: PipelineRun = {
      id: newId,
      triggeredBy: triggerName,
      startedAt: nowStr,
      durationSeconds: 15,
      currentStage: 'INGESTION',
      processedCount: 18,
      approvedCount: 3,
      reviewCount: 1,
      failedCount: 0,
      llmCallsCount: 22,
      status: 'RUNNING',
      stages: [
        { stage: 'INGESTION', label: 'Tender Ingestion', status: 'RUNNING', durationSeconds: 5, processedCount: 18, errorsCount: 0, retryCount: 0, details: "Fetching active sources..." },
        { stage: 'NORMALIZATION', label: 'Document Normalization', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
        { stage: 'GATEKEEPER', label: 'AI Gatekeeper Qualification', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
        { stage: 'PRODUCTION', label: 'Data Enrichment', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
        { stage: 'OPPORTUNITY_ANALYSIS', label: 'AI Fit Analysis & Scoring', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
        { stage: 'REVIEW', label: 'Review Queue Routing', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
        { stage: 'COMPLETED', label: 'Run Completion', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
      ],
    };

    runsStore = [newRun, ...runsStore];
    return newRun;
  },

  // GET /v1/agents/status
  async getSystemHealth(): Promise<{ services: SystemService[]; incidents: SystemIncident[] }> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      services: [...systemServicesStore],
      incidents: [...incidentsStore],
    };
  },

  // GET /v1/metrics/cost
  async getCostMetrics(): Promise<CostMetrics> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return { ...costMetricsStore };
  },

  // Company Profile
  async getCompanyProfile(): Promise<CompanyProfile> {
    await new Promise((resolve) => setTimeout(resolve, 80));
    return { ...companyProfileStore };
  },

  async updateCompanyProfile(profile: CompanyProfile): Promise<CompanyProfile> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    companyProfileStore = { ...profile };
    return { ...companyProfileStore };
  },

  // Proposals REST API Abstraction
  // GET /v1/proposals
  async getProposals(): Promise<Proposal[]> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return [...proposalsStore];
  },

  // GET /v1/proposals/:proposal_id
  async getProposalById(id: string): Promise<Proposal | null> {
    await new Promise((resolve) => setTimeout(resolve, 80));
    return proposalsStore.find((p) => p.id === id) || null;
  },

  // POST /v1/proposals
  async createProposal(payload: CreateProposalPayload): Promise<Proposal> {
    await new Promise((resolve) => setTimeout(resolve, 200));

    const opportunity = opportunitiesStore.find((o) => o.id === payload.opportunityId);
    if (!opportunity) throw new Error('Target opportunity not found');

    const newId = `prop-${Date.now().toString().slice(-6)}`;
    const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);

    const defaultSections: ProposalSection[] = [
      { id: 'sec-exec', title: 'Executive Summary', content: `Executive summary draft for ${opportunity.title}...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-req', title: 'Understanding of Requirements', content: `Analysis of key specifications for ${opportunity.title}...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-comp', title: 'Company Profile', content: `Profile overview for ${payload.companyProfileName}...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-approach', title: 'Proposed Approach', content: `Proposed technical and strategic methodology...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-method', title: 'Methodology', content: `Deloitte Agile Public Sector delivery framework...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-tech', title: 'Technical Solution', content: `Architecture and technological stack specifications...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-plan', title: 'Project Plan', content: `Milestones and delivery schedule...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-team', title: 'Team & Expertise', content: `Personnel allocation and subject matter expert qualifications...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-deliv', title: 'Deliverables', content: `Formal scope artifacts and acceptance documentation...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-qa', title: 'Quality Assurance', content: `Quality control protocols, CI/CD testing, and oversight...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-risk', title: 'Risk Management', content: `Risk identification matrix and mitigation strategies...`, status: 'GENERATED', lastUpdated: nowStr },
      { id: 'sec-concl', title: 'Conclusion', content: `Concluding statement and value proposition...`, status: 'GENERATED', lastUpdated: nowStr },
    ];

    const newProposal: Proposal = {
      id: newId,
      opportunityId: opportunity.id,
      opportunityTitle: opportunity.title,
      country: opportunity.country,
      source: opportunity.source,
      deadline: opportunity.deadline,
      overallScore: opportunity.overallScore,
      decision: opportunity.decision,
      status: 'DRAFT',
      createdAt: nowStr,
      updatedAt: nowStr,
      config: {
        title: payload.proposalTitle || `Proposal: ${opportunity.title}`,
        companyProfileId: payload.companyProfileId,
        companyProfileName: payload.companyProfileName,
        language: payload.language,
        proposalType: payload.proposalType,
        tone: payload.tone,
        additionalInstructions: payload.additionalInstructions || '',
      },
      qualityMetrics: {
        tenderAlignment: Math.min(98, opportunity.overallScore + 2),
        requirementCoverage: 88,
        companyCapabilityAlignment: 92,
        missingInformation: [
          'Detailed pricing rate schedule',
          'Specific localized partner SLAs',
          'Named CV references for secondary roles'
        ],
        aiConfidence: opportunity.overallScore >= 85 ? 'High' : 'Medium',
      },
      requirementsSummary: {
        keyRequirements: opportunity.requirements.length > 0 ? opportunity.requirements : ['Information not available'],
        eligibilityRequirements: opportunity.eligibilityCriteria.length > 0 ? opportunity.eligibilityCriteria : ['Information not available'],
        deliverables: [
          'Project Charter & Inception Document',
          'Architecture & Security Blueprint',
          'Core Solution Release Package',
          'Operations & Handover Documentation'
        ],
        importantDates: {
          submissionDeadline: opportunity.deadline,
          clarificationDeadline: 'Information not available'
        }
      },
      sections: defaultSections,
    };

    proposalsStore = [newProposal, ...proposalsStore];
    return newProposal;
  },

  // POST /v1/proposals/:proposal_id/generate
  async generateProposal(
    proposalId: string,
    onStageUpdate?: (stageName: string, progress: number) => void
  ): Promise<Proposal> {
    const index = proposalsStore.findIndex((p) => p.id === proposalId);
    if (index === -1) throw new Error('Proposal not found');

    const current = proposalsStore[index];
    proposalsStore[index] = { ...current, status: 'GENERATING' };

    const stages = [
      { name: 'Preparing tender information', progress: 15 },
      { name: 'Preparing opportunity analysis', progress: 35 },
      { name: 'Preparing company profile', progress: 50 },
      { name: 'Generating proposal sections', progress: 75 },
      { name: 'Validating draft', progress: 90 },
      { name: 'Draft ready', progress: 100 },
    ];

    for (const stage of stages) {
      if (onStageUpdate) {
        onStageUpdate(stage.name, stage.progress);
      }
      await new Promise((resolve) => setTimeout(resolve, 350));
    }

    const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);

    // Populate tailored high quality sections
    const generatedSections: ProposalSection[] = [
      {
        id: 'sec-exec',
        title: 'Executive Summary',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Deloitte Digital & Advisory EMEA submits this ${current.config.proposalType} for "${current.opportunityTitle}".\n\nOur proposal aligns directly with the requirements specified by ${current.source}. Utilizing ${current.config.companyProfileName}'s deep public sector capabilities, our solution guarantees full technical compliance, robust risk mitigation, and seamless project execution tailored for ${current.country}.`
      },
      {
        id: 'sec-req',
        title: 'Understanding of Requirements',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `We have thoroughly analyzed the scope for "${current.opportunityTitle}".\n\nKey Requirements Highlighted:\n${current.requirementsSummary.keyRequirements.map((r, i) => `${i + 1}. ${r}`).join('\n')}\n\nOur team brings verified experience fulfilling each specific operational constraint.`
      },
      {
        id: 'sec-comp',
        title: 'Company Profile',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `${current.config.companyProfileName} is a global leader in management consulting and cloud transformation.\n\nCore Service Lines:\n• Enterprise Architecture & AI Integration\n• Cloud Engineering & Sovereign Infrastructure\n• Program Management & Governance\n• ISO 27001 & Cyber Security Operations`
      },
      {
        id: 'sec-approach',
        title: 'Proposed Approach',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Our proposed approach is structured with a ${current.config.tone.toLowerCase()} focus on high availability, security by design, and rapid value delivery.\n\nKey Pillars:\n1. Sovereign Compliance: Absolute adherence to European data sovereignty frameworks.\n2. Modular Component Design: Containerized microservices to ensure future adaptability.\n3. Transparent Governance: Real-time dashboard tracking for project stakeholders.`
      },
      {
        id: 'sec-method',
        title: 'Methodology',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Delivery will follow the Deloitte Agile Public Sector (DAPS) Framework:\n\n• Sprint 1–4: Inception, Security Concept & Blueprint Signoff\n• Sprint 5–12: Core Engineering & Modular Component Integration\n• Sprint 13–18: Acceptance Testing, User Training & Go-Live Preparation`
      },
      {
        id: 'sec-tech',
        title: 'Technical Solution',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `The Technical Solution leverages open standards and cloud-native architecture.\n\nTech Stack Overview:\n• Infrastructure: Sovereign Cloud Kubernetes Cluster (ISO 27001 / BSI C5 certified)\n• Middleware: High-throughput event streaming & REST API Gateway\n• AI & Analytics: Gemini Flash model API backend proxied through server-side rate limiters`
      },
      {
        id: 'sec-plan',
        title: 'Project Plan',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Milestone Schedule:\n• Month 1: Project Kickoff & Stakeholder Alignment\n• Month 3: Technical Architecture Approval\n• Month 6: Beta Release & Initial User Acceptance Testing\n• Month 9: Full Production Cutover & Handover`
      },
      {
        id: 'sec-team',
        title: 'Team & Expertise',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Project Governance Team:\n• Lead Partner & Senior Executive Sponsor\n• Principal Enterprise Solutions Architect\n• Lead Security & Compliance Specialist\n• Senior Project Manager (PMP / PRINCE2 certified)`
      },
      {
        id: 'sec-deliv',
        title: 'Deliverables',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Formal Deliverable List:\n${current.requirementsSummary.deliverables.map((d, i) => `• Deliverable ${i + 1}: ${d}`).join('\n')}`
      },
      {
        id: 'sec-qa',
        title: "Quality Assurance",
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Quality Assurance includes 100% peer code reviews, automated CI/CD static security scanning (SAST), dynamic penetration testing, and independent quality audits before each milestone approval.`
      },
      {
        id: 'sec-risk',
        title: 'Risk Management',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `Risk Mitigation Matrix:\n• Sub-contractor & SLA Risk: Mitigated via binding partner consortium agreements.\n• Technical Complexity Risk: Mitigated via early prototyping and automated test suites.`
      },
      {
        id: 'sec-concl',
        title: 'Conclusion',
        status: 'GENERATED',
        lastUpdated: nowStr,
        content: `In conclusion, ${current.config.companyProfileName} possesses the technical expertise, industry reputation, and project delivery maturity required to guarantee success for ${current.opportunityTitle}.`
      }
    ];

    const updatedProposal: Proposal = {
      ...proposalsStore[index],
      status: 'READY_FOR_REVIEW',
      updatedAt: nowStr,
      sections: generatedSections,
    };

    proposalsStore[index] = updatedProposal;
    return updatedProposal;
  },

  // PATCH /v1/proposals/:proposal_id
  async updateProposal(proposalId: string, updates: Partial<Proposal>): Promise<Proposal> {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const index = proposalsStore.findIndex((p) => p.id === proposalId);
    if (index === -1) throw new Error('Proposal not found');

    const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const updated: Proposal = {
      ...proposalsStore[index],
      ...updates,
      updatedAt: nowStr,
    };

    proposalsStore[index] = updated;
    return updated;
  },

  // POST /v1/proposals/:proposal_id/sections/:section_id/regenerate
  async regenerateSection(
    proposalId: string,
    sectionId: string,
    action: 'Regenerate' | 'Improve' | 'Shorten' | 'Expand'
  ): Promise<ProposalSection> {
    await new Promise((resolve) => setTimeout(resolve, 600)); // simulate section LLM call
    const proposal = proposalsStore.find((p) => p.id === proposalId);
    if (!proposal) throw new Error('Proposal not found');

    const section = proposal.sections.find((s) => s.id === sectionId);
    if (!section) throw new Error('Section not found');

    const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19);

    let newContent = section.content;
    if (action === 'Shorten') {
      newContent = section.content
        .split('\n')
        .filter((line) => line.trim().length > 0)
        .slice(0, 3)
        .join('\n');
      newContent += '\n\n[Section concise summary updated via AI]';
    } else if (action === 'Expand') {
      newContent = section.content + `\n\nAdditional Comprehensive Detail (${action}):\nFurthermore, our team enforces continuous monitoring and automated operational telemetry across every deployment stage to guarantee resilience, compliance, and strategic alignment with tender objectives.`;
    } else if (action === 'Improve') {
      newContent = section.content.replace(/Deloitte/g, 'Deloitte Digital & Advisory (EMEA Public Sector)') + `\n\n[Polished with enhanced executive terminology & compliance precision]`;
    } else {
      newContent = `Regenerated Section Content (${section.title}):\n\nThis section has been regenerated using the latest context from tender "${proposal.opportunityTitle}", company profile "${proposal.config.companyProfileName}", and specific guidelines (${proposal.config.additionalInstructions || 'Standard guidelines'}). All technical points are tailored to ${proposal.country} public sector standards.`;
    }

    const updatedSection: ProposalSection = {
      ...section,
      content: newContent,
      status: 'EDITED',
      lastUpdated: nowStr,
    };

    // Update in store
    const propIndex = proposalsStore.findIndex((p) => p.id === proposalId);
    if (propIndex !== -1) {
      const updatedSections = proposalsStore[propIndex].sections.map((s) =>
        s.id === sectionId ? updatedSection : s
      );
      proposalsStore[propIndex] = {
        ...proposalsStore[propIndex],
        updatedAt: nowStr,
        sections: updatedSections,
      };
    }

    return updatedSection;
  },

  // GET /v1/proposals/:proposal_id/quality
  async getProposalQuality(proposalId: string): Promise<ProposalQualityMetrics> {
    await new Promise((resolve) => setTimeout(resolve, 80));
    const proposal = proposalsStore.find((p) => p.id === proposalId);
    if (!proposal) {
      return {
        tenderAlignment: 90,
        requirementCoverage: 85,
        companyCapabilityAlignment: 92,
        missingInformation: ['Team CVs not provided', 'Pricing schedule pending'],
        aiConfidence: 'High',
      };
    }
    return proposal.qualityMetrics;
  },

  // POST /v1/proposals/:proposal_id/export
  async exportProposal(proposalId: string, format: 'pdf' | 'docx' | 'markdown'): Promise<{ fileName: string; fileUrl: string }> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    const proposal = proposalsStore.find((p) => p.id === proposalId);
    const titleSlug = (proposal?.config.title || 'Proposal').toLowerCase().replace(/[^a-z0-9]/g, '_');
    const fileName = `${titleSlug}_draft.${format}`;

    // Mark status as EXPORTED if currently ready or in review
    if (proposal && (proposal.status === 'READY_FOR_REVIEW' || proposal.status === 'DRAFT')) {
      await this.updateProposal(proposalId, { status: 'EXPORTED' });
    }

    return {
      fileName,
      fileUrl: `#export-${format}-${proposalId}`,
    };
  },
};

