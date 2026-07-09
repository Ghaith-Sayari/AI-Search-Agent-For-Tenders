import os
from celery import Celery
from kombu import Queue  # <--- Import this to handle queue structures
from pipeline.normalizer import normalize
from db.loader import load_all

# 1. Initialize Celery pointing to your Redis broker
app = Celery('tender_pipeline', broker='redis://localhost:6379/0')

# 2. Configure explicit Queue Lanes inside Redis
app.conf.task_queues = (
    Queue('default', routing_key='task.#'),
    Queue('dead_letter', routing_key='dead.#'),
)

# Set the default queue lane for normal operations
app.conf.task_default_queue = 'default'


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_raw_file_task(self, file_path: str, source_name: str):
    """
    Background worker task. Processes data and automatically 
    routes itself to the dead_letter queue if it fails 3 times.
    """
    print(f"[WORKER] Received task for source '{source_name}'. File: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[WORKER ERROR] File not found: {file_path}. Task dropped.")
        return f"ERROR: File {file_path} missing"

    try:
        # Step A: Run normalizer logic
        clean_records = normalize(file_path, source_name)
        
        if not clean_records:
            print(f"[WORKER] File {file_path} contained no valid records or was empty.")
            return "SUCCESS: Empty Batch"

        # Step B: Bulk UPSERT into Supabase
        load_all(clean_records)
        
        print(f"[WORKER SUCCESS] Ingested records from {file_path}")
        return f"SUCCESS: Ingested items"

    except Exception as exc:
        # Check if we have exhausted all 3 attempts
        if self.request.retries >= self.max_retries:
            print(f"[DLQ CRITICAL] Task completely failed after {self.max_retries} attempts. Routing to Dead-Letter Queue!")
            
            # Programmatic DLQ Hand-off: Send a copy of the payload to the 'dead_letter' queue
            app.send_task(
                'pipeline.tasks.process_raw_file_task',
                args=[file_path, source_name],
                queue='dead_letter'
            )
            return f"FAILED: Sent to DLQ. Error: {exc}"
            
        print(f"[WORKER WARNING] Task failed. Retrying in 60s (Attempt {self.request.retries + 1}/{self.max_retries})...")
        raise self.retry(exc=exc)