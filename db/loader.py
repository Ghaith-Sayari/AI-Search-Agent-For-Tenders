from db.client import get_client


def load_all(records: list[dict], batch_size: int = 500):

    supabase = get_client()
    result = {
        "attempted": len(records),
        "inserted_batches": 0,
        "failed_batches": 0,
        "errors": [],
    }

    print(f"[OK] Total normalized records: {len(records)}")

    if not records:
        print("[WARN] No data to insert")
        return result

    # Insert in batches
    for i in range(0, len(records), batch_size):

        batch = records[i:i + batch_size]

        print(f"\n[INFO] Inserting batch {i//batch_size + 1} ({len(batch)} records)")

        try:
            res = (
                supabase
                .table("raw_tender_staging")
                .upsert(batch, on_conflict="unique_key")
                .execute()
            )

            print(f"[OK] Batch {i//batch_size + 1} inserted")
            result["inserted_batches"] += 1

        except Exception as e:
            print(f"[ERR] Batch failed {i//batch_size + 1}")
            print(e)
            result["failed_batches"] += 1
            result["errors"].append(
                {
                    "batch": i // batch_size + 1,
                    "batch_size": len(batch),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

    return result
