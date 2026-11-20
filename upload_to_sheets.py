import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_data_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if not creds_json:
        logger.error("GCP_CREDENTIALS environment variable not found.")
        return

    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    SHEET_NAME = "Clin Data" 
    
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except Exception as e:
        logger.error(f"Could not open sheet: {e}")
        return
    
    try:
        df = pd.read_csv("clean_data.csv")
        logger.info(f"Loaded {len(df)} rows from clean_data.csv")
    except FileNotFoundError:
        logger.error("clean_data.csv not found.")
        return

    # Fetch existing data from the sheet
    existing_records = sheet.get_all_records()

    if not existing_records:
        # If sheet is empty, upload everything with headers
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)
        logger.info(f"Initial upload: Uploaded {len(df)} rows with headers.")
    else:
        # Extract existing titles to filter duplicates
        # Using 'title' as the unique identifier
        existing_titles = {str(row.get('title', '')).strip() for row in existing_records}
        
        # Filter the new dataframe: Keep rows where title is NOT in existing_titles
        # We also strip the titles in the new df to ensure matching works perfectly
        df['title'] = df['title'].astype(str).str.strip()
        new_unique_data = df[~df['title'].isin(existing_titles)]
        
        if new_unique_data.empty:
            logger.info("No new unique data found. All scraped items already exist in Google Sheets.")
        else:
            # Append only the new unique data
            data_to_append = new_unique_data.astype(str).values.tolist()
            sheet.append_rows(data_to_append)
            logger.info(f"Appended {len(data_to_append)} NEW rows to Google Sheets.")
            logger.info(f"Filtered out {len(df) - len(data_to_append)} duplicate rows.")

if __name__ == "__main__":
    upload_data_to_sheet()