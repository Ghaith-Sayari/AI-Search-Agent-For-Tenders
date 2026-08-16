import {
  Proposal,
  CreateProposalPayload,
  ProposalSection,
  ProposalQualityMetrics,
} from '../types/proposal';
import { mockProposals } from '../mocks/proposalMockData';

// In-memory store for frontend mock persistence
let localProposals: Proposal[] = [...mockProposals];

export const proposalService = {
  /**
   * GET /v1/proposals
   * Fetch list of all created proposals
   */
  async getProposals(): Promise<Proposal[]> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return [...localProposals];
  },

  /**
   * GET /v1/proposals/{proposal_id}
   * Fetch single proposal details
   */
  async getProposalById(proposalId: string): Promise<Proposal | null> {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const found = localProposals.find((p) => p.id === proposalId);
    return found ? { ...found } : null;
  },

  /**
   * POST /v1/proposals/{opportunity_id}/generate
   * Creates draft proposal container & executes multi-step AI draft generation pipeline
   */
  async generateProposal(
    payload: CreateProposalPayload,
    onProgress?: (stage: string, progressPercent: number) => void
  ): Promise<Proposal> {
    const id = `PROP-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;

    const stages = [
      { name: 'Preparing tender information', progress: 15 },
      { name: 'Preparing opportunity analysis', progress: 35 },
      { name: 'Preparing company profile', progress: 55 },
      { name: 'Generating proposal sections', progress: 78 },
      { name: 'Validating draft', progress: 92 },
      { name: 'Proposal ready', progress: 100 },
    ];

    for (const stg of stages) {
      if (onProgress) {
        onProgress(stg.name, stg.progress);
      }
      await new Promise((resolve) => setTimeout(resolve, 350));
    }

    const defaultSections: ProposalSection[] = [
      {
        id: 'sec-exec',
        title: 'Executive Summary',
        content: `Deloitte is pleased to present this ${payload.proposalType} in response to the tender requirements. As a recognized market leader in enterprise consulting and public sector transformation, we bring a proven delivery track record, deep domain expertise, and a zero-compromise approach to quality, security, and compliance.\n\nOur tailored approach is designed to achieve all project objectives efficiently, mitigate operational risks, and deliver sustainable value for the Contracting Authority.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-reqs',
        title: 'Understanding of Requirements',
        content: `Based on a comprehensive review of the tender documentation and requirements analysis, the Contracting Authority requires a secure, high-availability solution. Deloitte has structured our delivery framework around three primary pillars:\n1. Strict compliance with regulatory standards and client governance rules.\n2. Agile execution backed by robust risk management protocols.\n3. Long-term operational sustainability and seamless knowledge transfer.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-company',
        title: 'Company Profile & Reference Credentials',
        content: `Deloitte brings extensive local and global experience in delivering mission-critical projects for public sector and enterprise clients.\n\nCore Credentials:\n- Global network of certified technical architects and subject matter experts.\n- Standardized quality frameworks aligned with ISO 9001, ISO 27001, and SOC 2 Type II.\n- Proven delivery track record across government ministries, multilateral agencies, and blue-chip enterprises.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-approach',
        title: 'Proposed Approach & Methodology',
        content: `Our proposed execution methodology follows Deloitte's Industry-Proven Project Lifecycle, designed to maintain speed without sacrificing control:\n\n- Discovery & Alignment Phase: Blueprint confirmation, security baselining, and stakeholder alignment.\n- Execution & Build Phase: Iterative development, continuous testing, and quality assurance.\n- Deployment & Handover Phase: Staged rollout, user training, and post-implementation support.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-tech',
        title: 'Technical Architecture & Solution Design',
        content: `The proposed architecture emphasizes security, scalable throughput, and high availability:\n\n- Modular Component Layer: Isolated microservices architecture with encrypted API channels.\n- Data Protection: End-to-end encryption for data in transit and at rest.\n- Governance & Compliance: Continuous security telemetry and automated audit logs.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-[#86BC25]',
        title: 'Project Plan & Implementation Schedule',
        content: `The execution timeline is structured across structured milestones over the contract duration:\n- Milestone 1: Project Charter & Technical Architecture Sign-off (Month 1)\n- Milestone 2: Pilot Deployment & Security Penetration Testing (Month 3)\n- Milestone 3: Full System Rollout & User Acceptance Testing (Month 6)\n- Milestone 4: Operational Handover & SLA Support Initiation (Month 8)`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-team',
        title: 'Team Structure & Key Personnel',
        content: `The engagement will be directed by Senior Deloitte Partners, supported by dedicated Lead Architects, Delivery Managers, and Certified Engineers. Detailed CVs and technical certifications are attached in Appendix A.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-deliv',
        title: 'Deliverables & SLAs',
        content: `Deliverables include:\n1. Solution Architecture Blueprint & Technical Specification\n2. Security Governance & Compliance Playbook\n3. System Integration Source Code & Automated Deployment Scripts\n4. Staff Training Curriculum & Handover Documentation`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-qa',
        title: 'Quality Assurance & Risk Management',
        content: `Quality management adheres strictly to Deloitte Quality Assurance Standards. Risk mitigation protocols cover technical dependencies, change management, cybersecurity controls, and SLA compliance monitoring.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
      {
        id: 'sec-[#26890D]',
        title: 'Conclusion',
        content: `Deloitte offers an unparalleled combination of domain leadership, technical rigor, and public-sector experience. We are fully prepared to mobilize immediately upon award to ensure successful project execution.`,
        status: 'GENERATED',
        lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
      },
    ];

    const newProposal: Proposal = {
      id,
      opportunityId: payload.opportunityId,
      opportunityTitle: payload.proposalTitle.replace('Technical Proposal: ', ''),
      country: 'European Union',
      source: 'TED / Public Procurement',
      deadline: '2026-09-30',
      overallScore: 90,
      decision: 'GOOD_FIT',
      confidence: 94,
      status: 'READY_FOR_REVIEW', // Requirement 16: Initially MUST be READY_FOR_REVIEW
      createdAt: new Date().toISOString().replace('T', ' ').substring(0, 16),
      updatedAt: new Date().toISOString().replace('T', ' ').substring(0, 16),
      config: {
        title: payload.proposalTitle,
        companyProfileId: payload.companyProfileId,
        companyProfileName: payload.companyProfileName,
        language: payload.language,
        proposalType: payload.proposalType,
        tone: payload.tone,
        additionalInstructions: payload.additionalInstructions || '',
      },
      sections: defaultSections,
      qualityMetrics: {
        tenderAlignment: 92,
        requirementCoverage: 89,
        companyCapabilityAlignment: 94,
        completeness: 90,
        missingInformation: [
          'Key team personnel CV approvals pending',
          'Specific client reference contacts confirmation needed',
          'Local jurisdiction tax registration compliance verification',
        ],
        aiConfidence: 'High',
      },
      requirementsSummary: {
        keyRequirements: [
          'Demonstrated expertise in enterprise technology implementation',
          'Compliance with local and regional data protection regulations',
          '24/7 technical support and sub-1 hour response SLA for critical incidents',
        ],
        eligibilityRequirements: [
          'Minimum 3 years active market operations',
          'ISO 27001 or equivalent cybersecurity certification',
        ],
        deliverables: [
          'Technical Architecture Specification',
          'Implementation & Integration Source Code',
          'Operational SLA Support Manual',
        ],
        evaluationCriteria: [
          'Technical Merit & Solution Design (45%)',
          'Implementation Methodology & Risk Management (35%)',
          'Team Qualifications & Experience (20%)',
        ],
        importantDates: {
          submissionDeadline: '2026-09-30 17:00 CET',
          clarificationDeadline: '2026-09-15 12:00 CET',
        },
      },
    };

    localProposals = [newProposal, ...localProposals];
    return newProposal;
  },

  /**
   * PATCH /v1/proposals/{proposal_id}
   * Update proposal sections or metadata
   */
  async updateProposal(proposalId: string, updates: Partial<Proposal>): Promise<Proposal> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    const index = localProposals.findIndex((p) => p.id === proposalId);
    if (index === -1) {
      throw new Error(`Proposal ${proposalId} not found`);
    }

    const updated: Proposal = {
      ...localProposals[index],
      ...updates,
      updatedAt: new Date().toISOString().replace('T', ' ').substring(0, 16),
    };

    localProposals[index] = updated;
    return updated;
  },

  /**
   * POST /v1/proposals/{proposal_id}/sections/{section_id}/regenerate
   * Regenerate, improve, shorten, or expand a single specific section
   */
  async regenerateSection(
    proposalId: string,
    sectionId: string,
    action: 'Regenerate' | 'Improve' | 'Shorten' | 'Expand'
  ): Promise<ProposalSection> {
    await new Promise((resolve) => setTimeout(resolve, 600));

    const proposal = localProposals.find((p) => p.id === proposalId);
    if (!proposal) throw new Error(`Proposal ${proposalId} not found`);

    const section = proposal.sections.find((s) => s.id === sectionId);
    if (!section) throw new Error(`Section ${sectionId} not found`);

    let newContent = section.content;

    if (action === 'Regenerate') {
      newContent = `${section.content}\n\n[AI Refined Section]: Deloitte's comprehensive framework integrates cutting-edge security, automated governance, and robust monitoring to guarantee complete operational compliance with all tender specifications.`;
    } else if (action === 'Improve') {
      newContent = `[Enhanced Strategy]: ${section.content}\n\nKey Strategic Advantage: Our proven governance protocols ensure zero operational disruption during transition phases.`;
    } else if (action === 'Shorten') {
      newContent = section.content.split('\n')[0] || section.content;
    } else if (action === 'Expand') {
      newContent = `${section.content}\n\nDetailed Specification Supplement:\n1. Scalability: Auto-scaling infrastructure handling up to 100k concurrent requests.\n2. High Availability: 99.99% SLA uptime guarantee across multi-region clusters.\n3. Governance: Real-time telemetry dashboard with automated incident alerting.`;
    }

    const updatedSection: ProposalSection = {
      ...section,
      content: newContent,
      status: 'GENERATED',
      lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 16),
    };

    // Update in local store
    proposal.sections = proposal.sections.map((s) => (s.id === sectionId ? updatedSection : s));
    return updatedSection;
  },

  /**
   * GET /v1/proposals/{proposal_id}/quality
   * Get quality metrics for proposal
   */
  async getProposalQuality(proposalId: string): Promise<ProposalQualityMetrics> {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const proposal = localProposals.find((p) => p.id === proposalId);
    if (!proposal) {
      return {
        tenderAlignment: 85,
        requirementCoverage: 80,
        companyCapabilityAlignment: 90,
        completeness: 85,
        missingInformation: ['Key reference details missing'],
        aiConfidence: 'Medium',
      };
    }
    return proposal.qualityMetrics;
  },

  /**
   * POST /v1/proposals/{proposal_id}/export
   * Export proposal in PDF, DOCX, or Markdown format
   */
  async exportProposal(
    proposalId: string,
    format: 'pdf' | 'docx' | 'markdown'
  ): Promise<{ fileName: string; downloadUrl: string }> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    const proposal = localProposals.find((p) => p.id === proposalId);

    if (proposal) {
      proposal.status = 'EXPORTED';
    }

    const fileName = `Proposal_${proposalId}_${new Date().toISOString().slice(0, 10)}.${format}`;
    return {
      fileName,
      downloadUrl: `#export-${fileName}`,
    };
  },
};
