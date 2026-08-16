import os
import json
import re
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

class BetaMrScraper(BaseScraper):
    source_name = "beta_mr"
    URL_CIBLE = "https://www.beta-conseils.com/appels-offres"

    def _parse_date(self, text_block):
        months = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc']
        if not text_block:
            return "Unknown"
        for line in text_block.split('\n'):
            if any(m in line.lower() for m in months):
                if any(char.isdigit() for char in line):
                    return line.strip()
        return "Unknown"

    def _parse_posting_date(self, full_page_text):
        if not full_page_text:
            return "Unknown"
        
        # Added \.? to match abbreviated months with dots (e.g., "juil.")
        # Added a fallback match for numeric dates (e.g., 01/07/2026)
        date_pattern = r"(\d{1,2}\s+(?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]*\.?\s+\d{4}|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})"

        # --- STRATEGY 1: Global Text Search (Safest against weird layout line-breaks) ---
        text_clean = " ".join(full_page_text.split())
        markers = ["date de publication", "publié le", "publication"]
        
        for marker in markers:
            match_marker = re.search(r"\b" + re.escape(marker) + r"\b", text_clean, re.IGNORECASE)
            if match_marker:
                # Look up to 100 characters immediately after the found label
                start_pos = match_marker.end()
                sub_text = text_clean[start_pos:start_pos + 100]
                date_match = re.search(date_pattern, sub_text, re.IGNORECASE)
                if date_match:
                    return date_match.group(1).strip()

        # --- STRATEGY 2: Line-by-Line Fallback ---
        lines = [line.strip() for line in full_page_text.split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if any(m in line.lower() for m in markers):
                # Check the current line and up to 3 lines below it
                for j in range(i, min(i + 4, len(lines))):
                    match = re.search(date_pattern, lines[j], re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                        
        return "Unknown"

    def _parse_location(self, text_block, clean_title):
        # Business rule: normalize Beta-MR country to a fixed value.
        return "Mauritania"

    def fetch(self) -> list[dict]:
        """
        The main entry point called by your AI Search Agent / Test Framework.
        Executes synchronously using sync_playwright.
        """
        print("[!] Launching hidden browser backend...")
        final_scraped_data = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            print(f"[!] Navigating to summary portal: {self.URL_CIBLE}")
            page.goto(self.URL_CIBLE, wait_until="load", timeout=60000)
            page.wait_for_timeout(4000)
            
            all_links = page.query_selector_all('a')
            initial_tenders = []
            seen_links = set()
            
            # --- ÉTAPE 1 : EXTRACTION DU PORTAIL SOMMAIRE ---
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
                        
                        tender_id = link_url.split("-")[-1]
                        
                        parent_text = ""
                        try:
                            grandparent_element = link_element.evaluate_handle("el => el.parentElement.parentElement")
                            if grandparent_element:
                                parent_text = grandparent_element.evaluate("el => el.innerText")
                        except Exception:
                            pass
                        
                        clean_title = " ".join(title.split())
                        deadline = self._parse_date(parent_text)
                        location = self._parse_location(parent_text, clean_title)
                        
                        initial_tenders.append({
                            "source": self.source_name,
                            "tender_id": tender_id,
                            "title": clean_title,
                            "location": location,
                            "deadline": deadline,
                            "posting_date": "Unknown",
                            "url_link": link_url
                        })
                except Exception:
                    continue

            print(f"[!] Found {len(initial_tenders)} summary targets. Starting deep-dive text extraction...")
            
            # --- ÉTAPE 2 : EXTRACTION EN PROFONDEUR DES DESCRIPTIONS ---
            detail_page = context.new_page()
            
            print(f"\n=================== DEEP EXTRACTION DISPLAY ===================")
            for index, tender in enumerate(initial_tenders, start=1):
                print(f"[{index}/{len(initial_tenders)}] Fetching ID {tender['tender_id']}: {tender['title'][:40]}...")
                try:
                    detail_page.goto(tender['url_link'], wait_until="load", timeout=30000)
                    detail_page.wait_for_timeout(1500)
                    
                    # Read all text inside the view to scan for fallbacks
                    full_body_text = detail_page.query_selector('body').inner_text().strip()
                    content_element = detail_page.query_selector('.main-content') or detail_page.query_selector('main') or detail_page.query_selector('#content') or detail_page.query_selector('article')
                    
                    if content_element:
                        raw_description = content_element.inner_text().strip()
                        if raw_description.startswith(tender['title']):
                            raw_description = raw_description[len(tender['title']):].strip()
                    else:
                        raw_description = full_body_text
                    
                    tender['description'] = raw_description
                    
                    # --- EXTRACTION OF POSTING DATE (Robust & Fixed regex) ---
                    tender['posting_date'] = self._parse_posting_date(full_body_text)
                    
                    # --- ROBUST DETAIL-PAGE DATE FALLBACK BACKUP FOR DEADLINE ---
                    if tender['deadline'] == "Unknown" or not tender['deadline']:
                        months_extended = ['janv', 'févr', 'mars', 'avr', 'mai', 'juin', 'juil', 'août', 'sept', 'oct', 'nov', 'déc', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
                        
                        # Strategy A: Find the explicit "Date limite" line inside the single document
                        for line in full_body_text.split('\n'):
                            if "date limite" in line.lower() and any(m in line.lower() for m in months_extended):
                                clean_date = re.sub(r'(?i)date limite\s*[:\-]\s*', '', line).strip()
                                tender['deadline'] = clean_date
                                break
                        
                        # Strategy B: Fallback line heading check
                        if tender['deadline'] == "Unknown":
                            for line in full_body_text.split('\n')[:15]:
                                if any(m in line.lower() for m in months_extended) and any(c.isdigit() for c in line):
                                    if len(line.strip()) < 40:
                                        tender['deadline'] = line.strip().strip('-').strip()
                                        break
                    
                    final_scraped_data.append(tender)
                    print(f"   ↳ [✓] Successfully loaded payload. Pub Date: {tender['posting_date']} | Deadline: {tender['deadline']}")
                    
                except Exception as e:
                    print(f"   ↳ [X] Failed to parse: {e}")
                    tender['description'] = "Unavailable due to request timeout."
                    final_scraped_data.append(tender)
                    
            print("============================================================\n")
            browser.close()
            
            # --- ÉTAPE 3 : SAUVEGARDE VIA LE PIPELINE BASE ---
            print("4. Sauvegarde des données brutes...")
            if final_scraped_data:
                saved_file = self.save_raw_json(final_scraped_data)
                print(f"[Succès] Fichier JSON brut enregistré : {saved_file}")
            else:
                print("[!] Aucune donnée à sauvegarder.")

        return final_scraped_data
