from db.client import get_client


def upsert_batch(batch: list[dict]) -> None:
    """
    Upsert a batch of normalized records into Supabase.
    """

    if not batch:
        print("[-] No records to upsert")
        return

    supabase = get_client()

    print(f"[➔] Upserting {len(batch)} records...")

    try:
        (
            supabase
            .table("opportunity")
            .upsert(
                batch,
                on_conflict="unique_key"
            )
            .execute()
        )

        print(f"[✓] Successfully upserted {len(batch)} records")

    except Exception as e:
        print(f"[X] Failed to upsert batch")
        print(f"    Error: {e}")