alter table public.gatekeeper_decisions
    add column if not exists document_type text,
    add column if not exists country_seen text,
    add column if not exists title_evidence text,
    add column if not exists description_evidence text,
    add column if not exists deadline_evidence text,
    add column if not exists missing_required_fields jsonb not null default '[]'::jsonb,
    add column if not exists model_name text,
    add column if not exists input_payload jsonb not null default '{}'::jsonb,
    add column if not exists raw_model_output text;

alter table public.gatekeeper_decisions
    add constraint gatekeeper_decisions_document_type_check
    check (document_type in ('solicitation', 'transaction', 'outcome', 'portal_page', 'unknown')) not valid;
