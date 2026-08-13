from scrapers.registry import discover_scrapers


def run_pipeline():
    print("Initializing Master Scraper Pipeline...")

    # 1. Discover all scrapers dynamically
    scrapers = discover_scrapers()
    print(f"Found {len(scrapers)} scrapers: {list(scrapers.keys())}")

    # 2. Loop through and run each one
    for source_name, scraper_instance in scrapers.items():
        print(f"\n--- Starting {source_name.upper()} ---")

        try:
            # Run the scraper logic (returns a list of raw dicts).
            # Each scraper is responsible for one save_raw_json() call.
            raw_data = scraper_instance.fetch()

            if raw_data:
                print(f"{source_name} finished. Collected {len(raw_data)} items.")
            else:
                print(f"{source_name} returned no data.")

        except Exception as e:
            print(f"CRITICAL ERROR in {source_name}: {e}")


if __name__ == "__main__":
    run_pipeline()
