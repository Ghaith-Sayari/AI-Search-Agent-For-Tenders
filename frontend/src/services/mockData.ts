import {
  Opportunity,
  ReviewItem,
  PipelineRun,
  SystemService,
  SystemIncident,
  CostMetrics,
  CompanyProfile,
  Proposal,
} from '../types';

export const INITIAL_COMPANY_PROFILE: CompanyProfile = {
  id: "default",
  name: "Deloitte Digital & Advisory EMEA",
  description: "Digital transformation and advisory practice focused on public-sector and enterprise modernization.",
  primarySector: "Management Consulting & Digital Transformation",
  subSectors: [
    "IT Consulting & Architecture",
    "Public Sector Advisory",
    "Cloud & AI Integration",
    "Cybersecurity & Data Governance",
    "Healthcare Systems Modernization"
  ],
  coreServices: [
    "Enterprise Software Architecture",
    "AI Strategy & LLM Deployment",
    "Cloud Migration (AWS/Azure/GCP)",
    "Program Management & PMO",
    "Data Analytics & Business Intelligence"
  ],
  targetCountries: ["DE", "UK", "FR", "NL", "BE", "SE", "US", "CH"],
  minContractValueEur: 250000,
  maxContractValueEur: 50000000,
  certifications: ["ISO 27001", "ISO 9001", "SOC2 Type II", "Cyber Essentials Plus"],
  gatekeeperMinScore: 65,
  autoApproveThreshold: 85,
};

