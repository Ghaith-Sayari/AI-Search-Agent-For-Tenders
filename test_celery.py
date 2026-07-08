import os
import json
from pipeline.tasks import process_raw_file_task

def test_celery_integration():
    print("--- Starting Celery Queue Test ---")
    
    # 1. Create a dummy scraped batch
    mock_data = [
        {"title": "Test Integration Tender 1", "reference": "SYS-TEST-001"},
        {"title": "Test Integration Tender 2", "reference": "SYS-TEST-002"}
    ]
    
    # 2. Ensure the directory exists and save the mock file
    folder_path = "data/raw_scrapes"
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, "celery_test_batch.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Created mock data file at: {file_path}")
    
    # 3. The Decoupling Action: Send to Queue!
    print("🚀 Pushing task to Redis broker...")
    
    # Calling .delay() triggers the background job
    async_result = process_raw_file_task.delay(file_path=file_path, source_name="test_script")
    
    print(f"✅ Message successfully sent to Redis!")
    print(f"📝 Celery Task ID: {async_result.id}")
    print("👉 Switch over to your Celery Worker terminal window to watch it execute.")

if __name__ == "__main__":
    test_celery_integration()