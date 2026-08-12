-- 009_create_generated_proposal.sql

create table if not exists public.generated_proposal (
    id uuid primary key default gen_random_uuid(),
    tender_external_id text,
    profile_name text not null,
    decision text not null check (decision in ('pursue', 'review', 'reject')),
    total_score double precision not null check (total_score >= 0 and total_score <= 1),
    confidence_score double precision not null check (confidence_score >= 0 and confidence_score <= 1),
    executive_summary text not null default '',
    sections jsonb not null default '[]'::jsonb,
    compliance_issues jsonb not null default '[]'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    markdown text not null default '',
    generated_at timestamp with time zone not null default now(),
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now()
);

create index if not exists generated_proposal_generated_at_idx
    on public.generated_proposal (generated_at desc);

create index if not exists generated_proposal_decision_idx
    on public.generated_proposal (decision);

create index if not exists generated_proposal_profile_name_idx
    on public.generated_proposal (profile_name);

-- Storage bucket for proposal artifacts (.md + .json)
insert into storage.buckets (id, name, public)
select 'proposal-files', 'proposal-files', false
where not exists (
    select 1 from storage.buckets where id = 'proposal-files'
);

-- Optional RLS policies for authenticated app usage.
do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname = 'storage'
          and tablename = 'objects'
          and policyname = 'proposal_files_select_authenticated'
    ) then
        execute $sql$
            create policy proposal_files_select_authenticated
            on storage.objects
            for select
            to authenticated
            using (bucket_id = 'proposal-files')
        $sql$;
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'storage'
          and tablename = 'objects'
          and policyname = 'proposal_files_insert_authenticated'
    ) then
        execute $sql$
            create policy proposal_files_insert_authenticated
            on storage.objects
            for insert
            to authenticated
            with check (bucket_id = 'proposal-files')
        $sql$;
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'storage'
          and tablename = 'objects'
          and policyname = 'proposal_files_update_authenticated'
    ) then
        execute $sql$
            create policy proposal_files_update_authenticated
            on storage.objects
            for update
            to authenticated
            using (bucket_id = 'proposal-files')
            with check (bucket_id = 'proposal-files')
        $sql$;
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname = 'storage'
          and tablename = 'objects'
          and policyname = 'proposal_files_delete_authenticated'
    ) then
        execute $sql$
            create policy proposal_files_delete_authenticated
            on storage.objects
            for delete
            to authenticated
            using (bucket_id = 'proposal-files')
        $sql$;
    end if;
end
$$;
