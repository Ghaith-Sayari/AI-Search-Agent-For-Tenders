from scrapers.registry import discover_scrapers

def run_pipeline():
    print("🚀 Initializing Master Scraper Pipeline...")
    
    # 1. Discover all scrapers dynamically
    scrapers = discover_scrapers()
    print(f"🔍 Found {len(scrapers)} scrapers: {list(scrapers.keys())}")
    
    # 2. Loop through and run each one
    for source_name, scraper_instance in scrapers.items():
        print(f"\n--- Starting {source_name.upper()} ---")
        
        try:
            # Run the scraper logic (returns a list of raw dicts)
            raw_data = scraper_instance.fetch()
            
            if raw_data:
                # Save the file and automatically notify Redis!
                scraper_instance.save_raw_json(raw_data)
                print(f"✅ {source_name} finished. Sent {len(raw_data)} items to queue.")
            else:
                print(f"⚠️ {source_name} returned no data.")
                
        except Exception as e:
            print(f"❌ CRITICAL ERROR in {source_name}: {e}")

if __name__ == "__main__":
    run_pipeline()