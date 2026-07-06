import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing from .env")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing from .env")


def main():
    # Initialize Supabase
    supabase: Client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )

    # Load embedding model
    print("[➔] Loading multilingual-e5-base...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")

    print("[➔] Fetching opportunities without embeddings...")

    response = (
        supabase.table("opportunity")
        .select("unique_key,title,description,country")
        .is_("embedding", "null")
        .execute()
    )

    rows = response.data

    if not rows:
        print("[✓] All opportunities already have embeddings.")
        return

    print(f"[*] Found {len(rows)} opportunities.")

    updated = 0

    for row in rows:
        text = (
            f"passage: "
            f"Title: {row.get('title') or ''}. "
            f"Description: {row.get('description') or ''}. "
            f"Country: {row.get('country') or ''}."
        )

        try:
            embedding = model.encode(text).tolist()

            (
                supabase.table("opportunity")
                .update({"embedding": embedding})
                .eq("unique_key", row["unique_key"])
                .execute()
            )

            updated += 1

            print(f"[✓] {updated}/{len(rows)} - {row['title'][:50]}")

        except Exception as e:
            print(f"[X] Failed for {row['unique_key']}: {e}")

    print(f"\n[✓] Finished! Updated {updated} opportunities.")


if __name__ == "__main__":
    main()