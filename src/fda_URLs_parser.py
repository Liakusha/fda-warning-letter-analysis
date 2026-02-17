import pandas as pd
import requests
from pathlib import Path
import re
from ddgs import DDGS
import time

DATA_PATH = Path.cwd()
df = pd.read_excel(DATA_PATH / "warning_letters_cder_base_v1.xls")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_marcs(url):
    m = re.search(r'-(\d{5,7})-\d{8}$', url)
    return m.group(1) if m else None

def url_is_valid(url):
    r = requests.get(url, headers=HEADERS, timeout=10)
    return r.status_code == 200


with DDGS() as ddgs:
    for i, row in df.iloc[len(df)].iterrows():
        company = row["company_name"]
        query = f'site:fda.gov "{company}" "Warning Letter"'

        try:
            results = list(ddgs.text(query, max_results=3))
        except RuntimeError:
            time.sleep(5)
            continue

        if not results:
            continue

        for r in results:
            url = r.get("href")
            marcs = extract_marcs(url)

            if marcs and url_is_valid(url):
                df.at[i, "letter_url"] = url
                df.at[i, "marcs_cms"] = marcs
                break

        time.sleep(3)  # rate limit


df_URLs=df.copy()
df_URLs.to_csv("Warning_letters_URLs.csv", index=False)