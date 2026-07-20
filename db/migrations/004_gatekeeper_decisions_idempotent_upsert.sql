create unique index if not exists gatekeeper_decisions_unique_key_policy_version_uidx
    on public.gatekeeper_decisions (unique_key, policy_version);

