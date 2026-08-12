create table if not exists public.analyzed_tender (
    id uuid primary key default gen_random_uuid(),
    production_tender_id uuid references public.production_tender(id) on delete set null,
    unique_key text not null,
    profile_id text not null,
    source text,
    title text,
    country text,
    deadline date,
    url text,
    decision text not null check (decision in ('pursue', 'review', 'reject')),
    total_score double precision not null check (total_score >= 0 and total_score <= 100),
    total_score_normalized double precision not null check (total_score_normalized >= 0 and total_score_normalized <= 1),
    confidence_score double precision not null check (confidence_score >= 0 and confidence_score <= 1),
    low_confidence boolean not null default false,
    decision_reason text not null default '',
    llm_status text not null default 'unknown',
    llm_error text,
    matched_keywords jsonb not null default '[]'::jsonb,
    location_match_type text not null default 'unknown',
    signals jsonb not null default '[]'::jsonb,
    processed_at timestamp with time zone not null default now(),
    policy_version text not null,
    agent_version text not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    unique (unique_key, profile_id, policy_version)
);

create index if not exists analyzed_tender_processed_at_idx
    on public.analyzed_tender (processed_at desc);

create index if not exists analyzed_tender_decision_idx
    on public.analyzed_tender (decision);

create index if not exists analyzed_tender_profile_id_idx
    on public.analyzed_tender (profile_id);

create index if not exists analyzed_tender_production_tender_id_idx
    on public.analyzed_tender (production_tender_id);

create index if not exists analyzed_tender_llm_status_idx
    on public.analyzed_tender (llm_status);

create index if not exists analyzed_tender_location_match_type_idx
    on public.analyzed_tender (location_match_type);
