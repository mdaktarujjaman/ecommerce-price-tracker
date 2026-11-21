import pandas as pd
import gspread
import logging
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

# Setup logging for production-ready tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Google Sheet Name
SHEET_NAME = "Clin Data"

def authenticate_gspread():
    """Authenticate with Google Sheets API using env var or local file."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Try to get credentials from GitHub Actions Environment Variable
    creds_json = os.environ.get("GCP_CREDENTIALS")
    
    if creds_json:
        logging.info("Using GCP_CREDENTIALS from environment variable.")
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # 2. Fallback for Local Testing
        logging.info("Environment variable not found. Looking for local 'gcp_credentials.json'.")
        local_creds_path = "gcp_credentials.json" 
        if not os.path.exists(local_creds_path):
            logging.error("Local credentials file 'gcp_credentials.json' not found.")
            return None
        creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scope)
        
    return gspread.authorize(creds)

def process_country_data(client, country_code, country_data):
    """Process and upload data for a specific country using batch updates to avoid Quota limits."""
    current_tab_name = f"{country_code}_Current_Data"
    history_tab_name = f"{country_code}_Price_History"
    
    try:
        sheet = client.open(SHEET_NAME)
        current_ws = sheet.worksheet(current_tab_name)
        history_ws = sheet.worksheet(history_tab_name)
    except gspread.exceptions.WorksheetNotFound:
        logging.error(f"Tabs '{current_tab_name}' or '{history_tab_name}' not found in '{SHEET_NAME}'.")
        return

    # 1. Fetch existing records to avoid duplicates
    existing_records = current_ws.get_all_records()
    
    # Map item_id to its row number AND its data for fast O(1) lookup
    # (Row number is index + 2 because index starts at 0 and row 1 is the header)
    existing_items = {
        str(row['item_id']): {'row_num': idx + 2, 'data': row} 
        for idx, row in enumerate(existing_records) if row.get('item_id')
    }
    
    rows_to_append_current = []
    rows_to_append_history = []
    batch_updates = [] # Store all cell updates here

    # 2. Iterate through new scraped data
    for item in country_data:
        item_id = str(item.get('item_id', ''))
        if not item_id:
            continue 
            
        try:
            new_price = float(item.get('price', 0))
        except ValueError:
            new_price = 0.0

        # Define row structures based on Google Sheet headers
        current_row = [
            item.get('country_code', ''), item.get('currency', ''), item_id, 
            item.get('title', ''), new_price, item.get('location', ''), 
            item.get('seller_name', ''), item.get('rating', ''), 
            item.get('reviews', ''), item.get('scraped_at', '')
        ]
        
        history_row = [
            item_id, item.get('country_code', ''), item.get('title', ''), 
            new_price, item.get('currency', ''), item.get('scraped_at', '')
        ]

        if item_id not in existing_items:
            # CASE A: Completely New Product
            logging.info(f"[{country_code}] New Product: {item['title'][:30]}...")
            rows_to_append_current.append(current_row)
            rows_to_append_history.append(history_row)
            
        else:
            # CASE B: Existing Product
            old_record_info = existing_items[item_id]
            old_data = old_record_info['data']
            row_num = old_record_info['row_num']
            
            try:
                old_price = float(old_data.get('price', 0))
            except ValueError:
                old_price = 0.0
            
            # If price changed, log it to Price_History
            if new_price != old_price:
                logging.info(f"[{country_code}] Price Drop/Increase: {item['title'][:30]} | {old_price} -> {new_price}")
                rows_to_append_history.append(history_row)
            
            # Queue updates for Current_Data instead of updating immediately
            # Columns: E=price, H=rating, I=reviews, J=scraped_at
            batch_updates.append({"range": f"E{row_num}", "values": [[new_price]]})
            batch_updates.append({"range": f"H{row_num}", "values": [[item.get('rating', '')]]})
            batch_updates.append({"range": f"I{row_num}", "values": [[item.get('reviews', '')]]})
            batch_updates.append({"range": f"J{row_num}", "values": [[item.get('scraped_at', '')]]})

    # 3. Bulk Append (For New Products)
    if rows_to_append_current:
        current_ws.append_rows(rows_to_append_current)
        logging.info(f"✅ [{country_code}] Added {len(rows_to_append_current)} new products to {current_tab_name}.")
        
    if rows_to_append_history:
        history_ws.append_rows(rows_to_append_history)
        logging.info(f"✅ [{country_code}] Logged {len(rows_to_append_history)} price changes to {history_tab_name}.")

    # 4. Bulk Batch Update (For Existing Products - Solves 429 Error)
    if batch_updates:
        # Chunk the updates if they exceed 100 at a time to stay safe
        chunk_size = 100
        for i in range(0, len(batch_updates), chunk_size):
            chunk = batch_updates[i:i + chunk_size]
            current_ws.batch_update(chunk, value_input_option='USER_ENTERED')
            logging.info(f"🔄 [{country_code}] Batch updated {len(chunk)} cells in {current_tab_name}.")


def main():
    json_file_path = "data/raw/raw.json"
    
    if not os.path.exists(json_file_path):
        logging.error(f"Data file not found: {json_file_path}")
        return

    with open(json_file_path, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
        
    if not new_data:
        logging.info("No new data found in raw.json.")
        return

    client = authenticate_gspread()
    if not client:
        return

    # Group data by country_code dynamically
    country_codes = set(item.get('country_code') for item in new_data if item.get('country_code'))
    logging.info(f"Found data for countries: {list(country_codes)}")

    # Process data for each country
    for code in country_codes:
        country_data = [item for item in new_data if item.get('country_code') == code]
        logging.info(f"--- Processing {len(country_data)} items for {code} ---")
        process_country_data(client, code, country_data)

    logging.info("🎉 All data successfully synced to Google Sheets.")

if __name__ == "__main__":
    main()