export const INITIAL_OPPORTUNITIES: Opportunity[] = [
  {
    id: "opp-2026-0891",
    title: "AI-Driven Public Healthcare Data Integration & Predictive Analytics Platform",
    externalId: "TED-2026-448219",
    source: "TED (Tenders Electronic Daily - EU)",
    sourceUrl: "https://ted.europa.eu/udl?uri=TED:NOTICE:2026-448219",
    country: "Germany",
    countryCode: "DE",
    sector: "Healthcare & Public Sector IT",
    estimatedValue: "€ 4,200,000",
    publishedDate: "2026-08-02",
    deadline: "2026-09-15",
    lastAnalyzedAt: "2026-08-09 10:14:22",
    overallScore: 92,
    decision: "GOOD_FIT",
    confidence: 96,
    analysisStatus: "COMPLETED",
    profileName: "EMEA Public Sector Practice",
    scoreBreakdown: {
      sectorRelevance: 95,
      servicesRelevance: 94,
      geographyRelevance: 98,
      eligibilityFit: 90,
      strategicFit: 83
    },
    aiReasoning: {
      matched: [
        "Direct alignment with Cloud & AI Data Analytics capabilities.",
        "Target geography (Germany) matches primary operating entity.",
        "Estimated contract value (€4.2M) fits target tier perfectly.",
        "Requires ISO 27001 and GDPR compliance certification — fully held."
      ],
      missingOrRisk: [
        "Sub-contractor commitment requested for localized 24/7 on-site support in Munich."
      ],
      recommendation: "High-priority strategic bid. Excellent alignment across technical stack, regional presence, and credential requirements. Recommend immediate partner consortium alignment for local on-site support."
    },
    description: "The Federal Ministry of Health requires a multi-year IT implementation partner to design, build, and maintain a unified national health analytics platform leveraging artificial intelligence for epidemiological prediction and resource optimization across 16 federal states.",
    requirements: [
      "Architecture design for federated data pipeline handling 50M+ citizen records.",
      "Implementation of privacy-preserving machine learning algorithms.",
      "ISO 27001, BSI C5, and GDPR compliance validation.",
      "Agile delivery team with German C1 level fluency."
    ],
    eligibilityCriteria: [
      "Minimum €10M annual turnover in Healthcare IT consulting over last 3 fiscal years.",
      "At least 3 reference projects of similar scale (€3M+) in EU public sector.",
      "ISO 27001 certification."
    ]
  },
  {
    id: "opp-2026-0892",
    title: "National Cyber Resilience & Threat Intelligence Orchestration Services",
    externalId: "UK-GCL-2026-003",
    source: "Contracts Finder UK",
    sourceUrl: "https://www.contractsfinder.service.gov.uk/Notice/uk-gcl-2026-003",
    country: "United Kingdom",
    countryCode: "UK",
    sector: "Cybersecurity & Defense",
    estimatedValue: "£ 6,800,000",
    publishedDate: "2026-08-04",
    deadline: "2026-09-20",
    lastAnalyzedAt: "2026-08-09 11:30:10",
    overallScore: 88,
    decision: "GOOD_FIT",
    confidence: 92,
    analysisStatus: "COMPLETED",
    profileName: "EMEA Cybersecurity Advisory",
    scoreBreakdown: {
      sectorRelevance: 92,
      servicesRelevance: 90,
      geographyRelevance: 95,
      eligibilityFit: 85,
      strategicFit: 78
    },
    aiReasoning: {
      matched: [
        "Direct match with Cyber Security & Threat Intelligence service line.",
        "UK location aligns with London Security Operations Practice.",
        "Includes automated incident triage using GenAI models."
      ],
      missingOrRisk: [
        "Requires SC (Security Clearance) for 100% of staff assigned to live triage."
      ],
      recommendation: "Strong strategic bid. Verify available SC-cleared staff allocation before formal submission."
    },
    description: "Provision of automated threat intelligence analysis, SIEM integration, and managed security operations consulting for critical national infrastructure departments.",
    requirements: [
      "SOC 2 Type II certified operations center.",
      "Deployment of custom AI triage automation scripts.",
      "24/7 UK-based incident response capability."
    ],
    eligibilityCriteria: [
      "Cyber Essentials Plus certification.",
      "Minimum 5 years operating in UK central government security environments."
    ]
  },
  {
    id: "opp-2026-0893",
    title: "Tax Authority Cloud Migration & Legacy Mainframe Modernization",
    externalId: "FR-BOAMP-2026-8812",
    source: "BOAMP France",
    sourceUrl: "https://www.boamp.fr/avis/detail/2026-8812",
    country: "France",
    countryCode: "FR",
    sector: "Cloud Architecture & Digital Transformation",
    estimatedValue: "€ 12,500,000",
    publishedDate: "2026-08-01",
    deadline: "2026-09-28",
    lastAnalyzedAt: "2026-08-09 09:05:00",
    overallScore: 74,
    decision: "NEEDS_REVIEW",
    confidence: 79,
    analysisStatus: "COMPLETED",
    profileName: "EMEA Public Sector Practice",
    scoreBreakdown: {
      sectorRelevance: 88,
      servicesRelevance: 82,
      geographyRelevance: 75,
      eligibilityFit: 62,
      strategicFit: 69
    },
    aiReasoning: {
      matched: [
        "High match on Cloud Migration & Application Refactoring.",
        "Scale of €12.5M provides high margin potential."
      ],
      missingOrRisk: [
        "Mandates proprietary French tax legacy code (COBOL / DB2) refactoring capability.",
        "Requires SecNumCloud certified cloud environment hosting in France."
      ],
      recommendation: "Needs Review. Technical qualification required to confirm availability of legacy COBOL migration specialists and partner compliance with SecNumCloud requirements."
    },
    description: "Modernization of legacy tax calculation engines to a microservices architecture hosted on sovereign European cloud infrastructure.",
    requirements: [
      "COBOL mainframe logic extraction to Java/Spring Boot.",
      "Sovereign cloud deployment compliant with French SecNumCloud standards."
    ],
    eligibilityCriteria: [
      "Minimum €25M annual turnover in France.",
      "SecNumCloud partner ecosystem agreement."
    ]
  },
  {
    id: "opp-2026-0894",
    title: "Smart Customs & Logistics AI Automation Pilot",
    externalId: "NL-TENDER-2026-041",
    source: "TenderNed Netherlands",
    sourceUrl: "https://www.tenderned.nl/tenderned-tap/notice/2026-041",
    country: "Netherlands",
    countryCode: "NL",
    sector: "Logistics & Customs Advisory",
    estimatedValue: "€ 1,800,000",
    publishedDate: "2026-08-05",
    deadline: "2026-09-10",
    lastAnalyzedAt: "2026-08-09 08:22:15",
    overallScore: 68,
    decision: "NEEDS_REVIEW",
    confidence: 72,
    analysisStatus: "COMPLETED",
    profileName: "EMEA Supply Chain & Operations",
    scoreBreakdown: {
      sectorRelevance: 70,
      servicesRelevance: 72,
      geographyRelevance: 85,
      eligibilityFit: 58,
      strategicFit: 55
    },
    aiReasoning: {
      matched: [
        "Strong geography fit (Amsterdam office nearby).",
        "AI computer vision inspection component matches innovative advisory capabilities."
      ],
      missingOrRisk: [
        "Contract requires hardware camera sensor procurement which is out of core advisory scope.",
        "Tight submission deadline (10 September)."
      ],
      recommendation: "Needs Review. Determine if hardware component can be outsourced to a local hardware partner while retaining prime consulting contract."
    },
    description: "AI-powered automated inspection of customs documentation and cargo container seal validation at the Port of Rotterdam.",
    requirements: [
      "Computer vision OCR for container codes.",
      "Integration with Dutch Customs risk engine."
    ],
    eligibilityCriteria: [
      "Port infrastructure experience in Benelux region."
    ]
  },
  {
    id: "opp-2026-0895",
    title: "Small Business Advisory Audit Software Maintenance",
    externalId: "BE-BULLETIN-2026-902",
    source: "e-Procurement Belgium",
    sourceUrl: "https://www.e-procurement.be/notice/2026-902",
    country: "Belgium",
    countryCode: "BE",
    sector: "Software Maintenance & Support",
    estimatedValue: "€ 180,000",
    publishedDate: "2026-08-03",
    deadline: "2026-08-25",
    lastAnalyzedAt: "2026-08-08 14:10:00",
    overallScore: 32,
    decision: "NOT_FIT",
    confidence: 94,
    analysisStatus: "COMPLETED",
    profileName: "EMEA Public Sector Practice",
    scoreBreakdown: {
      sectorRelevance: 40,
      servicesRelevance: 30,
      geographyRelevance: 80,
      eligibilityFit: 10,
      strategicFit: 0
    },
    aiReasoning: {
      matched: [
        "Geographic proximity (Brussels)."
      ],
      missingOrRisk: [
        "Contract value (€180k) falls below minimum target threshold (€250k).",
        "Relates to legacy PHP application bug fixing with no strategic growth potential."
      ],
      recommendation: "Reject. Below minimum economic threshold and lacks strategic transformation alignment."
    },
    description: "Routine maintenance and minor updates for legacy SME audit portal built in Drupal 7.",
    requirements: [
      "Drupal 7 bug fixes and PHP 7.4 patch maintenance."
    ],
    eligibilityCriteria: [
      "Low value threshold."
    ]
  },
  {
    id: "opp-2026-0896",
    title: "NATO Enterprise Knowledge Base LLM Rag System Deployment",
    externalId: "NATO-NCI-2026-119",
    source: "NATO Communications and Information Agency",
    sourceUrl: "https://www.ncia.nato.int/opportunities/2026-119",
    country: "Multilateral / NATO",
    countryCode: "EU",
    sector: "Defense & Strategic AI",
    estimatedValue: "€ 8,500,000",
    publishedDate: "2026-08-06",
    deadline: "2026-10-01",
    lastAnalyzedAt: "2026-08-09 12:00:00",
    overallScore: 95,
    decision: "GOOD_FIT",
    confidence: 98,
    analysisStatus: "COMPLETED",
    profileName: "Global Defense Practice",
    scoreBreakdown: {
      sectorRelevance: 98,
      servicesRelevance: 96,
      geographyRelevance: 90,
      eligibilityFit: 95,
      strategicFit: 96
    },
    aiReasoning: {
      matched: [
        "Perfect match for Enterprise RAG / LLM deployment framework.",
        "NATO Secret facility clearance held at practice level.",
        "High margin potential with multi-year extension options."
      ],
      missingOrRisk: [
        "Requires air-gapped on-premises GPU infrastructure validation."
      ],
      recommendation: "Flagship opportunity. Proceed immediately to capture plan development."
    },
    description: "Deployment of sovereign, air-gapped Retrieval-Augmented Generation LLM infrastructure across NATO headquarters and operational commands.",
    requirements: [
      "On-premise GPU cluster orchestration.",
      "Multi-lingual semantic search across un-structured classified documents."
    ],
    eligibilityCriteria: [
      "NATO Secret facility security clearance.",
      "Registered NATO supplier status."
    ]
  },
  {
    id: "opp-2026-0897",
    title: "Digital Public Administration Citizen Portal Redesign",
    externalId: "SE-KOMMUN-2026-302",
    source: "TendSign Sweden",
    sourceUrl: "https://www.tendsign.se/notice/2026-302",
    country: "Sweden",
    countryCode: "SE",
    sector: "Digital Service Design",
    estimatedValue: "€ 2,900,000",
    publishedDate: "2026-08-04",
    deadline: "2026-09-18",
    lastAnalyzedAt: "2026-08-09 07:45:00",
    overallScore: 82,
    decision: "GOOD_FIT",
    confidence: 88,
    analysisStatus: "COMPLETED",
    profileName: "Nordic Digital Advisory",
    scoreBreakdown: {
      sectorRelevance: 85,
      servicesRelevance: 88,
      geographyRelevance: 80,
      eligibilityFit: 82,
      strategicFit: 75
    },
    aiReasoning: {
      matched: [
        "Strong experience in civic portal UX/UI and accessibility standards (WCAG 2.1 AAA).",
        "Proven track record in Nordic municipality transformations."
      ],
      missingOrRisk: [
        "Requires Swedish language documentation for end-user guides."
      ],
      recommendation: "Approved for pursuit. Engage Stockholm office team for lead account management."
    },
    description: "User-centric overhaul of citizen engagement portals for 12 Swedish municipal councils.",
    requirements: [
      "Accessibility audit and implementation.",
      "Mobile-first React application architecture."
    ],
    eligibilityCriteria: [
      "Nordics presence."
    ]
  },
  {
    id: "opp-2026-0898",
    title: "Automated Scraping Engine Pipeline Failure Test",
    externalId: "RAW-ERR-9912",
    source: "Automated Ingestion Feed",
    sourceUrl: "https://example.org/invalid-notice",
    country: "Unknown",
    countryCode: "UN",
    sector: "Unclassified",
    estimatedValue: "Unknown",
    publishedDate: "2026-08-08",
    deadline: "Unknown",
    lastAnalyzedAt: "2026-08-08 19:30:00",
    overallScore: 0,
    decision: "FAILED",
    confidence: 10,
    analysisStatus: "FAILED",
    profileName: "System Diagnostics Profile",
    scoreBreakdown: {
      sectorRelevance: 0,
      servicesRelevance: 0,
      geographyRelevance: 0,
      eligibilityFit: 0,
      strategicFit: 0
    },
    aiReasoning: {
      matched: [],
      missingOrRisk: [
        "Document ingestion failed due to corrupt PDF header.",
        "Missing mandatory deadline and value fields."
      ],
      recommendation: "Failed Gatekeeper processing. Requires manual document upload or source re-scraping."
    },
    description: "Corrupt document payload received during automated daily scraper job.",
    requirements: [],
    eligibilityCriteria: []
  }
];

