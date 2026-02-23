import os
import json
import pandas as pd
from pathlib import Path
import time
import argparse
import google.generativeai as genai


SCHEMA = {
    "violations": [],
    "cfr_references": [],
    "qa_domain": "",
    "severity_signal": "",
    "summary_2_sentences": ""
}


def build_prompt(text: str) -> str:
    return f"""You are a pharmaceutical Quality Assurance expert.

Return ONLY valid JSON.
Do not include explanations, markdown, or text outside JSON.

JSON schema:
{json.dumps(SCHEMA, indent=2)}

Text:
{text}
"""


def clean_response(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    return raw


def analyze(input_csv: Path, output_csv: Path, delay: float, model_name: str):

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    df = pd.read_csv(input_csv)

    # ensure columns exist (resumable)
    cols = [
        "llm_violations", "llm_cfr_refs", "llm_qa_domain",
        "llm_severity", "llm_summary_2s", "llm_confidence"
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = None

    for i, row in df.iterrows():

        if pd.notna(row["llm_confidence"]):
            continue  # already processed

        text = row.get("letter_text")
        if not isinstance(text, str) or not text.strip():
            df.at[i, "llm_confidence"] = "EMPTY"
            continue

        print(f"[{i}] LLM analyzing")

        try:
            response = model.generate_content(
                build_prompt(text),
                generation_config={"temperature": 0}
            )

            raw = clean_response(response.text)
            parsed = json.loads(raw)

            df.at[i, "llm_violations"] = json.dumps(parsed["violations"])
            df.at[i, "llm_cfr_refs"]   = json.dumps(parsed["cfr_references"])
            df.at[i, "llm_qa_domain"]  = parsed["qa_domain"]
            df.at[i, "llm_severity"]   = parsed["severity_signal"]
            df.at[i, "llm_summary_2s"] = parsed["summary_2_sentences"]
            df.at[i, "llm_confidence"] = "OK"

        except json.JSONDecodeError:
            df.at[i, "llm_confidence"] = "JSON_FAIL"

        except Exception:
            df.at[i, "llm_confidence"] = "API_FAIL"

        if i % 5 == 0:
            df.to_csv(output_csv, index=False)

        time.sleep(delay)

    df.to_csv(output_csv, index=False)
    print("Saved:", output_csv)


def main():
    parser = argparse.ArgumentParser(description="FDA Warning Letter LLM analyzer")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, default="warning_letters_full.csv")
    parser.add_argument("--delay", type=float, default=7)
    parser.add_argument("--model", type=str, default="gemini-2.5-flash")

    args = parser.parse_args()
    analyze(args.input, args.output, args.delay, args.model)


if __name__ == "__main__":
    main()
