from pipeline.normalizer import normalize
from db.client import get_client


def load_all(batch_size: int = 500):

    supabase = get_client()

    records = normalize()

    print(f"[✓] Total normalized records: {len(records)}")

    if not records:
        print("[X] No data to insert")
        return

    # Ensure unique_key exists for ALL records
    for r in records:
        if "unique_key" not in r:
            r["unique_key"] = f"{r['source']}:{r.get('external_id')}"

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


if __name__ == "__main__":
    load_all()