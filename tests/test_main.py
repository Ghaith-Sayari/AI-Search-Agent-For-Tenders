import os
import json
import pytest
from scrapers.registry import discover_scrapers
from pipeline.tasks import normalize
from db.loader import load_all

# ============================================================================
# PYTEST FIXTURES (Manages data flow from Web -> Parser -> DB without mocks)
# ============================================================================

@pytest.fixture(scope="module")
def real_scraped_data():
    """
    Harvests actual live data from the internet exactly once.
    This shared payload prevents spamming the target server across multiple tests.
    """
    scrapers = discover_scrapers()
    assert len(scrapers) > 0, "❌ Setup Error: No real scrapers discovered in registry!"
    
    # Target the first active scraper (e.g., beta_mr)
    target_source = list(scrapers.keys())[0]
    scraper = scrapers[target_source]
    
    print(f"\n📡 [FIXTURE] Spawning hidden browser to pull live data from: [{target_source.upper()}]...")
    raw_data = scraper.fetch()
    
    return {
        "source_name": target_source,
        "raw_data": raw_data
    }


@pytest.fixture(scope="module")
def real_normalized_data(real_scraped_data):
    """
    Takes the actual data harvested from the live internet step and 
    runs it through your pipeline normalizer file-system flow.
    """
    source_name = real_scraped_data["source_name"]
    raw_data = real_scraped_data["raw_data"]
    
    assert len(raw_data) > 0, "❌ Pre-requisite Failed: Raw data array is empty. cannot normalize."
    
    # Mimic the main.py save sequence by writing the live raw dump to disk
    test_file_path = os.path.join("data/raw_scrapes", f"live_test_{source_name}.json")
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n⚙️ [FIXTURE] Normalizing real live data file: {test_file_path}")
    try:
        # Run your actual transformation/Pydantic validation layer
        clean_records = normalize(test_file_path, source_name)
        return clean_records
    finally:
        # Cleanup the live test file so it doesn't clutter your workspace
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


# ============================================================================
# THE TEST PIPELINE STAGES
# ============================================================================

def test_stage1_live_fetch(real_scraped_data):
    """
    STAGE 1: Confirms the live web scraper successfully connects, 
    bypasses bot mitigation, and yields true records.
    """
    raw_data = real_scraped_data["raw_data"]
    
    assert raw_data is not None, "❌ Scraper returned None."
    assert isinstance(raw_data, list), "❌ Raw scraper payload must be a list."
    assert len(raw_data) > 0, "❌ Live scrape returned 0 items from the target portal."
    
    print(f"✅ [STAGE 1 PASSED] Verified live scraper functionality. Harvested {len(raw_data)} real items.")


def test_stage2_real_pydantic_mapping(real_normalized_data):
    """
    STAGE 2: Confirms the structural format of the live website matches 
    your Pydantic CanonicalOpportunity schemas without breaking keys or throwing errors.
    """
    assert isinstance(real_normalized_data, list), "❌ Normalizer output must be a list."
    assert len(real_normalized_data) > 0, "❌ All records were dropped or failed schema validation!"
    
    # Inspect the first live parsed record to guarantee schema conversion properties are active
    sample_record = real_normalized_data[0]
    
    # Robust property check whether your normalizer outputs pure dicts or instantiated Pydantic objects
    has_title = hasattr(sample_record, "title") or (isinstance(sample_record, dict) and "title" in sample_record)
    assert has_title, "❌ Normalized real record missing required canonical field 'title'."
    
    print(f"✅ [STAGE 2 PASSED] Real web elements cleanly parsed into Canonical Models.")


def test_stage3_supabase_real_upload(real_normalized_data):
    """
    STAGE 3: Takes a sample subset of your actual live normalized web items 
    and writes them directly into your production Supabase database.
    """
    # Convert Pydantic object instances to pure dicts if needed by your DB loader layer
    prepared_records = []
    for record in real_normalized_data:
        if hasattr(record, "model_dump"):
            prepared_records.append(record.model_dump())
        elif hasattr(record, "dict"):
            prepared_records.append(record.dict())
        else:
            prepared_records.append(record)
            
    # To prevent flooding your DB with 50 test items every run, we slice the first 2 real records
    live_sample_batch = prepared_records[:2]
    print(f"📤 Injecting {len(live_sample_batch)} real web-scraped entries into Supabase...")
    
    db_response = load_all(live_sample_batch)
    
    assert db_response is not None, "❌ Supabase write operation failed or returned null response."
    print("✅ [STAGE 3 PASSED] Live data successfully upserted into your Supabase database tables.")