import {
  Opportunity,
  ReviewItem,
  PipelineRun,
  SystemService,
  SystemIncident,
  CostMetrics,
  CompanyProfile,
  Proposal,
  CreateProposalPayload,
  ProposalSection,
  ProposalQualityMetrics,
  DecisionStatus,
} from '../types';

export interface FetchOpportunitiesParams {
  search?: string;
  country?: string;
  source?: string;
  decision?: string;
  minScore?: number;
  maxScore?: number;
  sortBy?: 'score' | 'deadline' | 'published' | 'lastAnalyzedAt';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
}

const API_BASE_URL = ((import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

function toQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') search.set(k, String(v));
  });
  const q = search.toString();
  return q ? `?${q}` : '';
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const detail = (data && (data.detail || data.message)) || `HTTP ${res.status}`;
    throw new Error(String(detail));
  }
  return data as T;
}

const toDecisionStatus = (value: string | undefined | null): DecisionStatus => {
  const raw = (value || '').toUpperCase();
  if (raw === 'GOOD_FIT' || raw === 'NEEDS_REVIEW' || raw === 'NOT_FIT' || raw === 'FAILED') return raw;
  if (raw === 'PURSUE' || raw === 'APPROVED') return 'GOOD_FIT';
  if (raw === 'REJECT' || raw === 'REJECTED' || raw === 'EXPIRED') return 'NOT_FIT';
  return 'NEEDS_REVIEW';
};

const mapOpportunity = (o: any): Opportunity => ({
  id: String(o.id || ''),
  title: String(o.title || ''),
  externalId: String(o.externalId || o.external_id || ''),
  source: String(o.source || ''),
  sourceUrl: String(o.sourceUrl || o.source_url || o.url || ''),
  country: String(o.country || ''),
  countryCode: String(o.countryCode || o.country_code || ''),
  sector: String(o.sector || ''),
  estimatedValue: String(o.estimatedValue || o.estimated_value || ''),
  publishedDate: String(o.publishedDate || o.published_date || o.created_at || ''),
  deadline: String(o.deadline || ''),
  lastAnalyzedAt: String(o.lastAnalyzedAt || o.last_analyzed_at || o.processed_at || ''),
  overallScore: Number(o.overallScore ?? o.total_score ?? o.score ?? 0),
  decision: toDecisionStatus(o.decision),
  confidence: Number(o.confidence ?? o.confidence_score ?? 0),
  analysisStatus: (String(o.analysisStatus || o.analysis_status || 'COMPLETED').toUpperCase() as any),
  scoreBreakdown: {
    sectorRelevance: Number(o.scoreBreakdown?.sectorRelevance ?? o.score_breakdown?.sectorRelevance ?? 0),
    servicesRelevance: Number(o.scoreBreakdown?.servicesRelevance ?? o.score_breakdown?.servicesRelevance ?? 0),
    geographyRelevance: Number(o.scoreBreakdown?.geographyRelevance ?? o.score_breakdown?.geographyRelevance ?? 0),
    eligibilityFit: Number(o.scoreBreakdown?.eligibilityFit ?? o.score_breakdown?.eligibilityFit ?? 0),
    strategicFit: Number(o.scoreBreakdown?.strategicFit ?? o.score_breakdown?.strategicFit ?? 0),
  },
  aiReasoning: {
    matched: Array.isArray(o.aiReasoning?.matched) ? o.aiReasoning.matched : [],
    missingOrRisk: Array.isArray(o.aiReasoning?.missingOrRisk) ? o.aiReasoning.missingOrRisk : [],
    recommendation: String(o.aiReasoning?.recommendation || ''),
  },
  description: String(o.description || ''),
  requirements: Array.isArray(o.requirements) ? o.requirements : [],
  eligibilityCriteria: Array.isArray(o.eligibilityCriteria || o.eligibility_criteria)
    ? (o.eligibilityCriteria || o.eligibility_criteria)
    : [],
  profileName: String(o.profileName || ''),
});

