import os
from celery import Celery
# Import your existing normalizer and loader logic
from pipeline.normalizer import normalize
from db.loader import load_all

# 1. Initialize Celery and point it to your local Redis instance
# 'redis://localhost:6379/0' means connect to Redis on the default port, database 0
app = Celery('tender_pipeline', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_raw_file_task(self, file_path: str, source_name: str):
    """
    Background worker task. It receives a file path, opens it,
    runs data governance checks, and upserts to Supabase.
    """
    print(f"[WORKER] Received task for source '{source_name}'. File: {file_path}")
    
    # Safety Check: Verify the file actually exists on disk before reading it
    if not os.path.exists(file_path):
        print(f"[WORKER ERROR] File not found: {file_path}. Task dropped.")
        return f"ERROR: File {file_path} missing"

    try:
        # 2. Call your existing robust normalizer logic 
        # This maps, hashes, runs Pydantic, and returns clean, deduped records
        clean_records = normalize(file_path, source_name)
        
        if not clean_records:
            print(f"[WORKER] File {file_path} contained no valid records or was empty.")
            return "SUCCESS: Empty Batch"

        # 3. Call your existing loader logic to bulk UPSERT into Supabase
        load_all(clean_records)

        print(f"[WORKER SUCCESS] Successfully ingested {len(clean_records)} records from {file_path}")
        return f"SUCCESS: Ingested {len(clean_records)} items"

    except Exception as exc:
        print(f"[WORKER CRITICAL] Pipeline failed processing {file_path}. Retrying... Error: {exc}")
        # If Supabase is down or a temporary network glitch occurs, retry the task in 60 seconds
        raise self.retry(exc=exc)