import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

# =============================================================
# CONFIGURATION
# =============================================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing from .env")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is missing from .env")


def search_opportunities(
    search_text: str,
    limit: int = 5,
    threshold: float = 0.75,
):
    # Initialize clients
    supabase: Client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )

    print("[➔] Loading embedding model...")
    model = SentenceTransformer("intfloat/multilingual-e5-base")

    # E5 models require the "query:" prefix
    query = f"query: {search_text}"

    print(f"[➔] Vectorizing '{search_text}'...")
    query_vector = model.encode(query).tolist()

    print("[➔] Searching vector database...")

    try:
        response = (
            supabase.rpc(
                "match_opportunity",
                {
                    "query_embedding": query_vector,
                    "match_threshold": threshold,
                    "match_count": limit,
                },
            )
            .execute()
        )

        results = response.data

        if not results:
            print("No matching opportunities found.")
            return

        print(f"\nFound {len(results)} opportunities:\n")

        for i, item in enumerate(results, start=1):
            print("=" * 80)
            print(f"{i}. {item['title']}")
            print(f"Similarity : {item['similarity']:.3f}")
            print(f"Country    : {item.get('country')}")
            print(f"Posted     : {item.get('posting_date')}")
            print(f"Deadline   : {item.get('deadline')}")
            print(f"Source     : {item.get('source')}")
            print(f"URL        : {item.get('url')}")
            print()

    except Exception as e:
        print(f"[X] Search failed:\n{e}")


if __name__ == "__main__":
    query = input("Search tenders: ").strip()

    if query:
        search_opportunities(query)