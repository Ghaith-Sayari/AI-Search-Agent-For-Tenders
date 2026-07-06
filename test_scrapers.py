import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.registry import discover_scrapers
from pipeline.normalizer import normalize_batch

def test_scrapers():
    scrapers = discover_scrapers()

    if not scrapers:
        print("[X] No scrapers discovered — check scrapers/sources/ folder.")
        return

    print(f"[✓] Discovered {len(scrapers)} scraper(s): {list(scrapers.keys())}\n")

    for name, scraper in scrapers.items():
        print(f"{'─'*50}")
        print(f"[➔] Testing scraper: {name}")

        # ── Health check ──────────────────────────────
        # Assuming is_healthy() is still implemented in your scrapers
        if hasattr(scraper, 'is_healthy'):
            healthy = scraper.is_healthy()
            print(f"    Health check : {'✓ OK' if healthy else '✗ FAILED'}")
            if not healthy:
                print(f"    [!] Skipping {name} — failed health check.")
                continue

        # ── Fetch ─────────────────────────────────────
        try:
            # Returns List[Dict[str, Any]] based on our new base.py
            raw_records = scraper.fetch()
        except FileNotFoundError as e:
            print(f"    [X] JSON file not found: {e}")
            continue
        except Exception as e:
            print(f"    [X] Fetch failed: {e}")
            continue

        print(f"    Raw records  : {len(raw_records)}")

        if not raw_records:
            print(f"    [!] No records returned.")
            continue

        # ── Spot check first RAW record ───────────────────
        print(f"\n    --- First RAW record (Before Pipeline) ---")
        # Pretty-print the dictionary to handle any arbitrary keys the scraper invented
        first_raw = raw_records[0]
        print(json.dumps(first_raw, indent=4, ensure_ascii=False)[:500] + "\n    ... (truncated)")

        # ── Normalizer pass ───────────────────────────
        # Pass the raw dictionaries directly to the pipeline
        valid, dropped = normalize_batch(raw_records)
        
        print(f"\n    --- After normalizer ---")
        print(f"    Valid   : {len(valid)}")
        print(f"    Dropped : {dropped}")

        if not valid:
            print(f"    [!] No valid records after normalization.")
            continue

        # ── Spot check first NORMALIZED record ─────────────
        first = valid[0]
        print(f"\n    --- First NORMALIZED record ---")
        print(f"    title        : {first.get('title')}")
        print(f"    source       : {first.get('source')}")
        print(f"    source_id    : {first.get('source_id')}")
        print(f"    type         : {first.get('type')}")
        print(f"    country      : {first.get('country')}")
        print(f"    posted_date  : {first.get('posted_date')}")
        print(f"    deadline_date: {first.get('deadline_date')}")
        print(f"    url          : {str(first.get('url'))[:60]}...")
        print(f"    unique_key   : {first.get('unique_key')}")

        # ── Unique key collision check ─────────────────
        # Ensure your normalizer is generating the 'unique_key'
        all_keys = [r.get('unique_key') for r in valid if r.get('unique_key')]
        unique_keys = set(all_keys)
        duplicates = len(all_keys) - len(unique_keys)
        
        print(f"\n    Unique keys  : {len(unique_keys)} / {len(valid)}")
        if duplicates:
            print(f"    [!] WARNING: {duplicates} duplicate unique_key(s) detected.")
        elif len(all_keys) < len(valid):
            print(f"    [!] WARNING: Some valid records are missing a 'unique_key'.")
        else:
            print(f"    [✓] No duplicate keys.")

        # ── Missing field report ───────────────────────
        # Done on the valid records since the normalizer enforces the schema
        missing_title    = sum(1 for r in valid if not r.get('title'))
        missing_posted   = sum(1 for r in valid if not r.get('posted_date'))
        missing_deadline = sum(1 for r in valid if not r.get('deadline_date'))
        missing_url      = sum(1 for r in valid if not r.get('url'))
        missing_country  = sum(1 for r in valid if not r.get('country'))

        print(f"\n    --- Missing fields (Normalized Data) ---")
        print(f"    No title        : {missing_title}")
        print(f"    No posted_date  : {missing_posted}")
        print(f"    No deadline_date: {missing_deadline}")
        print(f"    No url          : {missing_url}")
        print(f"    No country      : {missing_country}")

        # ── Type breakdown ────────────────────────────
        types = {}
        for r in valid:
            t = r.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        print(f"\n    Types   : {types}")

        # ── Sector breakdown ──────────────────────────
        sectors = {}
        for r in valid:
            s = r.get("sector") or "unclassified"
            sectors[s] = sectors.get(s, 0) + 1
        print(f"    Sectors : {sectors}")

        print(f"\n    [✓] {name} passed all checks.\n")

if __name__ == "__main__":
    test_scrapers()