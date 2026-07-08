import json
from pydantic import ValidationError
from mappings.mapper import build_canonical_opportunity

def normalize_batch(records: list) -> tuple[list, int]:
    """
    Processes a batch of raw records in memory.
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
            dropped += 1
            print(f"  ↳ Rejected record: {e}")
        except Exception as e:
            dropped += 1
            print(f"  ↳ Error mapping record: {e}")

    return valid, dropped


def normalize(file_path: str, source_name: str) -> list:
    """
    Called by the Celery worker. 
    Opens a specific JSON file, normalizes it, deduplicates internal records, 
    and returns a clean list ready for the database.
    """
    print(f"Processing single file from queue: {file_path}")
    
    try:
        with open(file_path, encoding="utf-8") as f:
            records = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return []

    # Process the batch
    valid, dropped = normalize_batch(records)

    if dropped > 0:
        print(f"  ↳ Warning: Dropped {dropped} records in {file_path}")

    # Deduplicate within this specific file batch by unique_key
    # (Fixes the Postgres 21000 error for duplicate keys in the same batch)
    deduped = {}
    for record in valid:
        deduped[record["unique_key"]] = record

    duplicate_count = len(valid) - len(deduped)
    if duplicate_count > 0:
        print(f"[i] Removed {duplicate_count} internal duplicate record(s) sharing a unique_key")

    return list(deduped.values())