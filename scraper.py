# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
import random

def scrape_books():
    url = "http://books.toscrape.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    books_data = []
    
    # ওয়েবসাইট থেকে ডেটা খোঁজা
    for book in soup.select('.product_pod'):
        title = book.select_one('h3 a')['title']
        price = book.select_one('.price_color').text
        availability = book.select_one('.instock.availability').text.strip()
        
        books_data.append({
            "title": title,
            "price": price,
            "availability": availability
        })
        
    return books_data

if __name__ == "__main__":
    print("Scraping started...")
    data = scrape_books()
    print(f"Collected {len(data)} items.")
    
    # raw data সেভ করা
    with open('raw_data.json', 'w') as f:
        json.dump(data, f, indent=4)
    print("Saved to raw_data.json")