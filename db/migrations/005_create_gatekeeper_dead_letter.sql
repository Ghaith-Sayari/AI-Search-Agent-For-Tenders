create table if not exists public.gatekeeper_dead_letter (
    id uuid primary key default gen_random_uuid(),
    unique_key text not null,
    policy_version text not null,
    stage text not null,
    error_type text not null,
    error_message text not null,
    retry_count integer not null default 0,
    source_table text,
    raw_payload jsonb,
    last_seen_at timestamp with time zone not null default now(),
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    constraint gatekeeper_dead_letter_unique_key_policy_version_unique
        unique (unique_key, policy_version)
);

create index if not exists gatekeeper_dead_letter_stage_idx
    on public.gatekeeper_dead_letter (stage);

create index if not exists gatekeeper_dead_letter_last_seen_at_idx
    on public.gatekeeper_dead_letter (last_seen_at);

