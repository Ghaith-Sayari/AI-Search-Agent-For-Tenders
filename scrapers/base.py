from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os
import json

class BaseScraper(ABC):
    """
    Abstract base class that all website scrapers must inherit from.
    This enforces a standard structure so the main AI Agent can run them,
    while allowing complete flexibility in the raw data they collect.
    """
    
    # Every scraper must define its source name (e.g., "tendersontime", "ungm")
    source_name: str

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        The main entry point called by the registry/agent.
        Must return a list of raw dictionaries containing the scraped data.
        """
        pass

    def save_raw_json(self, data: List[Dict[str, Any]]) -> str:
        """
        A built-in helper method available to all your scrapers.
        Call this at the end of your fetch() method to instantly save 
        the raw data to a standardized JSON file.
        """
        folder_path = "data/raw_scrapes"
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, f"{self.source_name}_raw.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return file_path