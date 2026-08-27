create table if not exists public.offer_notification_queue (
    id uuid primary key default gen_random_uuid(),
    event_key text not null default 'valid_offers_score_gt_70',
    offer_id uuid references public.analyzed_tender(id) on delete set null,
    reason text not null default 'eligible_offer_change',
    payload jsonb not null default '{}'::jsonb,
    status text not null default 'pending' check (status in ('pending', 'processing', 'sent', 'failed')),
    attempts integer not null default 0 check (attempts >= 0),
    last_error text,
    provider_response text,
    created_at timestamp with time zone not null default now(),
    processing_started_at timestamp with time zone,
    processed_at timestamp with time zone
);

create index if not exists offer_notification_queue_status_created_idx
    on public.offer_notification_queue (status, created_at);

create table if not exists public.offer_notification_state (
    event_key text primary key,
    last_snapshot_hash text,
    last_sent_count integer not null default 0,
    last_sent_at timestamp with time zone,
    updated_at timestamp with time zone not null default now()
);

insert into public.offer_notification_state (event_key)
values ('valid_offers_score_gt_70')
on conflict (event_key) do nothing;

create or replace function public.is_offer_eligible_for_email(
    in_deadline date,
    in_total_score double precision
)
returns boolean
language sql
stable
as $$
    select coalesce(in_deadline >= current_date, false)
       and coalesce(in_total_score > 70, false);
$$;

create or replace function public.enqueue_offer_notification_if_eligible()
returns trigger
language plpgsql
as $$
declare
    new_eligible boolean;
    old_eligible boolean;
begin
    new_eligible := public.is_offer_eligible_for_email(new.deadline, new.total_score);

    if tg_op = 'INSERT' then
        if new_eligible then
            insert into public.offer_notification_queue (offer_id, reason, payload)
            values (
                new.id,
                'insert_eligible',
                jsonb_build_object(
                    'title', new.title,
                    'total_score', new.total_score,
                    'deadline', new.deadline
                )
            );
        end if;
        return new;
    end if;

    old_eligible := public.is_offer_eligible_for_email(old.deadline, old.total_score);

    if new_eligible and (
        not old_eligible
        or old.total_score is distinct from new.total_score
        or old.deadline is distinct from new.deadline
        or old.title is distinct from new.title
    ) then
        insert into public.offer_notification_queue (offer_id, reason, payload)
        values (
            new.id,
            case when old_eligible then 'update_eligible' else 'became_eligible' end,
            jsonb_build_object(
                'title', new.title,
                'total_score', new.total_score,
                'deadline', new.deadline
            )
        );
    end if;

    return new;
end;
$$;

drop trigger if exists analyzed_tender_offer_notification_trigger on public.analyzed_tender;

create trigger analyzed_tender_offer_notification_trigger
after insert or update of total_score, deadline, title
on public.analyzed_tender
for each row
execute function public.enqueue_offer_notification_if_eligible();