export const INITIAL_REVIEWS: ReviewItem[] = [
  {
    id: "rev-101",
    opportunityId: "opp-2026-0893",
    opportunityTitle: "Tax Authority Cloud Migration & Legacy Mainframe Modernization",
    country: "France",
    source: "BOAMP France",
    reviewType: "OPPORTUNITY_ANALYSIS",
    aiDecision: "NEEDS_REVIEW",
    score: 74,
    confidence: 79,
    reason: "Mandatory SecNumCloud sovereignty requirement detected. AI confidence is below auto-approval threshold (85%) due to strict French local partner eligibility ambiguity.",
    createdAt: "2026-08-09 09:06:12",
    priority: "HIGH",
    assignee: "Jean-Luc Moreau (Partner, Paris)",
    status: "OPEN",
    auditTrail: [
      {
        timestamp: "2026-08-09 09:05:00",
        action: "AI Gatekeeper Evaluation Completed",
        actor: "AI Gatekeeper Agent v2.4",
        notes: "Assigned decision: NEEDS_REVIEW. Triggered by confidence score (79%) below threshold (85%)."
      },
      {
        timestamp: "2026-08-09 09:10:00",
        action: "Assigned Reviewer",
        actor: "System Router",
        notes: "Automatically assigned to Lead France Partner based on geographic metadata."
      }
    ]
  },
  {
    id: "rev-102",
    opportunityId: "opp-2026-0894",
    opportunityTitle: "Smart Customs & Logistics AI Automation Pilot",
    country: "Netherlands",
    source: "TenderNed Netherlands",
    reviewType: "GATEKEEPER",
    aiDecision: "NEEDS_REVIEW",
    score: 68,
    confidence: 72,
    reason: "Out-of-scope hardware procurement detected (Camera Sensors & Barriers). Gatekeeper flagged potential low margin due to hardware pass-through costs.",
    createdAt: "2026-08-09 08:23:40",
    priority: "MEDIUM",
    assignee: "Anouk van der Meer (Director, Amsterdam)",
    status: "OPEN",
    auditTrail: [
      {
        timestamp: "2026-08-09 08:22:15",
        action: "AI Gatekeeper Evaluation Completed",
        actor: "AI Gatekeeper Agent v2.4",
        notes: "Flagged for manual review due to Hardware Procurement keyword match."
      }
    ]
  },
  {
    id: "rev-103",
    opportunityId: "opp-2026-0898",
    opportunityTitle: "Automated Scraping Engine Pipeline Failure Test",
    country: "Unknown",
    source: "Automated Ingestion Feed",
    reviewType: "GATEKEEPER",
    aiDecision: "FAILED",
    score: 0,
    confidence: 10,
    reason: "PDF parsing failed with exception (Corrupt PDF Trailer). Unable to extract deadline or estimated budget.",
    createdAt: "2026-08-08 19:31:00",
    priority: "LOW",
    assignee: null,
    status: "OPEN",
    auditTrail: [
      {
        timestamp: "2026-08-08 19:30:00",
        action: "Ingestion Parse Error",
        actor: "Document Normalizer Node",
        notes: "PDF stream could not be converted to structured text."
      }
    ]
  }
];

