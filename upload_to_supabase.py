import os
import datetime
from supabase import create_client, Client

def upload_all_raw_scrapes():
    # =============================================================
    # 1. CONFIGURATION - Paste your Supabase details here
    # =============================================================
    SUPABASE_URL = "https://vipwfzgzxyaxzwwutpwd.supabase.co"       # e.g., https://xyz.supabase.co
    SUPABASE_KEY = "sb_publishable_XXJZvKwu0HzticcmqsTslQ_OQsrDgzN"  # Starts with sb_publishable_...
    BUCKET_NAME = "raw-tenders"                        # The bucket you created in Storage
    
    # Target directory where your scrapers save their raw data
    target_dir = os.path.join("data", "raw_scrapes")
    # =============================================================

    # Check if the local folder even exists yet
    if not os.path.exists(target_dir):
        print(f"[X] Error: Local folder '{target_dir}' does not exist.")
        print("    Run your scrapers first so they create this folder and save data into it!")
        return

    # Initialize the secure cloud connection
    print("[!] Authenticating connection to your Supabase cloud data lake...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get today's date to timestamp the files (e.g., "2026-06-23")
    today_str = datetime.date.today().isoformat()
    
    # List all files inside data/raw_scrapes
    all_files = os.listdir(target_dir)
    json_files = [f for f in all_files if f.endswith('.json')]
    
    if not json_files:
        print(f"[-] No JSON files found inside '{target_dir}' to upload.")
        return

    print(f"[✓] Found {len(json_files)} JSON file(s) ready for cloud sync.\n")

    # Loop through each JSON file and push it up
    for file_name in json_files:
        local_file_path = os.path.join(target_dir, file_name)
        cloud_file_name = f"{today_str}_{file_name}"
        
        print(f"[!] Uploading: {file_name} ➔ Bucket: {BUCKET_NAME}/{cloud_file_name}")
        
        try:
            # Read the JSON file as binary bytes
            with open(local_file_path, 'rb') as f:
                file_data = f.read()

            # Fire it to the cloud bucket
            supabase.storage.from_(BUCKET_NAME).upload(
                path=cloud_file_name,
                file=file_data,
                file_options={"content-type": "application/json"}
            )
            print(f"    ↳ [✓] Successfully uploaded {file_name}!")
            
        except Exception as e:
            print(f"    ↳ [X] Failed to upload {file_name}!")
            print(f"        Error Message: {e}")

    print("\n====================== SYNC PROCESS COMPLETE ======================")
    print(f"[✓] Check your Supabase Storage dashboard under '{BUCKET_NAME}' to see them!")
    print("===================================================================")

if __name__ == "__main__":
    upload_all_raw_scrapes()