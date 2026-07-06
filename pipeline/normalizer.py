import json
from pathlib import Path
from mappings.mapper import map_record

RAW_DIR = Path("data/raw_scrapes")


def normalize_batch(records: list) -> tuple[list, int]:
    """
    Processes a batch of raw records in memory.
    Required by test_scrapers.py to evaluate scrapers on the fly.
    Returns a tuple: (list of valid records, count of dropped records)
    """
    valid = []
    dropped = 0

    for record in records:
        try:
            # Pass the raw dictionary to your existing mapper
            mapped_record = map_record(record)
            valid.append(mapped_record)
        except Exception as e:
            # If mapping fails, track it as a dropped record
            dropped += 1

    return valid, dropped


def normalize():
    """
    Scans the raw data folder and normalizes all JSON files found on disk.
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

        # Reuse the batch logic here to keep code DRY (Don't Repeat Yourself)
        valid, dropped = normalize_batch(records)
        all_normalized.extend(valid)

        if dropped > 0:
            print(f"  ↳ Warning: Dropped {dropped} records in {file.name}")

    return all_normalized


if __name__ == "__main__":
    data = normalize()
    print(f"Normalized {len(data)} records")