# cleaner.py
import pandas as pd
import json

# raw data লোড করা
with open('raw_data.json', 'r') as f:
    data = json.load(f)

df = pd.DataFrame(data)

# ক্লিনিং
# ১. প্রাইস থেকে অক্ষর সরিয়ে শুধু নাম্বার রাখা
df['price'] = df['price'].str.replace('Â£', '', regex=False).astype(float)

# ২. Availability টেক্সট ক্লিন করা
df['availability'] = df['availability'].str.replace('\n', ' ').str.strip()

# ক্লিন ডেটা সেভ করা (CSV এবং JSON)
df.to_csv('clean_data.csv', index=False)
df.to_json('clean_data.json', orient='records', indent=4)

print("Data Cleaned and Saved as CSV & JSON!")