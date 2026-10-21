# -*- coding: utf-8 -*-

import requests
import pandas as pd
from io import BytesIO


CSV_URL = (
    "https://data.d4science.org/shub/"
    "E_Q005UkRYM3Z5ckRUM0hRRkpidTJBQWxXSTZTVDBRVzV5aDQxV21Sc1RpeEh1"
    "RG9Ja05sQXZFa21KaEgxRG82aQ=="
)


def load_live_data():
    """
    Download the live environmental indicators and return
    the first data row as a pandas Series.
    """

    response = requests.get(CSV_URL)
    response.raise_for_status()

    # utf-8-sig removes a UTF-8 BOM when present.
    df = pd.read_csv(
        BytesIO(response.content),
        encoding="utf-8-sig"
    )

    # Normalize column names without changing their meaning.
    df.columns = [
        str(column).strip().lstrip("\ufeff").lower()
        for column in df.columns
    ]

    if df.empty:
        raise ValueError("Live data empty")

    return df.iloc[0]


def safe_get(row, key_fragment):
    """
    Return the first field whose normalized name contains
    the requested fragment.
    """

    for col in row.index:
        if key_fragment.lower() in str(col).lower():
            return row[col]

    return "N/A"


def build_live_summary(row):
    """
    Build the existing compact live-data summary.
    """

    try:
        return f"""
Year: {safe_get(row, "reference year")}
Temperature change: {safe_get(row, "temperature change")} °C
Precipitation change: {safe_get(row, "water from rain")} %
Evaporation change: {safe_get(row, "evaporation change")} %
Species richness: {safe_get(row, "species richness")}
"""
    except Exception as exc:
        print("⚠️ Live summary error:", exc)
        return ""