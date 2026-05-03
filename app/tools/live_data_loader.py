"""
Massaciuccoli Digital Twin
Live Data Loader — FINAL FIXED (COLUMN SAFE)
"""

import requests
import pandas as pd
from io import StringIO

CSV_URL = "https://data.d4science.org/shub/E_Q005UkRYM3Z5ckRUM0hRRkpidTJBQWxXSTZTVDBRVzV5aDQxV21Sc1RpeEh1RG9Ja05sQXZFa21KaEgxRG82aQ=="


# ======================================================
# LOAD CSV (ROBUST)
# ======================================================

def load_live_data():

    response = requests.get(CSV_URL)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))

    # 🔥 NORMALIZZA NOMI COLONNE
    df.columns = [c.strip().lower() for c in df.columns]

    if df.empty:
        raise ValueError("Live data empty")

    return df.iloc[0]


# ======================================================
# HELPER (SAFE GET)
# ======================================================

def safe_get(row, key_fragment):

    for col in row.index:
        if key_fragment in col:
            return row[col]

    return "N/A"


# ======================================================
# SUMMARY (ROBUST)
# ======================================================

def build_live_summary(row):

    try:
        return f"""
Year: {safe_get(row, "reference year")}

Temperature change: {safe_get(row, "temperature change")} °C
Precipitation change: {safe_get(row, "water from rain")} %
Evaporation change: {safe_get(row, "evaporation change")} %

Species richness: {safe_get(row, "species richness")}
"""
    except Exception as e:
        print("⚠️ Live summary error:", e)
        return ""