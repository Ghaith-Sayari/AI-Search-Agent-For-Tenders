create table if not exists public.production_tender (
    id uuid primary key default gen_random_uuid(),
    unique_key text not null unique,
    source text not null,
    title text not null,
    country text,
    posting_date text,
    deadline date not null,
    url text,
    description text,
    external_id text,
    staging_tender_id uuid not null references public.raw_tender_staging(id),
    gatekeeper_decision_id uuid references public.gatekeeper_decisions(id),
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);

create index if not exists production_tender_deadline_idx
    on public.production_tender (deadline);

create index if not exists production_tender_staging_tender_id_idx
    on public.production_tender (staging_tender_id);
