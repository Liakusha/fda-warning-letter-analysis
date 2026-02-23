import pandas as pd
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import re
import time
import argparse

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.fda.gov"
}


def normalize_text(text: str | None):
    if not isinstance(text, str):
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_letter(session: requests.Session, url: str):
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        article = soup.find("article")

        raw_text = (
            article.get_text("\n", strip=True)
            if article else soup.get_text("\n", strip=True)
        )

        return raw_text, normalize_text(raw_text)

    except requests.RequestException:
        return None, None


def collect_text(input_csv: Path, output_csv: Path, delay: float = 2.5):

    df = pd.read_csv(input_csv)

    if "letter_text_raw" not in df.columns:
        df["letter_text_raw"] = None
    if "letter_text" not in df.columns:
        df["letter_text"] = None

    session = requests.Session()
    session.headers.update(HEADERS)

    for i, row in df.iterrows():

        if pd.notna(row["letter_text"]):
            continue  # resumable

        url = row.get("letter_url")
        if not isinstance(url, str):
            continue

        print(f"[{i}] downloading")

        raw, clean = extract_letter(session, url)

        df.at[i, "letter_text_raw"] = raw
        df.at[i, "letter_text"] = clean

        if i % 20 == 0:
            df.to_csv(output_csv, index=False)  # checkpoint save

        time.sleep(delay)

    df.to_csv(output_csv, index=False)
    print("Saved:", output_csv)


def main():
    parser = argparse.ArgumentParser(description="FDA Warning Letter text collector")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, default="warning_letters_text.csv")
    parser.add_argument("--delay", type=float, default=2.5)

    args = parser.parse_args()
    collect_text(args.input, args.output, args.delay)


if __name__ == "__main__":
    main()
