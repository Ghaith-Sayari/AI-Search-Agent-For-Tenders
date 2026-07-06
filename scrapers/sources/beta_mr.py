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
        
        # Split text into clean, non-empty lines
        lines = [line.strip() for line in full_page_text.split('\n') if line.strip()]
        date_pattern = r"(\d{1,2}\s+(?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]*\s+\d{4})"

        for i, line in enumerate(lines):
            # Locate the sidebar label
            if "date de publication" in line.lower() or "publié le" in line.lower():
                # Check the current line and the next 2 lines below it for the date text
                for j in range(i, min(i + 3, len(lines))):
                    match = re.search(date_pattern, lines[j], re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                        
        return "Unknown"

    def _parse_location(self, text_block, clean_title):
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
                    
                    # 1. Pull the absolute whole body text to ensure we hit sidebars/footers for the metadata
                    whole_page_text = detail_page.query_selector('body').inner_text().strip()
                    
                    # 2. Pull content block purely for the main description payload
                    content_element = detail_page.query_selector('.main-content') or detail_page.query_selector('main') or detail_page.query_selector('#content') or detail_page.query_selector('article')
                    
                    if content_element:
                        raw_description = content_element.inner_text().strip()
                        if raw_description.startswith(tender['title']):
                            raw_description = raw_description[len(tender['title']):].strip()
                    else:
                        raw_description = whole_page_text
                    
                    # Assign parsed fields
                    tender['description'] = raw_description
                    tender['posting_date'] = self._parse_posting_date(whole_page_text)
                    
                    final_scraped_data.append(tender)
                    print(f"   ↳ [✓] Successfully loaded payload. Posting Date: {tender['posting_date']}")
                    
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