export type DecisionStatus = 'GOOD_FIT' | 'NEEDS_REVIEW' | 'NOT_FIT' | 'FAILED';

export type ReviewType = 'GATEKEEPER' | 'OPPORTUNITY_ANALYSIS';

export type PriorityLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type PipelineStage = 
  | 'INGESTION'
  | 'NORMALIZATION'
  | 'GATEKEEPER'
  | 'PRODUCTION'
  | 'OPPORTUNITY_ANALYSIS'
  | 'REVIEW'
  | 'COMPLETED';

export type RunStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'PARTIALLY_COMPLETED';

export type ServiceHealthStatus = 'HEALTHY' | 'DEGRADED' | 'DOWN';

export interface ScoreBreakdown {
  sectorRelevance: number;      // 0-100
  servicesRelevance: number;    // 0-100
  geographyRelevance: number;   // 0-100
  eligibilityFit: number;       // 0-100
  strategicFit: number;         // 0-100
}

export interface AIReasoning {
  matched: string[];
  missingOrRisk: string[];
  recommendation: string;
}

export interface Opportunity {
  id: string;
  title: string;
  externalId: string;
  source: string;
  sourceUrl: string;
  country: string;
  countryCode: string; // e.g. "DE", "UK", "US", "FR"
  sector: string;
  estimatedValue: string;
  publishedDate: string;
  deadline: string;
  lastAnalyzedAt: string;
  overallScore: number; // 0-100
  decision: DecisionStatus;
  confidence: number; // 0-100 %
  analysisStatus: 'COMPLETED' | 'PENDING' | 'FAILED';
  scoreBreakdown: ScoreBreakdown;
  aiReasoning: AIReasoning;
  description: string;
  requirements: string[];
  eligibilityCriteria: string[];
  profileName: string;
}

export interface ReviewItem {
  id: string;
  opportunityId: string;
  opportunityTitle: string;
  country: string;
  source: string;
  reviewType: ReviewType;
  aiDecision: DecisionStatus;
  score: number;
  confidence: number;
  reason: string;
  createdAt: string;
  priority: PriorityLevel;
  assignee: string | null;
  status: 'OPEN' | 'RESOLVED_APPROVED' | 'RESOLVED_REJECTED' | 'RESOLVED_SENT_BACK';
  resolvedAt?: string;
  resolvedBy?: string;
  overrideReason?: string;
  auditTrail: {
    timestamp: string;
    action: string;
    actor: string;
    notes?: string;
  }[];
}

export interface StageDetail {
  stage: PipelineStage;
  label: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  durationSeconds: number;
  processedCount: number;
  errorsCount: number;
  retryCount: number;
  details?: string;
}

export interface PipelineRun {
  id: string;
  triggeredBy: string;
  startedAt: string;
  completedAt?: string;
  durationSeconds: number;
  currentStage: PipelineStage;
  processedCount: number;
  approvedCount: number;
  reviewCount: number;
  failedCount: number;
  llmCallsCount: number;
  status: RunStatus;
  stages: StageDetail[];
}

export interface SystemService {
  id: string;
  name: string;
  category: 'Ingestion' | 'Queue' | 'AI / Agent' | 'Database' | 'Storage';
  status: ServiceHealthStatus;
  latencyMs: number;
  lastSuccessfulExecution: string;
  errorCount24h: number;
  uptimePercent: number;
  details: string;
}

export interface SystemIncident {
  id: string;
  timestamp: string;
  service: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  message: string;
  resolved: boolean;
}

export interface CostMetrics {
  totalLlmCalls: number;
  inputTokens: number;
  outputTokens: number;
  estimatedCostUsd: number;
  costPerOpportunityUsd: number;
  avgTokensPerRequest: number;
  cacheHitRatePercent: number;
  llmCallsAvoidedByRules: number;
  retryCount: number;
  avgPromptSizeTokens: number;
  callsByStage: { stage: string; calls: number; cost: number }[];
  costOverTime: { date: string; cost: number; calls: number }[];
  tokensOverTime: { date: string; inputTokens: number; outputTokens: number }[];
  costPerOpportunityTrend: { category: string; avgCost: number; opportunitiesCount: number }[];
}

export interface CompanyProfile {
  name: string;
  primarySector: string;
  subSectors: string[];
  coreServices: string[];
  targetCountries: string[];
  minContractValueEur: number;
  maxContractValueEur: number;
  certifications: string[];
  gatekeeperMinScore: number;
  autoApproveThreshold: number;
}

export * from './proposal';

