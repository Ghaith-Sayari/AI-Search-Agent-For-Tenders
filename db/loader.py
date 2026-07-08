from db.client import get_client


def load_all(records: list, batch_size: int = 500):

    supabase = get_client()

    print(f"[✓] Total normalized records: {len(records)}")

    if not records:
        print("[X] No data to insert")
        return

    # Insert in batches
    for i in range(0, len(records), batch_size):

        batch = records[i:i + batch_size]

        print(f"\n[→] Inserting batch {i//batch_size + 1} ({len(batch)} records)")

        try:
            res = (
                supabase
                .table("opportunity")
                .upsert(batch, on_conflict="unique_key")
                .execute()
            )

            print(f"[✓] Batch {i//batch_size + 1} inserted")

        except Exception as e:
            print(f"[X] Batch failed {i//batch_size + 1}")
            print(e)