export const INITIAL_RUNS: PipelineRun[] = [
  {
    id: "run-2026-0809-01",
    triggeredBy: "Scheduled Cron (06:00 UTC)",
    startedAt: "2026-08-09 06:00:00",
    completedAt: "2026-08-09 06:14:32",
    durationSeconds: 872,
    currentStage: "COMPLETED",
    processedCount: 142,
    approvedCount: 18,
    reviewCount: 5,
    failedCount: 1,
    llmCallsCount: 284,
    status: "COMPLETED",
    stages: [
      { stage: 'INGESTION', label: 'Tender Ingestion', status: 'COMPLETED', durationSeconds: 120, processedCount: 142, errorsCount: 0, retryCount: 0, details: "Scraped TED, Contracts Finder, BOAMP, TenderNed." },
      { stage: 'NORMALIZATION', label: 'Document Normalization', status: 'COMPLETED', durationSeconds: 180, processedCount: 142, errorsCount: 1, retryCount: 1, details: "Extracted PDF text and metadata." },
      { stage: 'GATEKEEPER', label: 'AI Gatekeeper Qualification', status: 'COMPLETED', durationSeconds: 210, processedCount: 141, errorsCount: 0, retryCount: 0, details: "Filtered 118 non-matching tenders via deterministic rules & LLM zero-shot." },
      { stage: 'PRODUCTION', label: 'Data Enrichment', status: 'COMPLETED', durationSeconds: 90, processedCount: 23, errorsCount: 0, retryCount: 0, details: "Enriched company financial data & historical buyer stats." },
      { stage: 'OPPORTUNITY_ANALYSIS', label: 'AI Fit Analysis & Scoring', status: 'COMPLETED', durationSeconds: 212, processedCount: 23, errorsCount: 0, retryCount: 0, details: "Calculated 5-dimension fit scores and generated match reasoning." },
      { stage: 'REVIEW', label: 'Review Queue Routing', status: 'COMPLETED', durationSeconds: 30, processedCount: 5, errorsCount: 0, retryCount: 0, details: "Routed 5 items to human review queues." },
      { stage: 'COMPLETED', label: 'Run Completion', status: 'COMPLETED', durationSeconds: 30, processedCount: 142, errorsCount: 0, retryCount: 0, details: "Run executed successfully." }
    ]
  },
  {
    id: "run-2026-0809-02",
    triggeredBy: "Manual Trigger (User: Ghaith)",
    startedAt: "2026-08-09 11:15:00",
    completedAt: "2026-08-09 11:22:10",
    durationSeconds: 430,
    currentStage: "COMPLETED",
    processedCount: 45,
    approvedCount: 8,
    reviewCount: 2,
    failedCount: 0,
    llmCallsCount: 90,
    status: "COMPLETED",
    stages: [
      { stage: 'INGESTION', label: 'Tender Ingestion', status: 'COMPLETED', durationSeconds: 45, processedCount: 45, errorsCount: 0, retryCount: 0, details: "Targeted fetch for UK & Germany RSS feeds." },
      { stage: 'NORMALIZATION', label: 'Document Normalization', status: 'COMPLETED', durationSeconds: 85, processedCount: 45, errorsCount: 0, retryCount: 0, details: "Clean text parsed." },
      { stage: 'GATEKEEPER', label: 'AI Gatekeeper Qualification', status: 'COMPLETED', durationSeconds: 110, processedCount: 45, errorsCount: 0, retryCount: 0, details: "Filtered 35 irrelevant tenders." },
      { stage: 'PRODUCTION', label: 'Data Enrichment', status: 'COMPLETED', durationSeconds: 50, processedCount: 10, errorsCount: 0, retryCount: 0, details: "Buyer profile lookup." },
      { stage: 'OPPORTUNITY_ANALYSIS', label: 'AI Fit Analysis & Scoring', status: 'COMPLETED', durationSeconds: 120, processedCount: 10, errorsCount: 0, retryCount: 0, details: "Generated recommendations." },
      { stage: 'REVIEW', label: 'Review Queue Routing', status: 'COMPLETED', durationSeconds: 10, processedCount: 2, errorsCount: 0, retryCount: 0, details: "Assigned to reviewers." },
      { stage: 'COMPLETED', label: 'Run Completion', status: 'COMPLETED', durationSeconds: 10, processedCount: 45, errorsCount: 0, retryCount: 0, details: "Manual pipeline run finished." }
    ]
  },
  {
    id: "run-2026-0809-03",
    triggeredBy: "Webhook Trigger (TED EU Live Feed)",
    startedAt: "2026-08-09 14:00:00",
    durationSeconds: 175,
    currentStage: "OPPORTUNITY_ANALYSIS",
    processedCount: 28,
    approvedCount: 3,
    reviewCount: 1,
    failedCount: 0,
    llmCallsCount: 42,
    status: "RUNNING",
    stages: [
      { stage: 'INGESTION', label: 'Tender Ingestion', status: 'COMPLETED', durationSeconds: 30, processedCount: 28, errorsCount: 0, retryCount: 0, details: "TED Webhook payload received." },
      { stage: 'NORMALIZATION', label: 'Document Normalization', status: 'COMPLETED', durationSeconds: 45, processedCount: 28, errorsCount: 0, retryCount: 0, details: "XML and PDF transformed to Markdown." },
      { stage: 'GATEKEEPER', label: 'AI Gatekeeper Qualification', status: 'COMPLETED', durationSeconds: 60, processedCount: 28, errorsCount: 0, retryCount: 0, details: "Filtered out 22 low relevance notices." },
      { stage: 'PRODUCTION', label: 'Data Enrichment', status: 'COMPLETED', durationSeconds: 40, processedCount: 6, errorsCount: 0, retryCount: 0, details: "Enrichment complete." },
      { stage: 'OPPORTUNITY_ANALYSIS', label: 'AI Fit Analysis & Scoring', status: 'RUNNING', durationSeconds: 0, processedCount: 6, errorsCount: 0, retryCount: 0, details: "Evaluating multidimensional vector distance & scoring..." },
      { stage: 'REVIEW', label: 'Review Queue Routing', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 },
      { stage: 'COMPLETED', label: 'Run Completion', status: 'PENDING', durationSeconds: 0, processedCount: 0, errorsCount: 0, retryCount: 0 }
    ]
  }
];

