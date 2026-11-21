import requests
import json
import random
import time
import logging
import os

# Setup logging for production-ready output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of user agents to avoid getting blocked by anti-bot systems
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# Supported Daraz regional domains and their currencies
DARAZ_DOMAINS = {
    "bd": {"domain": "www.daraz.com.bd", "currency": "BDT"},
    "pk": {"domain": "www.daraz.pk", "currency": "PKR"},
    "lk": {"domain": "www.daraz.lk", "currency": "LKR"},
    "np": {"domain": "www.daraz.com.np", "currency": "NPR"},
    "mm": {"domain": "www.shop.com.mm", "currency": "MMK"}
}

# List of keywords to randomly select from
KEYWORDS = ["mobile", "laptop", "earbuds", "smartwatch", "power bank", "headphones", "gaming mouse"]

def get_random_headers():
    """Generate random headers to mimic a real browser and avoid IP bans."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Referer": "https://www.daraz.com.bd/"
    }

def scrape_daraz(countries=["bd", "pk"], keywords_per_country=2, pages_per_keyword=2):
    """
    Scrape product data from multiple Daraz regional domains.
    
    Args:
        countries (list): List of country codes to scrape (e.g., ["bd", "pk"]).
        keywords_per_country (int): Number of random keywords to scrape per country.
        pages_per_keyword (int): Number of pages to scrape per keyword.
    """
    all_scraped_data = []
    
    for country_code in countries:
        config = DARAZ_DOMAINS.get(country_code)
        if not config:
            logging.error(f"Unsupported country code: {country_code}. Skipping...")
            continue

        base_domain = config["domain"]
        currency = config["currency"]
        
        # Select random keywords for the specific country
        selected_keywords = random.sample(KEYWORDS, min(keywords_per_country, len(KEYWORDS)))
        
        logging.info(f"==== Starting scrape for {country_code.upper()} ({base_domain}) ====")
        
        for keyword in selected_keywords:
            for page in range(1, pages_per_keyword + 1):
                url = f"https://{base_domain}/catalog/?ajax=true&q={keyword}&page={page}"
                logging.info(f"Scraping {country_code.upper()} | Keyword: {keyword} | Page: {page}")
                
                try:
                    response = requests.get(url, headers=get_random_headers(), timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    
                    products = data.get('mods', {}).get('listItems', [])
                    
                    if not products:
                        logging.warning(f"No products found for '{keyword}' on page {page} in {country_code.upper()}.")
                        continue
                        
                    for item in products:
                        # Extract essential and enriched data safely
                        product_info = {
                            "country_code": country_code.upper(),
                            "currency": currency,
                            "item_id": item.get('itemId', ''),
                            "product_url": f"https:{item.get('productUrl', '')}" if item.get('productUrl') else '',
                            "title": item.get('name', ''),
                            "price": item.get('price', ''),
                            "original_price": item.get('originalPrice', ''),
                            "location": item.get('location', ''),
                            "seller_name": item.get('sellerName', ''),
                            "rating": item.get('ratingScore', '0'),
                            "reviews": item.get('review', '0'),
                            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        all_scraped_data.append(product_info)
                    
                    # Random delay to avoid rate limiting and getting blocked
                    time.sleep(random.uniform(2.5, 5.5))
                    
                except requests.exceptions.RequestException as e:
                    logging.error(f"Network error scraping {country_code.upper()} page {page}: {e}")
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON for {country_code.upper()} page {page}. Likely blocked by Daraz.")
                except Exception as e:
                    logging.error(f"Unexpected error for {country_code.upper()} page {page}: {e}")

    # Save all raw data to JSON
    if all_scraped_data:
        os.makedirs('data/raw', exist_ok=True)
        with open('data/raw/raw.json', 'w', encoding='utf-8') as f:
            json.dump(all_scraped_data, f, ensure_ascii=False, indent=4)
        logging.info(f"✅ Successfully scraped a total of {len(all_scraped_data)} products across all countries.")
    else:
        logging.warning("⚠️ No data was scraped in this run.")

if __name__ == "__main__":
    # You can configure which countries to scrape here.
    # By default, it will scrape Bangladesh (bd) and Pakistan (pk).
    # To add more, simply add their country codes (e.g., ["bd", "pk", "lk", "np"]).
    target_countries = ["bd", "pk"] 
    
    scrape_daraz(countries=target_countries, keywords_per_country=2, pages_per_keyword=2)