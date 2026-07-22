alter table public.opportunity_analysis
    add column if not exists blocker_evidence jsonb not null default '{}'::jsonb,
    add column if not exists budget_source text not null default 'unknown',
    add column if not exists budget_eur double precision,
    add column if not exists budget_range_min_eur double precision,
    add column if not exists budget_range_max_eur double precision;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'opportunity_analysis_budget_source_check'
    ) then
        alter table public.opportunity_analysis
            add constraint opportunity_analysis_budget_source_check
            check (budget_source in ('extracted', 'estimated', 'unknown')) not valid;
    end if;
end $$;
