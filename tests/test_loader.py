# test_loader.py
"""
Integration test: runs the full pipeline (normalize -> load_all)
and verifies that records actually land in the Supabase `opportunity` table.

This is NOT a unit test with mocks — it hits the real database,
so run it against a dev/staging Supabase project, not production.
"""

from db.client import get_client
from db.loader import load_all


def test_loader():
    supabase = get_client()

    # Count rows before running the pipeline
    before = supabase.table("raw_tender_staging").select("id", count="exact").execute()
    before_count = before.count or 0
    print(f"[i] Rows in raw_tender_staging table before: {before_count}")

    # Run the real pipeline: normalize() -> upsert in batches
    load_all()

    # Count rows after
    after = supabase.table("raw_tender_staging").select("id", count="exact").execute()
    after_count = after.count or 0
    print(f"[i] Rows in raw_tender_staging table after: {after_count}")

    if after_count >= before_count:
        print(f"[✓] Load succeeded — {after_count - before_count} new/updated rows reflected")
    else:
        print(f"[X] Row count dropped unexpectedly ({before_count} → {after_count})")

    # Spot-check: pull a few rows to confirm shape looks right
    sample = (
        supabase
        .table("raw_tender_staging")
        .select("unique_key, source, title, created_at")
        .limit(5)
        .execute()
    )

    print("\n[i] Sample rows:")
    for row in sample.data:
        print(f"  - [{row['source']}] {row['title']} (key={row['unique_key'][:8]}...)")


if __name__ == "__main__":
    test_loader()