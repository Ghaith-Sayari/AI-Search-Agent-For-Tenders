import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from scrapers.base import BaseScraper


class TendersOnTimeScraper(BaseScraper):
    source_name = "tendersontime"
    URL_CIBLE = "https://www.tendersontime.com/africa-tenders/"

    def __init__(self):
        self.debug_stats = {}
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    async def _is_cloudflare_challenge(self, page) -> bool:
        try:
            title = (await page.title() or "").lower()
            body_text = (await page.locator("body").inner_text() or "").lower()
        except Exception:
            return False
        sample = body_text[:4000]
        markers = [
            "just a moment",
            "verify you are human",
            "attention required",
            "cf-challenge",
            "cloudflare",
            "checking your browser",
        ]
        haystack = f"{title}\n{sample}"
        return any(m in haystack for m in markers)

    async def _manual_cloudflare_bootstrap(self, p):
        enabled = str(
            os.getenv("TENDERSONTIME_CF_BOOTSTRAP", "false")
        ).strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            return False, None, None, None, "cloudflare_bootstrap_disabled"

        wait_seconds = max(
            30,
            int(os.getenv("TENDERSONTIME_CF_BOOTSTRAP_WAIT_SECONDS", "120")),
        )
        sessions_dir = Path("data") / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        user_data_dir = sessions_dir / "tendersontime_user_data"
        storage_state_path = sessions_dir / "tendersontime_storage_state.json"

        persistent = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            user_agent=self._user_agent,
        )
        try:
            boot_page = persistent.pages[0] if persistent.pages else await persistent.new_page()
            await boot_page.goto(self.URL_CIBLE, wait_until="domcontentloaded", timeout=60000)
            deadline = time.monotonic() + wait_seconds
            solved = False
            while time.monotonic() < deadline:
                if not await self._is_cloudflare_challenge(boot_page):
                    solved = True
                    break
                await boot_page.wait_for_timeout(1000)

            if solved:
                await persistent.storage_state(path=str(storage_state_path))
            else:
                return False, None, None, None, "cloudflare_challenge_not_solved_within_timeout"
        finally:
            await persistent.close()

        # Reuse the same persistent profile in headless mode after manual solve.
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            user_agent=self._user_agent,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(self.URL_CIBLE, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(1500)
        if await self._is_cloudflare_challenge(page):
            await context.close()
            return False, None, None, None, "cloudflare_still_blocking_after_bootstrap"
        return True, None, context, page, "cloudflare_bootstrap_solved"

    def format_date(self, date_str):
        """Convertit '23 Jun 2026' en '23/6/2026'."""
        try:
            date_str = " ".join(date_str.split()).strip()
            dt = datetime.strptime(date_str, "%d %b %Y")
            return f"{dt.day}/{dt.month}/{dt.year}"
        except Exception:
            return date_str

    def fetch(self) -> list[dict]:
        """
        Main entry point called by the AI Search Agent.
        """
        return asyncio.run(self._scrape_tenders())

    async def diagnose_page(self):
        """
        Diagnostic uniquement.

        Cette méthode ne scrape pas les offres.
        Elle vérifie simplement ce que Playwright voit réellement
        sur la page TendersOnTime.
        """

        async with async_playwright() as p:

            print("1. Lancement du navigateur...")

            browser = await p.chromium.launch(
                headless=True
            )

            context_kwargs = {
                "user_agent": self._user_agent,
            }
            storage_state_path = Path("data") / "sessions" / "tendersontime_storage_state.json"
            if storage_state_path.exists():
                context_kwargs["storage_state"] = str(storage_state_path)
            context = await browser.new_context(**context_kwargs)

            page = await context.new_page()

            print(f"2. Ouverture de : {self.URL_CIBLE}")

            try:
                await page.goto(
                    self.URL_CIBLE,
                    wait_until="domcontentloaded",
                    timeout=45000,
                )

            except Exception as exc:
                print(
                    f"[WARN] domcontentloaded failed: "
                    f"{type(exc).__name__}: {exc}"
                )

                print("Tentative avec wait_until='load'...")

                await page.goto(
                    self.URL_CIBLE,
                    wait_until="load",
                    timeout=60000,
                )

            print("3. Attente du rendu de la page...")

            await page.wait_for_timeout(2000)

            # ============================================================
            # PAGE TEXT
            # ============================================================

            print("\n" + "=" * 70)
            print("DEBUG 1 : CONTENU DE LA PAGE")
            print("=" * 70)

            body_text = await page.locator("body").inner_text()

            print(
                "Body contains 'TOT Reference':",
                "TOT Reference" in body_text
            )

            print(
                "Body contains 'View Details':",
                "View Details" in body_text
            )

            print(
                "Body contains 'Deadline':",
                "Deadline" in body_text
            )

            print(
                "Body length:",
                len(body_text)
            )

            # ============================================================
            # BODY TEXT SAMPLE
            # ============================================================

            print("\n" + "=" * 70)
            print("DEBUG 2 : PREMIERS 5000 CARACTÈRES")
            print("=" * 70)

            print(body_text[:5000])

            # ============================================================
            # TEXT LOCATORS
            # ============================================================

            print("\n" + "=" * 70)
            print("DEBUG 3 : LOCATORS")
            print("=" * 70)

            tot_count = await page.get_by_text(
                "TOT Reference No.",
                exact=False
            ).count()

            view_count = await page.get_by_text(
                "View Details",
                exact=False
            ).count()

            deadline_count = await page.get_by_text(
                "Deadline:",
                exact=False
            ).count()

            print(
                "TOT Reference elements:",
                tot_count
            )

            print(
                "View Details elements:",
                view_count
            )

            print(
                "Deadline elements:",
                deadline_count
            )

            # ============================================================
            # LINK DIAGNOSTICS
            # ============================================================

            print("\n" + "=" * 70)
            print("DEBUG 4 : LIENS")
            print("=" * 70)

            detail_links = await page.locator(
                "a[href*='/tenders-details/']"
            ).count()

            print(
                "Links containing '/tenders-details/':",
                detail_links
            )

            # Print first few detail URLs
            if detail_links > 0:

                links = await page.locator(
                    "a[href*='/tenders-details/']"
                ).all()

                print("\nPremiers liens:")

                for index, link in enumerate(links[:10]):

                    href = await link.get_attribute("href")
                    text = (await link.inner_text()).strip()

                    print(
                        f"[{index + 1}] "
                        f"text={text!r} "
                        f"href={href!r}"
                    )

            # ============================================================
            # GENERIC SELECTORS
            # ============================================================

            print("\n" + "=" * 70)
            print("DEBUG 5 : SELECTEURS GENERIQUES")
            print("=" * 70)

            div_count = await page.locator("div").count()
            li_count = await page.locator("li").count()
            tr_count = await page.locator("tr").count()
            a_count = await page.locator("a").count()

            print("div:", div_count)
            print("li:", li_count)
            print("tr:", tr_count)
            print("a:", a_count)

            # ============================================================
            # ELEMENTS CONTENANT TOT REFERENCE
            # ============================================================

            print("\n" + "=" * 70)
            print("DEBUG 6 : ELEMENTS CONTENANT 'TOT Reference'")
            print("=" * 70)

            tot_elements = await page.locator(
                "text=TOT Reference"
            ).all()

            print(
                "Nombre d'éléments trouvés:",
                len(tot_elements)
            )

            for index, element in enumerate(tot_elements[:10]):

                try:
                    text = (await element.inner_text()).strip()

                    print(
                        f"\n[{index + 1}]"
                    )

                    print(
                        "Text:",
                        repr(text)
                    )

                    tag_name = await element.evaluate(
                        "(el) => el.tagName"
                    )

                    print(
                        "Tag:",
                        tag_name
                    )

                except Exception as exc:
                    print(
                        f"[WARN] Impossible de lire "
                        f"l'élément {index + 1}: {exc}"
                    )

            # ============================================================
            # SCREENSHOT
            # ============================================================

            screenshot_path = (
                "data/raw_scrapes/tendersontime_debug.png"
            )

            await page.screenshot(
                path=screenshot_path,
                full_page=True
            )

            print("\n" + "=" * 70)
            print("DEBUG 7 : SCREENSHOT")
            print("=" * 70)

            print(
                f"Screenshot sauvegardé : {screenshot_path}"
            )

            # ============================================================
            # HTML
            # ============================================================

            html_path = (
                "data/raw_scrapes/tendersontime_debug.html"
            )

            html = await page.content()

            with open(
                html_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(html)

            print(
                f"HTML sauvegardé : {html_path}"
            )

            # ============================================================
            # FINAL SUMMARY
            # ============================================================

            print("\n" + "=" * 70)
            print("DIAGNOSTIC FINAL")
            print("=" * 70)

            print(
                f"TOT Reference visible : "
                f"{'YES' if 'TOT Reference' in body_text else 'NO'}"
            )

            print(
                f"View Details visible : "
                f"{'YES' if 'View Details' in body_text else 'NO'}"
            )

            print(
                f"TOT Reference elements : "
                f"{tot_count}"
            )

            print(
                f"View Details elements : "
                f"{view_count}"
            )

            print(
                f"Detail links : "
                f"{detail_links}"
            )

            print(
                f"Body length : "
                f"{len(body_text)}"
            )

            print("=" * 70)

            await browser.close()

    async def _scrape_tenders(self) -> list[dict]:

        async with async_playwright() as p:

            print(
                "1. Lancement du navigateur en arrière-plan..."
            )

            use_persistent_session = str(
                os.getenv("TENDERSONTIME_USE_PERSISTENT_SESSION", "true")
            ).strip().lower() in {"1", "true", "yes", "on"}

            browser = None
            if use_persistent_session:
                sessions_dir = Path("data") / "sessions"
                sessions_dir.mkdir(parents=True, exist_ok=True)
                user_data_dir = sessions_dir / "tendersontime_user_data"
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    headless=True,
                    user_agent=self._user_agent,
                )
                page = context.pages[0] if context.pages else await context.new_page()
            else:
                browser = await p.chromium.launch(headless=True)
                context_kwargs = {"user_agent": self._user_agent}
                storage_state_path = Path("data") / "sessions" / "tendersontime_storage_state.json"
                if storage_state_path.exists():
                    context_kwargs["storage_state"] = str(storage_state_path)
                context = await browser.new_context(**context_kwargs)
                page = await context.new_page()

            print(
                f"2. Récupération des 50 derniers liens sur : "
                f"{self.URL_CIBLE}..."
            )

            try:
                await page.goto(
                    self.URL_CIBLE,
                    wait_until="domcontentloaded",
                    timeout=45000
                )

            except Exception:
                await page.goto(
                    self.URL_CIBLE,
                    wait_until="load",
                    timeout=60000
                )

            preliminary_tenders = []
            seen_references = set()

            page_num = 1
            limite_atteinte = False

            scan_stats = {
                "pages_scanned": 0,
                "cards_seen": 0,
                "cards_with_tot_ref_and_deadline": 0,
                "cards_with_tot_ref": 0,
                "missing_ref_pattern": 0,
                "duplicate_ref_skipped": 0,
                "fallback_anchor_candidates": 0,
                "cf_challenge_detected": False,
                "cf_bootstrap_attempted": False,
                "cf_bootstrap_solved": False,
                "cf_bootstrap_message": "",
            }

            await page.wait_for_timeout(1500)
            if await self._is_cloudflare_challenge(page):
                scan_stats["cf_challenge_detected"] = True
                scan_stats["cf_bootstrap_attempted"] = True
                if browser is not None:
                    await browser.close()
                else:
                    await context.close()
                solved, new_browser, new_context, new_page, cf_message = await self._manual_cloudflare_bootstrap(p)
                scan_stats["cf_bootstrap_solved"] = bool(solved)
                scan_stats["cf_bootstrap_message"] = cf_message
                if not solved:
                    self.debug_stats = {
                        **scan_stats,
                        "preliminary_tenders_count": 0,
                        "unique_references": 0,
                    }
                    print(f"[DEBUG tendersontime] {self.debug_stats}")
                    return []
                browser = new_browser
                context = new_context
                page = new_page

            while not limite_atteinte:

                print(
                    f"   -> Scan de la Page {page_num} "
                    f"(Trouvés : "
                    f"{len(preliminary_tenders)}/50)...",
                    end="\r"
                )

                await page.wait_for_timeout(1500)

                scan_stats["pages_scanned"] = page_num

                cards = await page.query_selector_all(
                    "div, li, tr"
                )

                for card in cards:

                    scan_stats["cards_seen"] += 1

                    if len(preliminary_tenders) >= 50:
                        limite_atteinte = True
                        break

                    text = await card.inner_text()

                    text_clean = " ".join(
                        text.split()
                    ).strip()

                    if "TOT Ref" in text_clean:

                        scan_stats[
                            "cards_with_tot_ref"
                        ] += 1

                        if "Deadline" in text_clean:
                            scan_stats[
                                "cards_with_tot_ref_and_deadline"
                            ] += 1

                        ref_match = re.search(
                            r"TOT Ref(?:erence)?"
                            r"(?:\s*No\.?)?"
                            r"\s*:?\s*(\d+)",
                            text_clean,
                            re.IGNORECASE
                        )

                        if not ref_match:

                            scan_stats[
                                "missing_ref_pattern"
                            ] += 1

                            continue

                        tot_ref = ref_match.group(1)

                        if tot_ref in seen_references:

                            scan_stats[
                                "duplicate_ref_skipped"
                            ] += 1

                            continue

                        seen_references.add(tot_ref)

                        link_elem = await card.query_selector(
                            "a:has-text('View Details')"
                        )

                        if not link_elem:

                            link_elem = await card.query_selector(
                                "a[href*='/tenders-details/']"
                            )

                        detail_url = None

                        if link_elem:

                            detail_url = await link_elem.get_attribute(
                                "href"
                            )

                            if (
                                detail_url
                                and detail_url.startswith("/")
                            ):
                                detail_url = (
                                    "https://www.tendersontime.com"
                                    + detail_url
                                )

                        deadline_match = re.search(
                            r"Deadline:\s*"
                            r"([\d]+\s+[A-Za-z]+\s+[\d]{4})",
                            text_clean
                        )

                        raw_deadline = (
                            deadline_match.group(1).strip()
                            if deadline_match
                            else ""
                        )

                        formatted_deadline = (
                            self.format_date(raw_deadline)
                            if raw_deadline
                            else "N/A"
                        )

                        title = (
                            text_clean.split(
                                "TOT Ref"
                            )[0].strip()
                            or text_clean.split(
                                "Deadline:"
                            )[0].strip()
                        )

                        country = "N/A"

                        if raw_deadline:

                            right_side = (
                                text_clean
                                .split(raw_deadline)[1]
                                .strip()
                            )

                            country_match = re.search(
                                r"^([A-Za-z\s\-\.]+?)"
                                r"(?=\s*TOT Ref|"
                                r"\s*View Details|$)",
                                right_side
                            )

                            if country_match:
                                country = (
                                    country_match
                                    .group(1)
                                    .strip()
                                )

                        preliminary_tenders.append(
                            {
                                "source": self.source_name,
                                "Titre": title,
                                "Pays": country,
                                "Posting Date": "N/A",
                                "Deadline": formatted_deadline,
                                "TOT Reference": tot_ref,
                                "Lien de l'offre": detail_url,
                                "Description": "N/A",
                            }
                        )

                if limite_atteinte:
                    break

                next_button = await page.query_selector(
                    "a:has-text('Next'):visible, "
                    "button:has-text('Next'):visible"
                )

                if next_button:

                    is_disabled = (
                        await next_button.get_attribute(
                            "disabled"
                        )
                        or await next_button.get_attribute(
                            "class"
                        )
                    )

                    if (
                        is_disabled
                        and (
                            "disabled"
                            in is_disabled.lower()
                            or "inactive"
                            in is_disabled.lower()
                        )
                    ):
                        break

                    try:

                        await next_button.click(
                            force=True,
                            timeout=5000
                        )

                        await page.wait_for_load_state(
                            "networkidle"
                        )

                        page_num += 1

                    except Exception:
                        break

                else:
                    break

            # ============================================================
            # FALLBACK
            # ============================================================

            if not preliminary_tenders:

                anchors = await page.query_selector_all(
                    "a[href*='/tenders-details/']"
                )

                scan_stats[
                    "fallback_anchor_candidates"
                ] = len(anchors)

                seen_urls = set()

                for a in anchors:

                    if len(preliminary_tenders) >= 50:
                        break

                    href = await a.get_attribute(
                        "href"
                    )

                    if not href:
                        continue

                    if href.startswith("/"):
                        href = (
                            "https://www.tendersontime.com"
                            + href
                        )

                    if "/tenders-details/" not in href:
                        continue

                    if href in seen_urls:
                        continue

                    seen_urls.add(href)

                    title = (
                        await a.inner_text()
                        or ""
                    ).strip()

                    if not title:
                        title = "Untitled tender"

                    preliminary_tenders.append(
                        {
                            "source": self.source_name,
                            "Titre": title,
                            "Pays": "N/A",
                            "Posting Date": "N/A",
                            "Deadline": "N/A",
                            "TOT Reference": "N/A",
                            "Lien de l'offre": href,
                            "Description": "N/A",
                        }
                    )

            # ============================================================
            # DETAIL PAGES
            # ============================================================

            print(
                f"\n\n3. Visite ciblée des "
                f"{len(preliminary_tenders)} pages de détails..."
            )

            detail_page = await context.new_page()

            for index, tender in enumerate(
                preliminary_tenders
            ):

                if not tender["Lien de l'offre"]:
                    continue

                print(
                    f"   -> [{index + 1}/"
                    f"{len(preliminary_tenders)}] "
                    f"Extraction Description Ref: "
                    f"{tender['TOT Reference']}...",
                    end="\r"
                )

                try:

                    await detail_page.goto(
                        tender["Lien de l'offre"],
                        wait_until="domcontentloaded",
                        timeout=10000
                    )

                    body_elem = await detail_page.query_selector(
                        "body"
                    )

                    if body_elem:

                        raw_text = await body_elem.inner_text()

                        clean_text = " ".join(
                            raw_text.split()
                        )

                        posting_match = re.search(
                            r"Posting\s*Date\s*:\s*"
                            r"([\d]+\s+[A-Za-z]+\s+[\d]{4})",
                            clean_text,
                            re.IGNORECASE
                        )

                        if posting_match:
                            tender["Posting Date"] = (
                                self.format_date(
                                    posting_match.group(1)
                                )
                            )
                        else:

                            alternative_match = re.search(
                                r"Posting\s*Date\s*"
                                r"([\d]+\s+[A-Za-z]+\s+[\d]{4})",
                                clean_text,
                                re.IGNORECASE
                            )

                            if alternative_match:
                                tender["Posting Date"] = (
                                    self.format_date(
                                        alternative_match.group(1)
                                    )
                                )

                        if tender.get(
                            "TOT Reference"
                        ) in ("N/A", "", None):

                            ref_match = re.search(
                                r"TOT\s*Ref(?:erence)?"
                                r"(?:\s*No\.?)?"
                                r"\s*:?\s*(\d+)",
                                clean_text,
                                re.IGNORECASE
                            )

                            if ref_match:
                                tender["TOT Reference"] = (
                                    ref_match.group(1).strip()
                                )

                        if tender.get(
                            "Deadline"
                        ) in ("N/A", "", None):

                            deadline_match = re.search(
                                r"Deadline\s*:\s*"
                                r"([\d]+\s+[A-Za-z]+\s+[\d]{4})",
                                clean_text,
                                re.IGNORECASE
                            )

                            if deadline_match:
                                tender["Deadline"] = (
                                    self.format_date(
                                        deadline_match.group(1)
                                    )
                                )

                        if tender.get(
                            "Pays"
                        ) in ("N/A", "", None):

                            country_match = re.search(
                                r"Country\s*:\s*"
                                r"([A-Za-z\-\s\.'()]+)",
                                clean_text,
                                re.IGNORECASE
                            )

                            if country_match:
                                tender["Pays"] = (
                                    country_match.group(1).strip()
                                )

                        paragraph_match = re.search(
                            r"([^.]*?has issued a Tender notice "
                            r"for the procurement of.*?"
                            r"Registering on the platform\.?)",
                            clean_text,
                            re.IGNORECASE
                        )

                        description_block = ""

                        if paragraph_match:
                            description_block = (
                                paragraph_match.group(1).strip()
                            )

                        extractions = {
                            "Notice Type": (
                                r"Notice\s*Type\s*:\s*(.*?)"
                                r"(?=\s*TOT\s*Ref\.No\.)"
                            ),
                            "Document Ref. No.": (
                                r"Document\s*Ref\.?\s*No\.?\s*:\s*(.*?)"
                                r"(?=\s*Competition\s*:)"
                            ),
                            "Competition": (
                                r"Competition\s*:\s*(.*?)"
                                r"(?=\s*Financier\s*:)"
                            ),
                            "Financier": (
                                r"Financier\s*:\s*(.*?)"
                                r"(?=\s*Purchaser\s*Ownership\s*:)"
                            ),
                            "Purchaser Ownership": (
                                r"Purchaser\s*Ownership\s*:\s*(.*?)"
                                r"(?=\s*Tender\s*Value\s*:)"
                            ),
                            "Tender Value": (
                                r"Tender\s*Value\s*:\s*(.*?)"
                                r"(?=\s*Purchaser's\s*Detail|$)"
                            ),
                        }

                        meta_lines = []

                        for key, pattern in extractions.items():

                            m = re.search(
                                pattern,
                                clean_text,
                                re.IGNORECASE
                            )

                            if m:
                                meta_lines.append(
                                    f"{key}: "
                                    f"{m.group(1).strip()}"
                                )

                        if meta_lines:

                            metadata_string = (
                                " | ".join(meta_lines)
                            )

                            if description_block:

                                tender["Description"] = (
                                    f"{description_block} "
                                    f"[{metadata_string}]"
                                )

                            else:

                                tender["Description"] = (
                                    metadata_string
                                )

                        elif description_block:

                            tender["Description"] = (
                                description_block
                            )

                except Exception:
                    continue

            if browser is not None:
                await browser.close()
            else:
                await context.close()

            # ============================================================
            # SAVE
            # ============================================================

            print(
                "\n\n4. Sauvegarde des données brutes..."
            )

            if preliminary_tenders:

                saved_file = self.save_raw_json(
                    preliminary_tenders
                )

                print(
                    f"[Succès] Fichier JSON brut enregistré : "
                    f"{saved_file}"
                )

            else:

                print(
                    "[!] Aucune donnée à sauvegarder."
                )

            self.debug_stats = {
                **scan_stats,
                "preliminary_tenders_count": len(
                    preliminary_tenders
                ),
                "unique_references": len(
                    seen_references
                ),
            }

            print(
                f"[DEBUG tendersontime] "
                f"{self.debug_stats}"
            )

        return preliminary_tenders
