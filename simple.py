import os
import json
from playwright.sync_api import sync_playwright

def parse_date(text_block):
    months = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc']
    if not text_block:
        return "Unknown"
    for line in text_block.split('\n'):
        if any(m in line.lower() for m in months):
            if any(char.isdigit() for char in line):
                return line.strip()
    return "Unknown"

def parse_location(text_block, clean_title):
    if not text_block:
        return "National / International"
    lines = [line.strip() for line in text_block.split('\n') if line.strip()]
    months = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc']
    mauritian_places = ["nouakchott", "trarza", "brakna", "gorgol", "guidimagha", "hodh", "assaba", "adrar", "tagant", "inchiri", "nouadhibou", "tiszemmour", "rosso"]
    
    for line in lines:
        if any(place in line.lower() for place in mauritian_places):
            return line
    for line in lines:
        if line == clean_title or any(m in line.lower() for m in months) and any(char.isdigit() for char in line):
            continue
        if any(skip in line.lower() for skip in ["en savoir plus", "partager", "télécharger", "détails"]):
            continue
        if 1 <= len(line.split()) <= 4:
            return line
    return "National / International"

def run():
    output_dir = os.path.join("data", "raw_scrapes")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print("[!] Launching hidden browser backend...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url = "https://www.beta-conseils.com/appels-offres"
        print(f"[!] Navigating to summary portal: {url}")
        page.goto(url, wait_until="load", timeout=60000)
        page.wait_for_timeout(4000)
        
        all_links = page.query_selector_all('a')
        initial_tenders = []
        seen_links = set()
        
        for link_element in all_links:
            try:
                link_url = link_element.get_attribute("href")
                if not link_url or len(link_url) < 5 or "appels-offres?c=" in link_url or "javascript" in link_url:
                    continue
                    
                title = link_element.inner_text().strip()
                if len(title) > 20 and not any(skip in title.lower() for skip in ["tous", "connexion", "s'inscrire", "recherche"]):
                    if link_url in seen_links:
                        continue
                    seen_links.add(link_url)
                    
                    if link_url.startswith("/"):
                        link_url = f"https://www.beta-conseils.com{link_url}"
                    elif not link_url.startswith("http"):
                        link_url = f"https://www.beta-conseils.com/{link_url}"
                    
                    # --- ADDED TENDER ID EXTRACTION ---
                    # Splits the URL by dashes and grabs the last element (the trailing number)
                    tender_id = link_url.split("-")[-1]
                    
                    parent_text = ""
                    try:
                        grandparent_element = link_element.evaluate_handle("el => el.parentElement.parentElement")
                        if grandparent_element:
                            parent_text = grandparent_element.evaluate("el => el.innerText")
                    except Exception:
                        pass
                    
                    clean_title = " ".join(title.split())
                    deadline = parse_date(parent_text)
                    location = parse_location(parent_text, clean_title)
                    
                    initial_tenders.append({
                        "tender_id": tender_id,  # Saved safely here
                        "title": clean_title,
                        "location": location,
                        "deadline": deadline,
                        "url_link": link_url
                    })
            except Exception:
                continue

        print(f"[!] Found {len(initial_tenders)} summary targets. Starting deep-dive text extraction...")
        
        detail_page = context.new_page()
        final_scraped_data = []
        
        print(f"\n=================== DEEP EXTRACTION DISPLAY ===================")
        for index, tender in enumerate(initial_tenders, start=1):
            print(f"[{index}/{len(initial_tenders)}] Fetching ID {tender['tender_id']}: {tender['title'][:40]}...")
            try:
                detail_page.goto(tender['url_link'], wait_until="load", timeout=30000)
                detail_page.wait_for_timeout(1500)
                
                content_element = detail_page.query_selector('.main-content') or detail_page.query_selector('main') or detail_page.query_selector('#content') or detail_page.query_selector('article')
                
                if content_element:
                    raw_description = content_element.inner_text().strip()
                    if raw_description.startswith(tender['title']):
                        raw_description = raw_description[len(tender['title']):].strip()
                else:
                    raw_description = detail_page.query_selector('body').inner_text().strip()
                
                tender['description'] = raw_description
                final_scraped_data.append(tender)
                print(f"   ↳ [✓] Successfully loaded description payload.")
                
            except Exception as e:
                print(f"   ↳ [X] Failed to parse: {e}")
                tender['description'] = "Unavailable due to request timeout."
                final_scraped_data.append(tender)
                
        print("============================================================\n")
        
        browser.close()
        
        output_file = os.path.join(output_dir, "beta_mr_clean.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_scraped_data, f, ensure_ascii=False, indent=2)
            
        print(f"[✓] Complete! Clean ingestion file ready at: {output_file}")

if __name__ == "__main__":
    run()