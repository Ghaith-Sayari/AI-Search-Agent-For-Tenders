import os
from dotenv import load_dotenv  # 1. Import the loader
from supabase import create_client, Client

# 2. Load the variables from .env into os.environ
load_dotenv() 

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not key:
            raise ValueError("SUPABASE_KEY is missing from the environment variables!")
            
        _client = create_client(url, key)
    return _client