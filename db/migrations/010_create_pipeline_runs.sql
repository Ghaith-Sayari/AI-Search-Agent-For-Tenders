create table if not exists public.pipeline_runs (
    id uuid primary key default gen_random_uuid(),
    triggered_by text not null,
    started_at timestamp with time zone not null default now(),
    completed_at timestamp with time zone,
    duration_seconds double precision,
    processed_count integer not null default 0,
    approved_count integer not null default 0,
    review_count integer not null default 0,
    failed_count integer not null default 0,
    llm_calls_count integer not null default 0,
    current_stage text not null check (
        current_stage in (
            'INGESTION',
            'NORMALIZATION',
            'GATEKEEPER',
            'PRODUCTION',
            'OPPORTUNITY_ANALYSIS',
            'REVIEW',
            'COMPLETED'
        )
    ),
    status text not null check (
        status in ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'PARTIALLY_COMPLETED')
    ),
    stages jsonb not null default '[]'::jsonb,
    summary jsonb not null default '{}'::jsonb,
    error jsonb,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);

create index if not exists pipeline_runs_started_at_idx
    on public.pipeline_runs (started_at desc);

create index if not exists pipeline_runs_status_idx
    on public.pipeline_runs (status);

create index if not exists pipeline_runs_current_stage_idx
    on public.pipeline_runs (current_stage);

