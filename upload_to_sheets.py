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

    # IMPORTANT: Sheet name must match exactly
    SHEET_NAME = "Clin Data" 
    sheet = client.open(SHEET_NAME).sheet1
    
    try:
        df = pd.read_csv("clean_data.csv")
        logger.info(f"Loaded {len(df)} rows from clean_data.csv")
    except FileNotFoundError:
        logger.error("clean_data.csv not found.")
        return

    # Check if the sheet is completely empty (needs headers)
    if not sheet.get_all_values():
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        sheet.update(data_to_upload)
        logger.info("Uploaded initial data with headers.")
    else:
        data_to_append = df.astype(str).values.tolist()
        sheet.append_rows(data_to_append)
        logger.info(f"Appended {len(data_to_append)} new rows to Google Sheets!")

if __name__ == "__main__":
    upload_data_to_sheet()