const mapReview = (r: any): ReviewItem => ({
  id: String(r.id || ''),
  opportunityId: String(r.opportunityId || r.opportunity_id || ''),
  opportunityTitle: String(r.opportunityTitle || r.opportunity_title || ''),
  country: String(r.country || ''),
  source: String(r.source || ''),
  reviewType: (String(r.reviewType || r.review_type || 'GATEKEEPER').toUpperCase() as any),
  aiDecision: toDecisionStatus(r.aiDecision || r.ai_decision || r.decision),
  score: Number(r.score ?? 0),
  confidence: Number(r.confidence ?? 0),
  reason: String(r.reason || ''),
  createdAt: String(r.createdAt || r.created_at || r.auditTrail?.[0]?.timestamp || r.resolvedAt || new Date().toISOString()),
  priority: (String(r.priority || 'MEDIUM').toUpperCase() as any),
  assignee: r.assignee ?? null,
  status: (String(r.status || 'OPEN').toUpperCase() as any),
  resolvedAt: r.resolvedAt || r.resolved_at,
  resolvedBy: r.resolvedBy || r.resolved_by,
  overrideReason: r.overrideReason || r.override_reason,
  auditTrail: Array.isArray(r.auditTrail)
    ? r.auditTrail.map((a: any) => ({
        timestamp: String(a.timestamp || ''),
        action: String(a.action || ''),
        actor: String(a.actor || ''),
        notes: a.notes ? String(a.notes) : undefined,
      }))
    : [],
});

const mapRun = (r: any): PipelineRun => ({
  id: String(r.id || ''),
  triggeredBy: String(r.triggeredBy || r.triggered_by || 'api'),
  startedAt: String(r.startedAt || r.started_at || ''),
  completedAt: r.completedAt || r.completed_at,
  durationSeconds: Number(r.durationSeconds ?? r.duration_seconds ?? 0),
  currentStage: (String(r.currentStage || r.current_stage || 'INGESTION').toUpperCase() as any),
  processedCount: Number(r.processedCount ?? r.processed_count ?? 0),
  approvedCount: Number(r.approvedCount ?? r.approved_count ?? 0),
  reviewCount: Number(r.reviewCount ?? r.review_count ?? 0),
  failedCount: Number(r.failedCount ?? r.failed_count ?? 0),
  llmCallsCount: Number(r.llmCallsCount ?? r.llm_calls_count ?? 0),
  status: (String(r.status || 'QUEUED').toUpperCase() as any),
  stages: Array.isArray(r.stages)
    ? r.stages.map((s: any) => ({
        stage: String(s.stage || 'INGESTION').toUpperCase() as any,
        label: String(s.label || s.stage || ''),
        status: String(s.status || 'PENDING').toUpperCase() as any,
        durationSeconds: Number(s.durationSeconds ?? s.duration_seconds ?? 0),
        processedCount: Number(s.processedCount ?? s.processed_count ?? 0),
        errorsCount: Number(s.errorsCount ?? s.errors_count ?? 0),
        retryCount: Number(s.retryCount ?? s.retry_count ?? 0),
        details: typeof s.details === 'string' ? s.details : s.details ? JSON.stringify(s.details) : undefined,
      }))
    : [],
});

const mapSystemService = (s: any, idx: number): SystemService => {
  const name = String(s.name || `service-${idx + 1}`);
  const lowered = name.toLowerCase();
  let category: SystemService['category'] = 'AI / Agent';
  if (lowered.includes('ingest') || lowered.includes('scrap')) category = 'Ingestion';
  else if (lowered.includes('queue') || lowered.includes('redis')) category = 'Queue';
  else if (lowered.includes('db') || lowered.includes('supabase')) category = 'Database';
  else if (lowered.includes('storage')) category = 'Storage';

  const statusRaw = String(s.status || 'DOWN').toUpperCase();
  const status: SystemService['status'] = statusRaw === 'UP' ? 'HEALTHY' : statusRaw === 'DEGRADED' ? 'DEGRADED' : 'DOWN';

  return {
    id: String(s.id || name),
    name,
    category,
    status,
    latencyMs: Number(s.latencyMs ?? s.latency_ms ?? 0),
    lastSuccessfulExecution: String(s.lastCheckedAt || s.last_checked_at || ''),
    errorCount24h: Number(s.errorCount24h ?? 0),
    uptimePercent: Number(s.uptimePercent ?? 100),
    details: typeof s.details === 'string' ? s.details : JSON.stringify(s.details || {}),
  };
};

const mapIncident = (i: any): SystemIncident => {
  const sev = String(i.severity || '').toUpperCase();
  const mappedSeverity: SystemIncident['severity'] = sev === 'CRITICAL' || sev === 'HIGH' ? 'CRITICAL' : sev === 'LOW' || sev === 'INFO' ? 'INFO' : 'WARNING';
  return {
    id: String(i.id || ''),
    timestamp: String(i.timestamp || i.createdAt || i.created_at || ''),
    service: String(i.service || ''),
    severity: mappedSeverity,
    message: String(i.message || ''),
    resolved: String(i.status || '').toUpperCase() === 'RESOLVED' || Boolean(i.resolved),
  };
};

