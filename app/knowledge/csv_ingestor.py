import requests
import pandas as pd
import hashlib

CSV_URL = "https://data.d4science.org/shub/..."

def download_csv():
    response = requests.get(CSV_URL)
    response.raise_for_status()
    return response.text

def compute_hash(content: str):
    return hashlib.md5(content.encode()).hexdigest()

def parse_csv(content: str):
    from io import StringIO
    df = pd.read_csv(StringIO(content))
    return df