export const INITIAL_SYSTEM_SERVICES: SystemService[] = [
  {
    id: "srv-01",
    name: "Public Tender Web Scraper Cluster",
    category: "Ingestion",
    status: "HEALTHY",
    latencyMs: 142,
    lastSuccessfulExecution: "2026-08-09 14:15:02",
    errorCount24h: 2,
    uptimePercent: 99.94,
    details: "12 headless browser nodes active across EU and UK worker pools."
  },
  {
    id: "srv-02",
    name: "Celery Distributed Task Queue",
    category: "Queue",
    status: "HEALTHY",
    latencyMs: 18,
    lastSuccessfulExecution: "2026-08-09 14:28:44",
    errorCount24h: 0,
    uptimePercent: 100.0,
    details: "Concurrency limit: 64 tasks. Active queue depth: 4."
  },
  {
    id: "srv-03",
    name: "Redis State Cache & Broker",
    category: "Queue",
    status: "HEALTHY",
    latencyMs: 4,
    lastSuccessfulExecution: "2026-08-09 14:28:50",
    errorCount24h: 0,
    uptimePercent: 100.0,
    details: "Memory utilization: 1.2 GB / 8.0 GB (15%)."
  },
  {
    id: "srv-04",
    name: "AI Qualification Gatekeeper Agent",
    category: "AI / Agent",
    status: "HEALTHY",
    latencyMs: 410,
    lastSuccessfulExecution: "2026-08-09 14:22:10",
    errorCount24h: 1,
    uptimePercent: 99.85,
    details: "Gemini 2.5 Flash model endpoint. Deterministic fallback active."
  },
  {
    id: "srv-05",
    name: "Opportunity Fit Analyzer Agent",
    category: "AI / Agent",
    status: "HEALTHY",
    latencyMs: 820,
    lastSuccessfulExecution: "2026-08-09 14:25:33",
    errorCount24h: 0,
    uptimePercent: 99.98,
    details: "Multidimensional vector embedding and 5-tier scoring engine."
  },
  {
    id: "srv-06",
    name: "LangGraph Pipeline State Machine",
    category: "AI / Agent",
    status: "HEALTHY",
    latencyMs: 65,
    lastSuccessfulExecution: "2026-08-09 14:26:00",
    errorCount24h: 0,
    uptimePercent: 100.0,
    details: "Checkpoint store online with state rewind enabled."
  },
  {
    id: "srv-07",
    name: "PostgreSQL Production Database",
    category: "Database",
    status: "HEALTHY",
    latencyMs: 12,
    lastSuccessfulExecution: "2026-08-09 14:28:55",
    errorCount24h: 0,
    uptimePercent: 100.0,
    details: "Connections: 24/100. Storage: 14.2 GB used."
  },
  {
    id: "srv-08",
    name: "LLM Backend Proxy & Rate Limiter",
    category: "AI / Agent",
    status: "HEALTHY",
    latencyMs: 230,
    lastSuccessfulExecution: "2026-08-09 14:28:10",
    errorCount24h: 3,
    uptimePercent: 99.91,
    details: "Token rate limit: 1,000,000 TPM. Current load: 18%."
  }
];