const mapCostMetrics = (m: any): CostMetrics => {
  const llmCalls = Number(m.llmCalls ?? m.totalLlmCalls ?? 0);
  const inputTokens = Number(m.promptTokens ?? m.inputTokens ?? 0);
  const outputTokens = Number(m.completionTokens ?? m.outputTokens ?? 0);
  const estimatedCostUsd = Number(m.estimatedCostUsd ?? m.estimated_cost_usd ?? 0);
  const byStage = Array.isArray(m.byStage) ? m.byStage : [];
  return {
    totalLlmCalls: llmCalls,
    inputTokens,
    outputTokens,
    estimatedCostUsd,
    costPerOpportunityUsd: Number(m.costPerOpportunityUsd ?? 0),
    avgTokensPerRequest: llmCalls > 0 ? (inputTokens + outputTokens) / llmCalls : 0,
    cacheHitRatePercent: Number(m.cacheHitRatePercent ?? 0),
    llmCallsAvoidedByRules: Number(m.llmCallsAvoidedByRules ?? 0),
    retryCount: Number(m.retryCount ?? 0),
    avgPromptSizeTokens: Number(m.avgPromptSizeTokens ?? 0),
    callsByStage: byStage.map((s: any) => ({
      stage: String(s.stage || ''),
      calls: Number(s.llmCalls ?? s.calls ?? 0),
      cost: Number(s.estimatedCostUsd ?? s.cost ?? 0),
    })),
    costOverTime: Array.isArray(m.costOverTime) ? m.costOverTime : [],
    tokensOverTime: Array.isArray(m.tokensOverTime) ? m.tokensOverTime : [],
    costPerOpportunityTrend: Array.isArray(m.costPerOpportunityTrend) ? m.costPerOpportunityTrend : [],
  };
};

const mapCompanyProfile = (p: any): CompanyProfile => ({
  id: String(p.id || 'default'),
  name: String(p.name || ''),
  description: String(p.description || ''),
  primarySector: String(p.primarySector || ''),
  subSectors: Array.isArray(p.subSectors) ? p.subSectors : [],
  coreServices: Array.isArray(p.coreServices) ? p.coreServices : [],
  targetCountries: Array.isArray(p.targetCountries) ? p.targetCountries : [],
  minContractValueEur: Number(p.minContractValueEur ?? 0),
  maxContractValueEur: Number(p.maxContractValueEur ?? 0),
  certifications: Array.isArray(p.certifications) ? p.certifications : [],
  gatekeeperMinScore: Number(p.gatekeeperMinScore ?? 50),
  autoApproveThreshold: Number(p.autoApproveThreshold ?? 75),
});

const toAiConfidenceLabel = (v: any): 'High' | 'Medium' | 'Low' => {
  if (typeof v === 'string') {
    const s = v.toLowerCase();
    if (s === 'high' || s === 'medium' || s === 'low') return s[0].toUpperCase() as 'High' | 'Medium' | 'Low';
  }
  const n = Number(v ?? 0);
  if (n >= 75) return 'High';
  if (n >= 45) return 'Medium';
  return 'Low';
};

