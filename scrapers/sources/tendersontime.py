import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright
from scrapers.base import BaseScraper

class TendersOnTimeScraper(BaseScraper):
    source_name = "tendersontime"
    URL_CIBLE = "https://www.tendersontime.com/africa-tenders/"

    def format_date(self, date_str):
        """Convertit '23 Jun 2026' en '23/6/2026'"""
        try:
            date_str = " ".join(date_str.split()).strip()
            dt = datetime.strptime(date_str, "%d %b %Y")
            return f"{dt.day}/{dt.month}/{dt.year}"
        except Exception:
            return date_str

    def fetch(self) -> list[dict]:
        """
        The main entry point called by your AI Search Agent.
        Because Playwright is async, we wrap it in asyncio.run() here.
        """
        return asyncio.run(self._scrape_tenders())

    async def _scrape_tenders(self) -> list[dict]:
        async with async_playwright() as p:
            print("1. Lancement du navigateur en arrière-plan...")
            browser = await p.chromium.launch(headless=True) 
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # --- ÉTAPE 1 : COLLECTE LIMITÉE À 50 OFFRES ---
            print(f"2. Récupération des 50 derniers liens sur : {self.URL_CIBLE}...")
            try:
                # `networkidle` can hang on pages with long-polling/ads.
                await page.goto(self.URL_CIBLE, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                # One fallback attempt with a less strict readiness condition.
                await page.goto(self.URL_CIBLE, wait_until="load", timeout=60000)
            
            preliminary_tenders = []
            seen_references = set()
            page_num = 1
            limite_atteinte = False
            
            while not limite_atteinte:
                print(f"   -> Scan de la Page {page_num} (Trouvés : {len(preliminary_tenders)}/50)...", end="\r")
                await page.wait_for_timeout(1500)
                
                cards = await page.query_selector_all("div, li, tr")
                
                for card in cards:
                    if len(preliminary_tenders) >= 50:
                        limite_atteinte = True
                        break
                        
                    text = await card.inner_text()
                    text_clean = " ".join(text.split()).strip()
                    
                    if "TOT Ref" in text_clean and "Deadline" in text_clean:
                        ref_match = re.search(r"TOT Ref(?:erence)?\s*No\.?:\s*(\d+)", text_clean)
                        if not ref_match:
                            continue
                            
                        tot_ref = ref_match.group(1)
                        if tot_ref in seen_references:
                            continue
                        seen_references.add(tot_ref)
                        
                        link_elem = await card.query_selector("a:has-text('View Details')")
                        detail_url = None
                        if link_elem:
                            detail_url = await link_elem.get_attribute("href")
                            if detail_url and detail_url.startswith("/"):
                                detail_url = f"https://www.tendersontime.com{detail_url}"
                        
                        deadline_match = re.search(r"Deadline:\s*([\d]+\s+[A-Za-z]+\s+[\d]{4})", text_clean)
                        raw_deadline = deadline_match.group(1).strip() if deadline_match else ""
                        formatted_deadline = self.format_date(raw_deadline) if raw_deadline else "N/A"
                        
                        title = text_clean.split("Deadline:")[0].strip()
                        
                        country = "N/A"
                        if raw_deadline:
                            right_side = text_clean.split(raw_deadline)[1].strip()
                            country_match = re.search(r"^([A-Za-z\s\-\.]+?)(?=\s*TOT Ref|\s*View Details|$)", right_side)
                            if country_match:
                                country = country_match.group(1).strip()

                        # Initializing the raw dictionary structure with a single Description field
                        preliminary_tenders.append({
                            "source": self.source_name,
                            "Titre": title,
                            "Pays": country,
                            "Posting Date": "N/A",
                            "Deadline": formatted_deadline,
                            "TOT Reference": tot_ref,
                            "Lien de l'offre": detail_url,
                            "Description": "N/A"  # All extra information will be loaded here
                        })
                
                if limite_atteinte:
                    break
                    
                next_button = await page.query_selector("a:has-text('Next'):visible, button:has-text('Next'):visible")
                if next_button:
                    is_disabled = await next_button.get_attribute("disabled") or await next_button.get_attribute("class")
                    if is_disabled and ("disabled" in is_disabled.lower() or "inactive" in is_disabled.lower()):
                        break
                    try:
                        await next_button.click(force=True, timeout=5000)
                        await page.wait_for_load_state("networkidle")
                        page_num += 1
                    except Exception:
                        break
                else:
                    break
                    
            # --- ÉTAPE 2 : EXTRACTION DU TEXTE DE DESCRIPTION COMPLET ---
            print(f"\n\n3. Visite ciblée des {len(preliminary_tenders)} pages de détails...")
            
            detail_page = await context.new_page()
            for index, tender in enumerate(preliminary_tenders):
                if not tender["Lien de l'offre"]:
                    continue
                    
                print(f"   -> [{index+1}/{len(preliminary_tenders)}] Extraction Description Ref: {tender['TOT Reference']}...", end="\r")
                try:
                    await detail_page.goto(tender["Lien de l'offre"], wait_until="domcontentloaded", timeout=10000)
                    
                    body_elem = await detail_page.query_selector("body")
                    if body_elem:
                        raw_text = await body_elem.inner_text()
                        clean_text = " ".join(raw_text.split())
                        
                        # Extract and format Posting Date natively
                        posting_match = re.search(r"Posting\s*Date\s*:\s*([\d]+\s+[A-Za-z]+\s+[\d]{4})", clean_text, re.IGNORECASE)
                        if posting_match:
                            tender["Posting Date"] = self.format_date(posting_match.group(1))
                        else:
                            alternative_match = re.search(r"Posting\s*Date\s*([\d]+\s+[A-Za-z]+\s+[\d]{4})", clean_text, re.IGNORECASE)
                            if alternative_match:
                                tender["Posting Date"] = self.format_date(alternative_match.group(1))

                        # 1. Capture the main summary paragraph shown in your image
                        paragraph_match = re.search(
                            r"([^.]*?has issued a Tender notice for the procurement of.*?Registering on the platform\.?)", 
                            clean_text, 
                            re.IGNORECASE
                        )
                        
                        description_block = ""
                        if paragraph_match:
                            description_block = paragraph_match.group(1).strip()
                        
                        # 2. Extract specific metadata from "Other Information" to guarantee nothing gets missed
                        extractions = {
                            "Notice Type": r"Notice\s*Type\s*:\s*(.*?)(?=\s*TOT\s*Ref\.No\.)",
                            "Document Ref. No.": r"Document\s*Ref\.?\s*No\.?\s*:\s*(.*?)(?=\s*Competition\s*:)",
                            "Competition": r"Competition\s*:\s*(.*?)(?=\s*Financier\s*:)",
                            "Financier": r"Financier\s*:\s*(.*?)(?=\s*Purchaser\s*Ownership\s*:)",
                            "Purchaser Ownership": r"Purchaser\s*Ownership\s*:\s*(.*?)(?=\s*Tender\s*Value\s*:)",
                            "Tender Value": r"Tender\s*Value\s*:\s*(.*?)(?=\s*Purchaser's\s*Detail|$)"
                        }
                        
                        meta_lines = []
                        for key, pattern in extractions.items():
                            m = re.search(pattern, clean_text, re.IGNORECASE)
                            if m:
                                meta_lines.append(f"{key}: {m.group(1).strip()}")

                        # 3. Combine paragraph text and specifications cleanly into the Description field
                        if meta_lines:
                            metadata_string = " | ".join(meta_lines)
                            if description_block:
                                tender["Description"] = f"{description_block} [{metadata_string}]"
                            else:
                                tender["Description"] = metadata_string
                        elif description_block:
                            tender["Description"] = description_block

                except Exception:
                    continue

            await browser.close()
            
            # --- ÉTAPE 3 : SAUVEGARDE EN JSON RAW ---
            print("\n\n4. Sauvegarde des données brutes...")
            if preliminary_tenders:
                saved_file = self.save_raw_json(preliminary_tenders)
                print(f"[Succès] Fichier JSON brut enregistré : {saved_file}")
            else:
                print("[!] Aucune donnée à sauvegarder.")

        return preliminary_tenders
