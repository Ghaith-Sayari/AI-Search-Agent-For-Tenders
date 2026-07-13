create table if not exists public.gatekeeper_decisions (
    id uuid primary key default gen_random_uuid(),
    staging_tender_id uuid not null references public.raw_tender_staging(id),
    unique_key text not null,
    status text not null check (status in ('approved', 'rejected', 'needs_review', 'expired', 'failed')),
    confidence_score double precision not null check (confidence_score >= 0 and confidence_score <= 1),
    decision_reason text not null,
    cleaned_description text,
    extracted_deadline date,
    processed_at timestamp with time zone not null,
    policy_version text not null,
    agent_version text not null,
    created_at timestamp with time zone not null default now()
);

create index if not exists gatekeeper_decisions_staging_tender_id_idx
    on public.gatekeeper_decisions (staging_tender_id);

create index if not exists gatekeeper_decisions_status_idx
    on public.gatekeeper_decisions (status);