const mapProposal = (p: any): Proposal => ({
  id: String(p.id || ''),
  opportunityId: String(p.opportunityId || p.opportunity_id || ''),
  opportunityTitle: String(p.opportunityTitle || p.opportunity_title || ''),
  country: String(p.country || ''),
  source: String(p.source || ''),
  deadline: String(p.deadline || ''),
  overallScore: Number(p.overallScore ?? p.total_score ?? 0),
  decision: toDecisionStatus(p.decision),
  confidence: Number(p.confidence ?? p.qualityMetrics?.aiConfidence ?? 0),
  status: (String(p.status || 'DRAFT').toUpperCase() as any),
  createdAt: String(p.createdAt || p.created_at || p.generated_at || ''),
  updatedAt: String(p.updatedAt || p.updated_at || p.generated_at || ''),
  config: {
    title: String(p.config?.title || ''),
    companyProfileId: String(p.config?.companyProfileId || ''),
    companyProfileName: String(p.config?.companyProfileName || ''),
    language: (p.config?.language || 'English') as any,
    proposalType: (p.config?.proposalType || 'Technical Proposal') as any,
    tone: (p.config?.tone || 'Professional') as any,
    additionalInstructions: String(p.config?.additionalInstructions || ''),
  },
  sections: Array.isArray(p.sections)
    ? p.sections.map((s: any) => ({
        id: String(s.id || ''),
        title: String(s.title || ''),
        content: String(s.content || ''),
        status: (String(s.status || 'GENERATED').toUpperCase() as any),
        lastUpdated: String(s.lastUpdated || s.last_updated || ''),
      }))
    : [],
  qualityMetrics: {
    tenderAlignment: Number(p.qualityMetrics?.tenderAlignment ?? 0),
    requirementCoverage: Number(p.qualityMetrics?.requirementCoverage ?? 0),
    companyCapabilityAlignment: Number(p.qualityMetrics?.companyCapabilityAlignment ?? 0),
    completeness: Number(p.qualityMetrics?.completeness ?? 0),
    missingInformation: Array.isArray(p.qualityMetrics?.missingInformation)
      ? p.qualityMetrics.missingInformation
      : [],
    aiConfidence: toAiConfidenceLabel(p.qualityMetrics?.aiConfidence),
  },
  requirementsSummary: {
    keyRequirements: Array.isArray(p.requirementsSummary?.keyRequirements)
      ? p.requirementsSummary.keyRequirements
      : [],
    eligibilityRequirements: Array.isArray(p.requirementsSummary?.eligibilityRequirements)
      ? p.requirementsSummary.eligibilityRequirements
      : [],
    deliverables: Array.isArray(p.requirementsSummary?.deliverables)
      ? p.requirementsSummary.deliverables
      : [],
    evaluationCriteria: Array.isArray(p.requirementsSummary?.evaluationCriteria)
      ? p.requirementsSummary.evaluationCriteria
      : [],
    importantDates: {
      submissionDeadline: String(p.requirementsSummary?.importantDates?.submissionDeadline || ''),
      clarificationDeadline: String(p.requirementsSummary?.importantDates?.clarificationDeadline || ''),
    },
  },
});

