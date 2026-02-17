# FDA Warning Letters Analysis

Pipeline for collecting, structuring, and analyzing FDA Warning Letters using web scraping and LLM structured extraction.

The project builds a structured dataset from raw FDA warning letter publications.

---

## Project Pipeline

1. Collect warning letter URLs
2. Download letter text
3. Extract structured QA signals using LLM
4. Analyze dataset (Jupyter Notebook)

All processing steps are resumable and safe to re-run.

---

## Project Structure

```
project/
│
├── data/                       # input/output datasets
│
├── src/
│   ├── fda_urls_parser.py      # search FDA warning letter URLs
│   ├── bs_letter_collector.py  # download and clean letter text
│   └── llm_analyzer.py         # structured extraction via LLM
│
├── notebooks/                  # EDA and modeling
│
├── requirements.txt
└── README.md
```

---

## Setup

Python 3.10+

Create environment and install dependencies:

```
pip install -r requirements.txt
```

Set API key:

```
export GEMINI_API_KEY=YOUR_KEY
```

(Windows PowerShell)

```
setx GEMINI_API_KEY "YOUR_KEY"
```

---

## Usage

### 1 — Collect URLs

```
python -m src.fda_urls_parser data/warning_letters_cder_base_v1.xls
```

Output:

```
warning_letters_urls.csv
```

---

### 2 — Download Letter Text

```
python -m src.bs_letter_collector warning_letters_urls.csv
```

Output:

```
warning_letters_text.csv
```

---

### 3 — LLM Structured Extraction

```
python -m src.llm_analyzer warning_letters_text.csv
```

Output:

```
warning_letters_full.csv
```

---

## Notes

* FDA website enforces rate limiting
* Scripts may stop and can be safely re-run
* Previously processed rows will be skipped

---

## Final Dataset Fields

Each warning letter is converted into structured fields:

* violations
* CFR references
* QA domain classification
* severity signal
* 2-sentence summary

---

## License

MIT
