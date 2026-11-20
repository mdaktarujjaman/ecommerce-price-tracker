# 🛒 E-commerce Price Tracker & Data Mining Pipeline

An automated, production-ready data mining pipeline that extracts real-time product data from **Daraz Bangladesh**, cleans the data, and automatically syncs it to **Google Sheets**. Built with Python and automated using **GitHub Actions**.

## 🚀 The Problem It Solves
E-commerce prices fluctuate rapidly. Manually tracking competitor prices, seller ratings, and product availability is impossible at scale. This system runs autonomously in the cloud, rotating through different product categories and pages to bypass basic anti-bot protections, and delivers clean, structured, sale-ready datasets every 6 hours.

## ✨ Key Features
- **Automated Scraping:** Uses Daraz's internal JSON API instead of HTML parsing for faster, cleaner, and more reliable data extraction.
- **Smart Rotation (Anti-Ban):** Randomly selects product categories (e.g., mobile, laptop, gaming) and starting pages to avoid scraping the same top 120 items and to prevent IP blocking.
- **Data Cleaning & Formatting:** Automatically strips currency symbols (e.g., `Tk.`), handles duplicates, and converts prices to numeric values using `pandas`.
- **Time-Series Data:** Instead of overwriting, the pipeline appends new data to Google Sheets along with a `scraped_at` timestamp, creating a valuable historical price dataset.
- **Cloud Automation:** Runs entirely on GitHub Actions on a `cron` schedule (every 6 hours). No local server or computer needs to be turned on.
- **Artifact Generation:** Automatically generates a `clean_data.csv` artifact for direct download and offline use.

## 🏗️ Architecture & Workflow

```text
[ GitHub Actions (Cron: Every 6 hours) ]
               │
               ▼
   1. `scraper.py`  ──> Extracts data via Daraz API (Random Keyword & Page)
               │         Saves to: `data/raw/raw.json`
               ▼
   2. `cleaner.py`  ──> Cleans prices, removes duplicates, adds timestamps
               │         Saves to: `clean_data.csv` & `data/clean/clean_data.json`
               ▼
   3. `upload_to_sheets.py` ──> Authenticates via Google Cloud Service Account
               │                 Appends data to Google Sheets
               ▼
   [ Google Sheets (Live Dashboard) ] & [ GitHub Artifacts (CSV) ]

🛠️ Tech Stack
Language: Python 3.10+

Data Processing: pandas, json, re (Regular Expressions)

HTTP Client: requests

Cloud Automation: GitHub Actions (YAML)

Google Integration: gspread, oauth2client (Google Sheets API & Drive API)

Logging: Built-in Python logging module for production-grade monitoring.

📂 Project Structure

ecommerce-price-tracker/
│
├── .github/workflows/
│   └── automate.yml         # GitHub Actions CI/CD pipeline
├── src/ (Optional for future scaling)
├── scraper.py               # Main scraping script using Daraz API
├── cleaner.py               # Data transformation and cleaning script
├── upload_to_sheets.py      # Google Sheets API integration script
├── requirements.txt         # Python dependencies
├── .gitignore               # Ignores venv, raw data, and secrets
└── README.md

⚙️ How to Setup Locally

Clone the repository:
git clone https://github.com/mdaktarujjaman/ecommerce-price-tracker.git
cd ecommerce-price-tracker

Create a virtual environment & install dependencies:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Run the pipeline manually:
python scraper.py   # Fetches raw data
python cleaner.py   # Cleans and formats data

🔐 Google Sheets Integration Setup
To enable the automated data upload, you must configure a Google Cloud Service Account:

Go to Google Cloud Console -> Create a new project.

Enable Google Sheets API and Google Drive API.

Create a Service Account and generate a JSON Key.

Share your target Google Sheet with the client_email found in the JSON file (give it Editor access).

Add the entire JSON text as a GitHub Repository Secret named GCP_CREDENTIALS.

⚠️ Disclaimer & Ethics
This project is for educational and market research purposes only. Scraping should be done responsibly. The pipeline includes polite delays (time.sleep) to avoid overloading the target server. Always check the target website's robots.txt and Terms of Service before scaling.

If you find this project useful for your data mining needs, feel free to star ⭐ the repository!