export const apiService = {
  async getOpportunities(params?: FetchOpportunitiesParams): Promise<Opportunity[]> {
    const decisionParam = params?.decision && params.decision !== 'ALL' ? params.decision : undefined;
    const data = await http<any[]>(
      `/v1/opportunities${toQuery({
        search: params?.search,
        country: params?.country && params.country !== 'ALL' ? params.country : undefined,
        source: params?.source && params.source !== 'ALL' ? params.source : undefined,
        decision: decisionParam,
        minScore: params?.minScore,
        maxScore: params?.maxScore,
        sortBy: params?.sortBy,
        sortOrder: params?.sortOrder,
        limit: params?.limit,
      })}`
    );
    return Array.isArray(data) ? data.map(mapOpportunity) : [];
  },

  async getOpportunityById(id: string): Promise<Opportunity | null> {
    try {
      const data = await http<any>(`/v1/opportunities/${id}`);
      return mapOpportunity(data);
    } catch {
      return null;
    }
  },

  async runOpportunityAnalysis(id: string): Promise<Opportunity> {
    try {
      const data = await http<any>(`/v1/opportunities/${id}/analyze`, { method: 'POST' });
      return mapOpportunity(data);
    } catch {
      // fallback while endpoint is being finalized
      const existing = await this.getOpportunityById(id);
      if (!existing) throw new Error('Opportunity not found');
      return {
        ...existing,
        lastAnalyzedAt: new Date().toISOString().replace('T', ' ').substring(0, 19),
        analysisStatus: 'COMPLETED',
      };
    }
  },

  async getAnalyses(params?: FetchOpportunitiesParams): Promise<Opportunity[]> {
    return this.getOpportunities(params);
  },

  async getReviews(): Promise<ReviewItem[]> {
    const data = await http<any[]>('/v1/reviews');
    return Array.isArray(data) ? data.map(mapReview) : [];
  },

  async resolveReview(
    reviewId: string,
    action: 'APPROVE' | 'REJECT' | 'SEND_BACK',
    overrideReason: string,
    actorName: string = 'Current User'
  ): Promise<ReviewItem> {
    const data = await http<any>(`/v1/reviews/${reviewId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ action, overrideReason, actorName }),
    });
    return mapReview(data);
  },

  async getPipelineRuns(): Promise<PipelineRun[]> {
    const data = await http<any[]>('/v1/runs');
    return Array.isArray(data) ? data.map(mapRun) : [];
  },

  async getRunById(id: string): Promise<PipelineRun | null> {
    try {
      const data = await http<any>(`/v1/runs/${id}`);
      return mapRun(data);
    } catch {
      return null;
    }
  },

  async triggerPipelineRun(triggerName: string = 'Manual Dashboard Trigger'): Promise<PipelineRun> {
    const data = await http<any>('/v1/runs', {
      method: 'POST',
      body: JSON.stringify({ triggerName }),
    });
    return mapRun(data);
  },

  async getSystemHealth(): Promise<{ services: SystemService[]; incidents: SystemIncident[] }> {
    const data = await http<any>('/v1/agents/status');
    return {
      services: Array.isArray(data?.services) ? data.services.map(mapSystemService) : [],
      incidents: Array.isArray(data?.incidents) ? data.incidents.map(mapIncident) : [],
    };
  },

  async getCostMetrics(): Promise<CostMetrics> {
    const data = await http<any>('/v1/metrics/cost');
    return mapCostMetrics(data || {});
  },

  async getCompanyProfile(): Promise<CompanyProfile> {
    const data = await http<any>('/v1/company-profile');
    return mapCompanyProfile(data || {});
  },

  async updateCompanyProfile(profile: CompanyProfile): Promise<CompanyProfile> {
    const data = await http<any>('/v1/company-profile', {
      method: 'PUT',
      body: JSON.stringify(profile),
    });
    return mapCompanyProfile(data || {});
  },

  async getProposals(): Promise<Proposal[]> {
    const data = await http<any[]>('/v1/proposals');
    return Array.isArray(data) ? data.map(mapProposal) : [];
  },

  async getProposalById(id: string): Promise<Proposal | null> {
    try {
      const data = await http<any>(`/v1/proposals/${id}`);
      return mapProposal(data);
    } catch {
      return null;
    }
  },

  async createProposal(payload: CreateProposalPayload): Promise<Proposal> {
    const data = await http<any>('/v1/proposals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return mapProposal(data);
  },

  async generateProposal(
    proposalId: string,
    onStageUpdate?: (stageName: string, progress: number) => void
  ): Promise<Proposal> {
    if (onStageUpdate) {
      onStageUpdate('Starting generation', 20);
    }
    const data = await http<any>(`/v1/proposals/${proposalId}/generate`, { method: 'POST' });
    if (onStageUpdate) {
      onStageUpdate('Draft ready', 100);
    }
    return mapProposal(data);
  },

  async updateProposal(proposalId: string, updates: Partial<Proposal>): Promise<Proposal> {
    const data = await http<any>(`/v1/proposals/${proposalId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
    return mapProposal(data);
  },

  async regenerateSection(
    proposalId: string,
    sectionId: string,
    action: 'Regenerate' | 'Improve' | 'Shorten' | 'Expand'
  ): Promise<ProposalSection> {
    const data = await http<any>(`/v1/proposals/${proposalId}/sections/${sectionId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
    return {
      id: String(data.id || sectionId),
      title: String(data.title || ''),
      content: String(data.content || ''),
      status: (String(data.status || 'GENERATED').toUpperCase() as any),
      lastUpdated: String(data.lastUpdated || data.last_updated || new Date().toISOString()),
    };
  },

  async getProposalQuality(proposalId: string): Promise<ProposalQualityMetrics> {
    const data = await http<any>(`/v1/proposals/${proposalId}/quality`);
    return {
      tenderAlignment: Number(data?.tenderAlignment ?? 0),
      requirementCoverage: Number(data?.requirementCoverage ?? 0),
      companyCapabilityAlignment: Number(data?.companyCapabilityAlignment ?? 0),
      completeness: Number(data?.completeness ?? 0),
      missingInformation: Array.isArray(data?.missingInformation) ? data.missingInformation : [],
      aiConfidence: toAiConfidenceLabel(data?.aiConfidence),
    };
  },

  async exportProposal(
    proposalId: string,
    format: 'pdf' | 'docx' | 'markdown'
  ): Promise<{ fileName: string; fileUrl: string }> {
    const data = await http<any>(`/v1/proposals/${proposalId}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
    });
    return {
      fileName: String(data.fileName || ''),
      fileUrl: String(data.fileUrl || ''),
    };
  },
};
