import os
import json
import re
import hashlib
import datetime
from dateutil import parser
from supabase import create_client, Client

# =============================================================
# CONFIGURATION
# =============================================================
SUPABASE_URL = "https://vipwfzgzxyaxzwwutpwd.supabase.co"
SUPABASE_KEY = "sb_publishable_XXJZvKwu0HzticcmqsTslQ_OQsrDgzN"
TARGET_DIR = os.path.join("data", "raw_scrapes")
# =============================================================

def make_unique_key(source: str, identifier: str) -> str:
    """MD5 hash of source:identifier to guarantee uniqueness."""
    raw = f"{source}:{identifier}"
    return hashlib.md5(raw.encode()).hexdigest()

def clean_date(date_string):
    if not date_string or "Unknown" in str(date_string):
        return None
    try:
        french_months = {
            'janv.': 'Jan', 'févr.': 'Feb', 'mars': 'Mar', 'avr.': 'Apr',
            'mai': 'May', 'juin': 'Jun', 'juil.': 'Jul', 'août': 'Aug',
            'sept.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'déc.': 'Dec'
        }
        for fr, en in french_months.items():
            date_string = date_string.replace(fr, en)
        parsed = parser.parse(date_string, fuzzy=True)
        return parsed.date().isoformat()
    except Exception:
        return None

def extract_posted_date(description_text: str):
    """Extract 'Date de publication' from beta_mr description block."""
    match = re.search(r'Date de publication\s+(\d{1,2}\s+\w+\.?\s+\d{4})', description_text)
    if match:
        return clean_date(match.group(1))
    return None

def extract_issuer(description_text: str, fallback: str = None):
    """
    Try to extract issuer name from beta_mr structured description.
    Looks for the org name after the title line before 'Date limite'.
    Falls back to the location field.
    """
    lines = [l.strip() for l in description_text.split('\n') if l.strip()]
    for i, line in enumerate(lines):
        if 'Date limite' in line and i >= 1:
            return lines[i - 1]
    return fallback

def parse_beta_mr_emploi_block(description_text: str, source_url: str) -> list:
    """
    Parse the large 'emploi' summary block into individual job opportunity rows.
    Maps to the opportunity table schema.
    """
    rows = []
    lines = [l.strip() for l in description_text.split('\n') if l.strip()]

    for i, line in enumerate(lines):
        if re.search(r'\d{1,2}\s+\w+\.?\s+\d{4}$', line):
            try:
                if i >= 2:
                    title     = lines[i - 2]
                    issuer    = lines[i - 1]
                    raw_date  = line
                    identifier = f"{title}_{issuer}"
                    unique_key = make_unique_key("beta_mr", identifier)

                    rows.append({
                        "unique_key":    unique_key,
                        "source_id":     None,
                        "source":        "beta_mr",
                        "type":          "job",
                        "title":         title,
                        "description":   "Extrait de la page offres d'emploi Beta Conseils.",
                        "url":           source_url,
                        "country":       "Mauritania",
                        "location":      None,
                        "issuer_name":   issuer,
                        "posted_date":   None,
                        "deadline_date": clean_date(raw_date),
                        "deadline_raw":  raw_date,
                    })
            except Exception:
                continue
    return rows

def process_and_load_data():
    if not os.path.exists(TARGET_DIR):
        print(f"[X] Directory '{TARGET_DIR}' not found.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    json_files = [f for f in os.listdir(TARGET_DIR) if f.endswith('.json')]

    if not json_files:
        print("[-] No JSON files found.")
        return

    for file_name in json_files:
        file_path  = os.path.join(TARGET_DIR, file_name)
        is_beta_mr = "beta_mr" in file_name.lower()

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                raw_data = json.load(f)
            except json.JSONDecodeError:
                print(f"[X] Invalid JSON: {file_name}")
                continue

        records   = raw_data if isinstance(raw_data, list) else [raw_data]
        batch     = []
        seen_keys = set()

        # ── BETA_MR ──────────────────────────────────────────────────────────
        if is_beta_mr:
            for item in records:
                tender_id = str(item.get("tender_id", ""))

                # Skip registration page
                if tender_id == "register":
                    continue

                # Jobs summary block
                if tender_id == "emploi":
                    jobs = parse_beta_mr_emploi_block(
                        item.get("description", ""),
                        item.get("url_link", "")
                    )
                    for job in jobs:
                        if job["unique_key"] not in seen_keys:
                            seen_keys.add(job["unique_key"])
                            batch.append(job)

                # Structured tenders (4497, 4498, …)
                else:
                    title = item.get("title", "").strip()
                    if not title or title == "Ajoutez votre entreprise":
                        continue

                    url        = item.get("url_link", "")
                    raw_date   = item.get("deadline")
                    desc       = item.get("description", "")
                    unique_key = make_unique_key("beta_mr", tender_id if tender_id else url)

                    if unique_key not in seen_keys:
                        seen_keys.add(unique_key)
                        batch.append({
                            "unique_key":    unique_key,
                            "source_id":     tender_id,
                            "source":        "beta_mr",
                            "type":          "tender",
                            "title":         title,
                            "description":   desc,
                            "url":           url,
                            "country":       "Mauritania",
                            "location":      item.get("location"),
                            "issuer_name":   extract_issuer(desc, fallback=item.get("location")),
                            "posted_date":   extract_posted_date(desc),
                            "deadline_date": clean_date(raw_date),
                            "deadline_raw":  raw_date,
                        })

        # ── TENDERSONTIME ─────────────────────────────────────────────────────
        else:
            for item in records:
                ref = item.get("TOT Reference") or item.get("tender_id")
                if not ref:
                    continue

                url        = item.get("Lien de l'offre", "")
                raw_date   = item.get("Deadline")
                country    = item.get("Pays", "Unknown")
                posted     = item.get("Posting Date")
                unique_key = make_unique_key("tendersontime", str(ref) if ref else url)

                if unique_key not in seen_keys:
                    seen_keys.add(unique_key)
                    batch.append({
                        "unique_key":    unique_key,
                        "source_id":     str(ref),
                        "source":        "tendersontime",
                        "type":          "tender",
                        "title":         item.get("Titre", "No Title"),
                        "description":   f"Country: {country}. Posted: {posted}.",
                        "url":           url,
                        "country":       country,
                        "location":      None,
                        "issuer_name":   None,
                        "posted_date":   clean_date(posted),
                        "deadline_date": clean_date(raw_date),
                        "deadline_raw":  raw_date,
                    })

        # ── UPSERT TO SUPABASE ────────────────────────────────────────────────
        if batch:
            print(f"\n[➔] Upserting {len(batch)} rows from '{file_name}'...")
            try:
                supabase.table("opportunity").upsert(
                    batch,
                    on_conflict="unique_key"
                ).execute()
                print(f"    [✓] Done — {file_name}")
            except Exception as e:
                print(f"    [X] Failed: {file_name}\n        Error: {e}")
        else:
            print(f"[-] No valid records in '{file_name}'")

if __name__ == "__main__":
    process_and_load_data()