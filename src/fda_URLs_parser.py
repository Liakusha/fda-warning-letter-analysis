import pandas as pd
import requests
from pathlib import Path
import re
from ddgs import DDGS
import time
import argparse

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def extract_marcs(url: str | None):
    if not url:
        return None
    m = re.search(r'-(\d{5,7})-\d{8}$', url)
    return m.group(1) if m else None


def url_is_valid(url: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.status_code == 200
    except requests.RequestException:
        return False


def parse_urls(input_file: Path, output_file: Path):
    df = pd.read_excel(input_file)

    with DDGS() as ddgs:
        for i, row in df.iterrows():

            company = str(row.get("company_name", "")).strip()
            if not company:
                continue

            query = f'site:fda.gov "{company}" "Warning Letter"'
            print(f"[{i}] Searching: {company}")

            try:
                results = list(ddgs.text(query, max_results=3))
            except RuntimeError:
                print("DDGS rate limited — sleeping 10s")
                time.sleep(10)
                continue

            for r in results:
                url = r.get("href")
                marcs = extract_marcs(url)

                if marcs and url_is_valid(url):
                    df.at[i, "letter_url"] = url
                    df.at[i, "marcs_cms"] = marcs
                    break

            time.sleep(3)

    df.to_csv(output_file, index=False)
    print("Saved:", output_file)


def main():
    parser = argparse.ArgumentParser(description="FDA Warning Letter URL parser")

    parser.add_argument("input", type=Path, help="Input Excel file")
    parser.add_argument("-o", "--output", type=Path, default="warning_letters_URLs.csv")

    args = parser.parse_args()

    parse_urls(args.input, args.output)


if __name__ == "__main__":
    main()