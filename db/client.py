import os
from supabase import create_client, Client

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "https://vipwfzgzxyaxzwwutpwd.supabase.co")
        key = os.environ.get("SUPABASE_KEY", "sb_publishable_XXJZvKwu0HzticcmqsTslQ_OQsrDgzN")
        _client = create_client(url, key)
    return _client