import hashlib

def generate_unique_key(title: str, source: str, external_id: str = "") -> str:
    """
    Deterministic key. Uses external_id when available (most reliable,
    since it's the source site's own reference number), falling back
    to title+source alone if external_id is missing.
    """
    if external_id:
        salt = f"{external_id.strip().lower()}_{source.strip().lower()}"
    else:
        salt = f"{title.strip().lower()}_{source.strip().lower()}"
    return hashlib.md5(salt.encode()).hexdigest()