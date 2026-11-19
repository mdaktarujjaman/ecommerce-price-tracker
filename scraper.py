import requests
import json
import time
import random
import logging
from pathlib import Path
from typing import List, Dict, Any

# ==========================================
# Configuration & Logging Setup
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Daraz Search API Endpoint
BASE_URL = "https://www.daraz.com.bd/catalog/"

# Required headers to bypass basic bot protection and mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.daraz.com.bd/",
    "X-Requested-With": "XMLHttpRequest"
}

# File paths
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "raw.json"


def fetch_page_data(keyword: str, page: int, session: requests.Session) -> List[Dict[str, Any]]:
    """
    Fetches product data for a specific keyword and page number from Daraz API.
    """
    params = {
        "ajax": "true",
        "isFirstRequest": "true" if page == 1 else "false",
        "page": page,
        "q": keyword
    }

    try:
        logger.info(f"Fetching data for keyword: '{keyword}' | Page: {page}")
        response = session.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        items = data.get("mods", {}).get("listItems", [])
        return items

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error on page {page}: {e}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON on page {page}. Daraz might be blocking the request.")
        return []


def scrape_daraz_products(keyword: str, max_pages: int = 3) -> List[Dict[str, Any]]:
    """
    Orchestrates the scraping process across multiple pages.
    """
    all_products = []
    # Reusing session for connection pooling (improves performance)
    session = requests.Session() 

    for page in range(1, max_pages + 1):
        items = fetch_page_data(keyword, page, session)
        
        if not items:
            logger.warning(f"No items found on page {page}. Stopping pagination.")
            break

        for item in items:
            # Extract relevant fields and handle missing keys gracefully
            product = {
                "title": item.get("name", "").strip(),
                "price": item.get("price", "").strip(),
                "location": item.get("location", ""),
                "rating": item.get("ratings", "0"),
                "seller": item.get("sellerName", ""),
                "source": "Daraz BD"
            }
            all_products.append(product)

        logger.info(f"Successfully extracted {len(items)} items from page {page}.")
        
        # Polite delay to avoid rate-limiting (IP ban)
        delay = random.uniform(2.0, 5.0)
        logger.info(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

    return all_products


def save_to_json(data: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Saves the scraped data to a JSON file, creating directories if necessary.
    """
    if not data:
        logger.warning("No data to save.")
        return

    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Successfully saved {len(data)} records to {filepath}")
    except IOError as e:
        logger.error(f"Failed to save data to {filepath}: {e}")


if __name__ == "__main__":
    # Change the keyword to whatever you want to mine (e.g., "mobile", "laptop", "shoes")
    TARGET_KEYWORD = "mobile"
    MAX_PAGES_TO_SCRAPE = 3

    logger.info("Starting Daraz scraping pipeline...")
    
    # Execute scraping pipeline
    scraped_data = scrape_daraz_products(keyword=TARGET_KEYWORD, max_pages=MAX_PAGES_TO_SCRAPE)
    
    if scraped_data:
        save_to_json(scraped_data, OUTPUT_FILE)
        logger.info("Scraping job completed successfully.")
    else:
        logger.error("Scraping job finished with 0 results.")