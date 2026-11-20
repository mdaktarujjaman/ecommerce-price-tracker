<div align="center">

# 🛒 E-commerce Price Tracker & Data Mining Pipeline

**Automated, cloud-native price intelligence for Daraz Bangladesh, scraped, cleaned, and synced to Google Sheets every 6 hours.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Cleaning-150458?style=for-the-badge&logo=pandas&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Live%20Dashboard-34A853?style=for-the-badge&logo=googlesheets&logoColor=white)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Google Sheets Integration](#-google-sheets-integration)
- [Automation](#-automation)
- [Responsible Scraping](#-responsible-scraping)
- [Author](#-author)

---

## 🎯 Overview

E-commerce prices change constantly. Tracking competitor prices, seller ratings, and stock availability by hand does not scale.

This pipeline runs fully in the cloud with no server and no local machine required. It rotates through product categories and result pages, collects fresh data from **Daraz Bangladesh**, cleans it, and appends it to Google Sheets with a timestamp. The result is a growing, structured, sale-ready price history dataset, delivered every **6 hours**.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| ⚡ **Internal JSON API** | Pulls data from Daraz's internal JSON API instead of parsing HTML, which is faster, cleaner, and more reliable. |
| 🔄 **Smart Rotation** | Randomly picks categories (mobile, laptop, gaming, etc.) and starting pages, so it never hits the same top 120 items and lowers the risk of IP blocks. |
| 🧹 **Data Cleaning** | Strips currency symbols (`Tk.`), removes duplicates, and converts prices to numeric values with `pandas`. |
| 📈 **Time-Series Dataset** | Appends instead of overwriting. Every row carries a `scraped_at` timestamp, building a valuable historical price record. |
| ☁️ **Zero-Infrastructure Automation** | Runs on GitHub Actions with a `cron` schedule (every 6 hours). |
| 📦 **Downloadable Artifact** | Generates a `clean_data.csv` artifact for direct download and offline analysis. |
| 📝 **Production Logging** | Uses Python's built-in `logging` module for monitoring and debugging. |

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────┐
│   GitHub Actions  (cron: every 6 hours)      │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 1. scraper.py                                │
│    Fetch data via Daraz API                  │
│    (random keyword + random page)            │
│    → data/raw/raw.json                       │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 2. cleaner.py                                │
│    Clean prices, drop duplicates,            │
│    add timestamps                            │
│    → clean_data.csv                          │
│    → data/clean/clean_data.json              │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 3. upload_to_sheets.py                       │
│    Authenticate via Google Service Account   │
│    Append rows to Google Sheets              │
└──────────────────────┬───────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
 ┌─────────────────┐     ┌────────────────────┐
 │  Google Sheets  │     │  GitHub Artifacts  │
 │ (Live Dashboard)│     │   (clean_data.csv) │
 └─────────────────┘     └────────────────────┘
```

---

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| **Language** | Python 3.10+ |
| **Data Processing** | `pandas`, `json`, `re` |
| **HTTP Client** | `requests` |
| **Automation / CI** | GitHub Actions (YAML) |
| **Google Integration** | `gspread`, `oauth2client` (Sheets API + Drive API) |
| **Monitoring** | Python `logging` |

---

## 📂 Project Structure

```text
ecommerce-price-tracker/
│
├── .github/
│   └── workflows/
│       └── automate.yml        # GitHub Actions pipeline
│
├── scraper.py                  # Daraz API scraper
├── cleaner.py                  # Data cleaning & transformation
├── upload_to_sheets.py         # Google Sheets sync
├── requirements.txt            # Python dependencies
├── .gitignore                  # Ignores venv, raw data, secrets
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

```bash
git clone https://github.com/mdaktarujjaman/ecommerce-price-tracker.git
cd ecommerce-price-tracker
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Run the Pipeline Manually

```bash
python scraper.py    # Step 1: fetch raw data
python cleaner.py    # Step 2: clean and format data
```

---

## 🔐 Google Sheets Integration

To enable automated uploads, configure a Google Cloud Service Account:

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and **create a new project**.
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account** and generate a **JSON key**.
4. Share your target Google Sheet with the `client_email` from the JSON file, with **Editor** access.
5. Add the **entire JSON content** as a GitHub repository secret named `GCP_CREDENTIALS`.

> **Path:** Repository → Settings → Secrets and variables → Actions → New repository secret

---

## ⏱️ Automation

The pipeline is scheduled in `.github/workflows/automate.yml` and runs every 6 hours on GitHub Actions. Each run:

1. Scrapes a random category and page
2. Cleans and deduplicates the data
3. Appends the results to Google Sheets
4. Publishes `clean_data.csv` as a downloadable workflow artifact

You can also trigger a run manually from the **Actions** tab.

---

## ⚠️ Responsible Scraping

This project is intended for **educational and market research purposes only**.

- Polite delays (`time.sleep`) are built in to avoid overloading the target server.
- Always review the target site's `robots.txt` and Terms of Service before scaling.
- Use the data responsibly and in compliance with applicable laws.

---

## 👨‍💻 Author

**Md Aktarujjaman**
Backend-focused Full-Stack Developer · Django Specialist · Founder of **ITzone360**

[![Website](https://img.shields.io/badge/Website-itzone360.net-0A66C2?style=flat-square&logo=googlechrome&logoColor=white)](https://itzone360.net)
[![GitHub](https://img.shields.io/badge/GitHub-mdaktarujjaman-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/mdaktarujjaman)

Need a custom scraper, data pipeline, or automation built for your business? Get in touch through the website above.

---

<div align="center">

If this project helps you, please consider giving it a ⭐

</div>