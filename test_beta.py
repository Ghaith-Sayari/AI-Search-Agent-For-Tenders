import sys
import os

# Ensure the project root is in the python path to prevent import errors
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your updated scraper class
# Replace 'your_file_name' with the actual filename where your BetaMrScraper class lives
from scrapers.sources.beta_mr import BetaMrScraper 

def run_scraper_test():
    print("=" * 60)
    print("[!] STARTING SCRAPER VALIDATION RUN")
    print("=" * 60)
    
    try:
        # Initialize the scraper subclass
        scraper = BetaMrScraper()
        
        # Execute the synchronous fetch pipeline
        scraped_items = scraper.fetch()
        
        print("\n" + "=" * 60)
        print(f"[✓] TEST COMPLETED SUCCESSFULLY")
        print(f"[!] Total Items Extracted: {len(scraped_items)}")
        print("=" * 60)
        
        # Print a structured preview of the data fields
        if scraped_items:
            print("\n🔍 PREVIEWING FIRST CAPTURED RECORD:")
            sample = scraped_items[0]
            
            print(f" 🔹 Source:       {sample.get('source')}")
            print(f" 🔹 ID:           {sample.get('tender_id')}")
            print(f" 🔹 Title:        {sample.get('title')}")
            print(f" 🔹 Location:     {sample.get('location')}")
            print(f" 🔹 Deadline:     {sample.get('deadline')}")
            print(f" 🔹 Posting Date: {sample.get('posting_date')}  <-- [Verified Field]")
            print(f" 🔹 URL:          {sample.get('url_link')}")
            
            # Truncate description for output readability
            desc = sample.get('description', '')
            truncated_desc = desc[:120] + "..." if len(desc) > 120 else desc
            print(f" 🔹 Description Preview:\n    \"{truncated_desc}\"")
            
        else:
            print("\n[⚠️] Warning: Scraper ran but returned an empty dataset. Check source selectors.")
            
    except ModuleNotFoundError as e:
        print(f"\n[X] Import Error: {e}")
        print("[!] Make sure this script is placed where the 'scrapers' folder is accessible.")
    except Exception as e:
        print(f"\n[X] Test Runner Runtime Exception: {e}")

if __name__ == "__main__":
    run_scraper_test()