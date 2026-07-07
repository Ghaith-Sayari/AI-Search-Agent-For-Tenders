import json
from pathlib import Path

from pydantic import ValidationError

from mappings.mapper import build_canonical_opportunity

RAW_DIR = Path("data/raw_scrapes")


def normalize_batch(records: list) -> tuple[list, int]:
    """
    Processes a batch of raw records in memory.
    Required by test_scrapers.py to evaluate scrapers on the fly.
    Returns a tuple: (list of valid, hashed, VALIDATED records as dicts, count of dropped records)
    """
    valid = []
    dropped = 0

    for record in records:
        try:
            # map -> hash -> validate, all in one call
            opportunity = build_canonical_opportunity(record)
            valid.append(opportunity.model_dump())
        except ValidationError as e:
            # Record failed the CanonicalOpportunity contract (e.g. blank title)
            dropped += 1
            print(f"  ↳ Rejected record: {e}")
        except Exception as e:
            # Any other unexpected failure (bad source key, malformed dict, etc.)
            dropped += 1
            print(f"  ↳ Error mapping record: {e}")

    return valid, dropped


def normalize():
    """
    Scans the raw data folder, normalizes all JSON files found on disk,
    and deduplicates records ACROSS all files by unique_key before returning.
    """
    all_normalized = []

    for file in RAW_DIR.glob("*.json"):
        print(f"Processing {file.name}")

        try:
            with open(file, encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {file.name}: {e}")
            continue

        valid, dropped = normalize_batch(records)
        all_normalized.extend(valid)

        if dropped > 0:
            print(f"  ↳ Warning: Dropped {dropped} records in {file.name}")

    # Deduplicate across ALL files by unique_key before returning.
    # Without this, two files (or two entries in the same file) sharing
    # the same unique_key would both be sent to the DB in the same upsert
    # batch, which Postgres rejects with:
    #   "ON CONFLICT DO UPDATE command cannot affect row a second time"
    deduped = {}
    for record in all_normalized:
        deduped[record["unique_key"]] = record

    duplicate_count = len(all_normalized) - len(deduped)
    if duplicate_count > 0:
        print(f"[i] Removed {duplicate_count} duplicate record(s) sharing a unique_key")

    return list(deduped.values())


if __name__ == "__main__":
    data = normalize()
    print(f"Normalized {len(data)} records")