export const INITIAL_SYSTEM_INCIDENTS: SystemIncident[] = [
  {
    id: "inc-801",
    timestamp: "2026-08-08 19:30:00",
    service: "Public Tender Web Scraper Cluster",
    severity: "WARNING",
    message: "Corrupt PDF payload encountered during TED feed ingestion (Notice TED-RAW-ERR-9912).",
    resolved: true
  },
  {
    id: "inc-802",
    timestamp: "2026-08-07 14:10:22",
    service: "LLM Backend Proxy & Rate Limiter",
    severity: "WARNING",
    message: "Transient 429 Rate Limit from primary AI model provider. Automatic retry succeeded on secondary backup model.",
    resolved: true
  }
];

export const INITIAL_COST_METRICS: CostMetrics = {
  totalLlmCalls: 14280,
  inputTokens: 18450000,
  outputTokens: 2120000,
  estimatedCostUsd: 148.25,
  costPerOpportunityUsd: 0.18,
  avgTokensPerRequest: 1440,
  cacheHitRatePercent: 42.5,
  llmCallsAvoidedByRules: 8410,
  retryCount: 14,
  avgPromptSizeTokens: 1290,
  callsByStage: [
    { stage: "Document Structuring", calls: 4200, cost: 31.50 },
    { stage: "Gatekeeper Qualification", calls: 6800, cost: 42.10 },
    { stage: "Opportunity Fit Scoring", calls: 2480, cost: 58.40 },
    { stage: "Review Reason Generation", calls: 800, cost: 16.25 }
  ],
  costOverTime: [
    { date: "Aug 03", cost: 18.40, calls: 1820 },
    { date: "Aug 04", cost: 22.10, calls: 2100 },
    { date: "Aug 05", cost: 19.80, calls: 1950 },
    { date: "Aug 06", cost: 24.50, calls: 2380 },
    { date: "Aug 07", cost: 21.00, calls: 2050 },
    { date: "Aug 08", cost: 22.90, calls: 2200 },
    { date: "Aug 09", cost: 19.55, calls: 1780 }
  ],
  tokensOverTime: [
    { date: "Aug 03", inputTokens: 2200000, outputTokens: 280000 },
    { date: "Aug 04", inputTokens: 2800000, outputTokens: 340000 },
    { date: "Aug 05", inputTokens: 2400000, outputTokens: 290000 },
    { date: "Aug 06", inputTokens: 3100000, outputTokens: 380000 },
    { date: "Aug 07", inputTokens: 2600000, outputTokens: 310000 },
    { date: "Aug 08", inputTokens: 2900000, outputTokens: 330000 },
    { date: "Aug 09", inputTokens: 2450000, outputTokens: 190000 }
  ],
  costPerOpportunityTrend: [
    { category: "Healthcare IT", avgCost: 0.22, opportunitiesCount: 42 },
    { category: "Cybersecurity", avgCost: 0.19, opportunitiesCount: 38 },
    { category: "Cloud & Advisory", avgCost: 0.16, opportunitiesCount: 65 },
    { category: "Public Defense", avgCost: 0.25, opportunitiesCount: 22 }
  ]
};

