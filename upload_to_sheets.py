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
    # Define the scope for Google Sheets and Drive APIs
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Try to get credentials from GitHub Actions Environment Variable
    creds_json = os.environ.get("GCP_CREDENTIALS")
    
    if creds_json:
        # Log that we are using the environment variable
        logging.info("Using GCP_CREDENTIALS from environment variable.")
        # Parse the JSON string into a dictionary
        creds_dict = json.loads(creds_json)
        # Create credentials object from dictionary
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Fallback for local testing using a local file
        logging.info("Environment variable not found. Looking for local 'gcp_credentials.json'.")
        local_creds_path = "gcp_credentials.json" 
        
        # Check if the local file exists
        if not os.path.exists(local_creds_path):
            logging.error("Local credentials file 'gcp_credentials.json' not found.")
            return None
            
        # Create credentials object from local file
        creds = ServiceAccountCredentials.from_json_keyfile_name(local_creds_path, scope)
        
    # Authorize and return the gspread client
    return gspread.authorize(creds)

def process_country_data(client, country_code, country_data):
    # Define the names of the tabs for the specific country
    current_tab_name = f"{country_code}_Current_Data"
    history_tab_name = f"{country_code}_Price_History"
    
    try:
        # Open the master Google Sheet
        sheet = client.open(SHEET_NAME)
        # Access the current data and history tabs
        current_ws = sheet.worksheet(current_tab_name)
        history_ws = sheet.worksheet(history_tab_name)
    except gspread.exceptions.WorksheetNotFound:
        # Log an error if the tabs do not exist
        logging.error(f"Tabs '{current_tab_name}' or '{history_tab_name}' not found in '{SHEET_NAME}'.")
        return

    # Fetch existing records from the current data tab to avoid duplicates
    existing_records = current_ws.get_all_records()
    
    # Map item_id to its row number and data for fast O(1) lookup
    # Row number is index + 2 because index starts at 0 and row 1 is the header
    existing_items = {
        str(row['item_id']): {'row_num': idx + 2, 'data': row} 
        for idx, row in enumerate(existing_records) if row.get('item_id')
    }
    
    # Lists to hold rows for bulk appending
    rows_to_append_current = []
    rows_to_append_history = []
    # List to hold cell updates for existing products
    batch_updates = []

    # Iterate through each item in the newly scraped data
    for item in country_data:
        # Safely get the item_id as a string
        item_id = str(item.get('item_id', ''))
        
        # Skip this item if there is no item_id
        if not item_id:
            continue 
            
        try:
            # Safely convert the new price to a float
            new_price = float(item.get('price', 0))
        except ValueError:
            # Default to 0.0 if the price is invalid
            new_price = 0.0

        # FIX: Clean the title to remove newlines that break Google Sheets rows
        raw_title = str(item.get('title', ''))
        # Replace newlines and carriage returns with spaces
        safe_title = raw_title.replace('\n', ' ').replace('\r', ' ').strip()

        # Define the row structure for Current Data
        current_row = [
            item.get('country_code', ''), 
            item.get('currency', ''), 
            item_id, 
            safe_title, 
            new_price, 
            item.get('location', ''), 
            item.get('seller_name', ''), 
            item.get('rating', ''), 
            item.get('reviews', ''), 
            item.get('scraped_at', '')
        ]
        
        # Define the row structure for Price History
        history_row = [
            item_id, 
            item.get('country_code', ''), 
            safe_title, 
            new_price, 
            item.get('currency', ''), 
            item.get('scraped_at', '')
        ]

        # Check if the product is completely new
        if item_id not in existing_items:
            # Log the new product
            logging.info(f"[{country_code}] New Product: {safe_title[:30]}...")
            # Add to the append lists
            rows_to_append_current.append(current_row)
            rows_to_append_history.append(history_row)
            
        else:
            # Product exists, so we check for updates
            old_record_info = existing_items[item_id]
            old_data = old_record_info['data']
            row_num = old_record_info['row_num']
            
            try:
                # Safely get the old price
                old_price = float(old_data.get('price', 0))
            except ValueError:
                old_price = 0.0
            
            # Check if the price has changed
            if new_price != old_price:
                # Log the price change
                logging.info(f"[{country_code}] Price Change: {safe_title[:30]} | {old_price} -> {new_price}")
                # Add to history log
                rows_to_append_history.append(history_row)
            
            # Queue updates for Current_Data (E=price, H=rating, I=reviews, J=scraped_at)
            batch_updates.append({"range": f"E{row_num}", "values": [[new_price]]})
            batch_updates.append({"range": f"H{row_num}", "values": [[item.get('rating', '')]]})
            batch_updates.append({"range": f"I{row_num}", "values": [[item.get('reviews', '')]]})
            batch_updates.append({"range": f"J{row_num}", "values": [[item.get('scraped_at', '')]]})

    # Bulk Append all completely new products to Current Data
    if rows_to_append_current:
        current_ws.append_rows(rows_to_append_current)
        logging.info(f"✅ [{country_code}] Added {len(rows_to_append_current)} new products to {current_tab_name}.")
        
    # Bulk Append all price changes and new products to Price History
    if rows_to_append_history:
        history_ws.append_rows(rows_to_append_history)
        logging.info(f"✅ [{country_code}] Logged {len(rows_to_append_history)} records to {history_tab_name}.")

    # Bulk Batch Update for existing products to avoid 429 Quota errors
    if batch_updates:
        # Define chunk size to avoid hitting API limits
        chunk_size = 100
        # Loop through the updates in chunks
        for i in range(0, len(batch_updates), chunk_size):
            chunk = batch_updates[i:i + chunk_size]
            # Execute the batch update
            current_ws.batch_update(chunk, value_input_option='USER_ENTERED')
            logging.info(f"🔄 [{country_code}] Batch updated {len(chunk)} cells in {current_tab_name}.")


def main():
    # Define the path to the scraped JSON data
    json_file_path = "data/raw/raw.json"
    
    # Check if the data file exists
    if not os.path.exists(json_file_path):
        logging.error(f"Data file not found: {json_file_path}")
        return

    # Open and read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
        
    # Exit if the JSON file is empty
    if not new_data:
        logging.info("No new data found in raw.json.")
        return

    # Authenticate with Google Sheets
    client = authenticate_gspread()
    if not client:
        return

    # Extract unique country codes from the data (e.g., 'BD', 'PK')
    country_codes = set(item.get('country_code') for item in new_data if item.get('country_code'))
    logging.info(f"Found data for countries: {list(country_codes)}")

    # Process data for each country separately
    for code in country_codes:
        # Filter the data for the current country
        country_data = [item for item in new_data if item.get('country_code') == code]
        logging.info(f"--- Processing {len(country_data)} items for {code} ---")
        # Call the processing function
        process_country_data(client, code, country_data)

    # Final success log
    logging.info("🎉 All data successfully synced to Google Sheets.")

if __name__ == "__main__":
    # Execute the main function
    main()