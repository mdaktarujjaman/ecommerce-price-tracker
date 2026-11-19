import pandas as pd
import json
import logging
import re
from pathlib import Path
from typing import Optional

# ==========================================
# Configuration & Logging Setup
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Input path from scraper.py
RAW_DATA_PATH = Path("data/raw/raw.json")

# Output paths
CSV_OUTPUT_PATH = Path("clean_data.csv")  # Root level for GitHub Actions artifact
JSON_OUTPUT_PATH = Path("data/clean/clean_data.json")

def load_raw_data(filepath: Path) -> pd.DataFrame:
    """
    Loads raw JSON data into a pandas DataFrame.
    """
    if not filepath.exists():
        logger.error(f"Raw data file not found at {filepath}")
        return pd.DataFrame()
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {len(data)} raw records.")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return pd.DataFrame()

def clean_price(price_str: str) -> Optional[float]:
    """
    Extracts numeric value from Daraz price strings (e.g., 'Tk. 25,000' -> 25000.0).
    """
    if not isinstance(price_str, str) or not price_str:
        return None
    
    try:
        # Remove all non-numeric characters except for decimals (removes Tk, commas, spaces)
        cleaned_str = re.sub(r'[^\d.]', '', price_str)
        if not cleaned_str:
            return None
        return float(cleaned_str)
    except ValueError:
        return None

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and transforms the raw DataFrame into a sale-ready format.
    """
    if df.empty:
        logger.warning("DataFrame is empty. Skipping processing.")
        return df

    logger.info("Starting data cleaning process...")

    # 1. Drop rows where essential fields are missing
    df = df.dropna(subset=["title", "price"])
    
    # 2. Remove duplicate records based on title
    df = df.drop_duplicates(subset=["title"])

    # 3. Clean title column
    df["title"] = df["title"].astype(str).str.strip()

    # 4. Clean and convert price to numeric
    df["price"] = df["price"].apply(clean_price)
    
    # 5. Drop rows where price couldn't be parsed
    df = df[df["price"].notna() & (df["price"] > 0)]

    # 6. Clean rating column (ensure it's numeric)
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

    # 7. Add metadata columns
    df["currency"] = "BDT"
    
    # Sort by price descending
    df = df.sort_values(by="price", ascending=False)

    logger.info(f"Data cleaning completed. {len(df)} valid records remaining.")
    return df

def save_clean_data(df: pd.DataFrame) -> None:
    """
    Saves the cleaned DataFrame to CSV and JSON formats.
    """
    if df.empty:
        logger.warning("No clean data to save.")
        return

    try:
        # Ensure directory exists for JSON
        JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV (Root level)
        df.to_csv(CSV_OUTPUT_PATH, index=False, encoding="utf-8")
        logger.info(f"Saved clean data to {CSV_OUTPUT_PATH}")
        
        # Save to JSON
        df.to_json(JSON_OUTPUT_PATH, orient="records", indent=4, force_ascii=False)
        logger.info(f"Saved clean data to {JSON_OUTPUT_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to save clean data: {e}")

if __name__ == "__main__":
    logger.info("Starting data cleaner pipeline...")
    
    # Execute pipeline
    raw_df = load_raw_data(RAW_DATA_PATH)
    clean_df = process_data(raw_df)
    save_clean_data(clean_df)
    
    logger.info("Data cleaner job completed successfully.")