export const INITIAL_PROPOSALS: Proposal[] = [
  {
    id: "prop-2026-001",
    opportunityId: "opp-2026-0891",
    opportunityTitle: "AI-Driven Public Healthcare Data Integration & Predictive Analytics Platform",
    country: "Germany",
    source: "TED (Tenders Electronic Daily - EU)",
    deadline: "2026-09-15",
    overallScore: 92,
    decision: "GOOD_FIT",
    status: "READY_FOR_REVIEW",
    createdAt: "2026-08-10 14:30:00",
    updatedAt: "2026-08-10 14:35:12",
    config: {
      title: "Technical Proposal: AI Healthcare Predictive Analytics Platform (Federal Ministry of Health)",
      companyProfileId: "prof-01",
      companyProfileName: "Deloitte Digital & Advisory EMEA",
      language: "English",
      proposalType: "Technical Proposal",
      tone: "Professional",
      additionalInstructions: "Emphasize ISO 27001 data governance, GDPR compliance, and federated machine learning architecture for 50M+ records.",
    },
    qualityMetrics: {
      tenderAlignment: 94,
      requirementCoverage: 91,
      companyCapabilityAlignment: 96,
      missingInformation: [
        "Local Munich partner on-site support SLA commitments",
        "Key personnel CV references for Senior Data Architect",
        "Specific fixed-price rate card per labor tier"
      ],
      aiConfidence: "High"
    },
    requirementsSummary: {
      keyRequirements: [
        "Architecture design for federated data pipeline handling 50M+ citizen records.",
        "Implementation of privacy-preserving machine learning algorithms.",
        "ISO 27001, BSI C5, and GDPR compliance validation.",
        "Agile delivery team with German C1 level fluency."
      ],
      eligibilityRequirements: [
        "Minimum €10M annual turnover in Healthcare IT consulting over last 3 fiscal years.",
        "At least 3 reference projects of similar scale (€3M+) in EU public sector.",
        "ISO 27001 certification."
      ],
      deliverables: [
        "Federated Architecture Blueprint & Security Concept Document",
        "Privacy-Preserving Predictive Analytics Core Model",
        "Production Data Pipeline Integration & Interoperability Layer",
        "16 Federal State Portal Dashboards & Operations Manual"
      ],
      importantDates: {
        submissionDeadline: "2026-09-15 17:00 CET",
        clarificationDeadline: "2026-08-28 12:00 CET"
      }
    },
    sections: [
      {
        id: "sec-exec",
        title: "Executive Summary",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Deloitte Digital & Advisory EMEA is pleased to submit this Technical Proposal to the German Federal Ministry of Health for the design, deployment, and ongoing operation of the AI-Driven Public Healthcare Data Integration & Predictive Analytics Platform.\n\nOur proposed solution combines proven public sector digital transformation methodologies with state-of-the-art federated machine learning technologies. By architecting an air-gapped, privacy-preserving analytics fabric, Deloitte will enable real-time epidemiological forecasting and hospital resource optimization across all 16 federal states without compromising individual patient data sovereignty or violating strict European GDPR and BSI C5 standards.`
      },
      {
        id: "sec-req",
        title: "Understanding of Requirements",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `The Federal Ministry of Health requires a unified national analytics engine capable of ingesting high-velocity healthcare telemetry while maintaining rigorous compliance across disparate regional health authorities.\n\nKey Operational Challenges Identified:\n1. Multi-State Heterogeneity: Normalizing schema across 16 federal state health databases with varied legacy formats.\n2. Scale & Security: Handling over 50 million citizen records under ultra-strict BSI C5 and ISO 27001 standards.\n3. Model Interpretability: Providing health officials with transparent, explainable AI predictions rather than opaque black-box recommendations.`
      },
      {
        id: "sec-comp",
        title: "Company Profile",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Deloitte Digital & Advisory EMEA stands as Europe's premier public sector consulting practice, bringing over 2,500 dedicated healthcare and cloud advisory professionals across Germany, France, the UK, and the Nordics.\n\nKey Organization Credentials:\n• ISO 27001 & ISO 9001 certified operations across all European delivery centers.\n• SOC 2 Type II compliance for cloud and managed intelligence platforms.\n• Over €85M delivered in EU public health modernization projects over the past 36 months.`
      },
      {
        id: "sec-approach",
        title: "Proposed Approach",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Our technical approach centers on three pillars: Federated Architecture, Privacy-Preserving AI, and Modular Microservices.\n\n1. Federated Machine Learning: Nodes deployed at state-level health authorities train models locally. Only anonymized model parameter updates are aggregated centrally, ensuring raw patient records never cross state boundaries.\n2. Zero-Trust Security Fabric: All communications utilize post-quantum resistant TLS encryption and hardware-backed key storage.`
      },
      {
        id: "sec-method",
        title: "Methodology",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `We execute our engagement through the Deloitte Agile Public Sector (DAPS) Framework—an iterative 4-phase delivery framework tailored for government stakeholders:\n\n• Phase 1: Architectural Foundation & Data Standard Alignment (Months 1–3)\n• Phase 2: Pilot Node Deployment & Model Training Validation (Months 4–6)\n• Phase 3: 16-State Rollout & System Interoperability Testing (Months 7–12)\n• Phase 4: Full Operational Handover & Managed Advisory (Months 13+)`
      },
      {
        id: "sec-tech",
        title: "Technical Solution",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `The Technical Solution relies on containerized cloud-native microservices orchestrated via Kubernetes on sovereign cloud infrastructure.\n\nCore Architecture Stack:\n• Ingestion Engine: Distributed Kafka streaming pipeline with automated FHIR/HL7 schema validation.\n• AI Models: Gemini Flash-powered time-series forecasting and anomaly detection algorithms tuned for hospital bed and ICU capacity prediction.\n• Visualization Suite: Real-time executive web application rendering geospatial heatmaps and predictive alert triggers.`
      },
      {
        id: "sec-plan",
        title: "Project Plan",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Work Breakdown Structure (WBS):\n\nMilestone 1: Inception & Governance Setup (Week 4)\nMilestone 2: Security Concept & BSI C5 Audit Signoff (Week 12)\nMilestone 3: Minimal Viable Platform (MVP) Pilot in Bavaria & NRW (Week 24)\nMilestone 4: Full Federal Rollout & Final Acceptance (Week 48)`
      },
      {
        id: "sec-team",
        title: "Team & Expertise",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `The project will be led by a dedicated Engagement Partner based in Berlin, supported by:\n\n• Principal Healthcare Solutions Architect (15+ yrs experience in federal IT)\n• Lead AI Data Scientist (PhD in Computational Health Analytics)\n• Lead Cybersecurity & BSI C5 Compliance Officer\n• Agile Delivery Managers with German C1 fluency.`
      },
      {
        id: "sec-deliv",
        title: "Deliverables",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `1. D-01: System Architecture & Data Schema Specification Document\n2. D-02: BSI C5 & GDPR Data Protection Impact Assessment (DPIA)\n3. D-03: Production Analytics Platform Release (v1.0)\n4. D-04: User Training Manuals & Administrator Operational Handbooks`
      },
      {
        id: "sec-qa",
        title: "Quality Assurance",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Deloitte applies automated CI/CD security scanning, dynamic application testing (DAST), and strict code reviews before any deployment. Automated unit test coverage must meet or exceed 90% across all technical repositories.`
      },
      {
        id: "sec-risk",
        title: "Risk Management",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Identified Risks & Mitigation Strategies:\n\n• Risk R-01: Delay in state-level legacy database API access.\n  Mitigation: Deploy standard FHIR adapter wrappers and synthetic data generators for early testing.\n• Risk R-02: Local 24/7 on-site support SLA fulfillment.\n  Mitigation: Subcontract qualified regional partner in Munich for tier-1 hardware on-site response.`
      },
      {
        id: "sec-concl",
        title: "Conclusion",
        status: "GENERATED",
        lastUpdated: "2026-08-10 14:35:12",
        content: `Deloitte brings unmatched technical depth, domain expertise in European public health, and robust governance to guarantee the success of the Federal Ministry of Health's AI analytics initiative. We look forward to partnering on this transformative national effort.`
      }
    ]
  }
];
