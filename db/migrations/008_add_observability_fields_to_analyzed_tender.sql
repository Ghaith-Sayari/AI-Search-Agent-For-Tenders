alter table public.analyzed_tender
    add column if not exists llm_status text not null default 'unknown',
    add column if not exists llm_error text,
    add column if not exists matched_keywords jsonb not null default '[]'::jsonb,
    add column if not exists location_match_type text not null default 'unknown';

create index if not exists analyzed_tender_llm_status_idx
    on public.analyzed_tender (llm_status);

create index if not exists analyzed_tender_location_match_type_idx
    on public.analyzed_tender (location_match_type);
