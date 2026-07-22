create table if not exists public.opportunity_analysis (
    id uuid primary key default gen_random_uuid(),
    production_tender_id uuid not null references public.production_tender(id),
    unique_key text not null,
    status text not null check (status in ('good_fit', 'needs_review', 'not_fit', 'failed')),
    total_score double precision not null check (total_score >= 0 and total_score <= 100),
    confidence_score double precision not null check (confidence_score >= 0 and confidence_score <= 1),
    decision_reason text not null,
    risk_level text not null check (risk_level in ('low', 'medium', 'high')),
    score_breakdown jsonb not null default '{}'::jsonb,
    blockers jsonb not null default '[]'::jsonb,
    blocker_evidence jsonb not null default '{}'::jsonb,
    strengths jsonb not null default '[]'::jsonb,
    gaps jsonb not null default '[]'::jsonb,
    budget_source text not null default 'unknown' check (budget_source in ('extracted', 'estimated', 'unknown')),
    budget_eur double precision,
    budget_range_min_eur double precision,
    budget_range_max_eur double precision,
    budget_estimation_rationale text,
    processed_at timestamp with time zone not null,
    policy_version text not null,
    agent_version text not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    unique (unique_key, policy_version)
);

create index if not exists opportunity_analysis_status_idx
    on public.opportunity_analysis (status);

create index if not exists opportunity_analysis_production_tender_id_idx
    on public.opportunity_analysis (production_tender_id);

create index if not exists opportunity_analysis_processed_at_idx
    on public.opportunity_analysis (processed_at desc);
