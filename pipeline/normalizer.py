import json
from pathlib import Path

from mappings.mapper import map_record

RAW_DIR = Path("data/raw_scrapes")


def normalize():
    normalized = []

    for file in RAW_DIR.glob("*.json"):

        print(f"Processing {file.name}")

        with open(file, encoding="utf-8") as f:
            records = json.load(f)

        for record in records:
            try:
                normalized.append(map_record(record))
            except Exception as e:
                print(f"Error mapping record in {file.name}: {e}")

    return normalized


if __name__ == "__main__":
    data = normalize()
    print(f"Normalized {len(data)} records")
    print(data)