import re
import os
from dateutil import parser
from datetime import datetime
import glob

# -------------------------------
# Date extraction pattern
# -------------------------------
MONTHS = (
    "Jan(?:uary)?",
    "Feb(?:ruary)?",
    "Mar(?:ch)?",
    "Apr(?:il)?",
    "May",
    "Jun(?:e)?",
    "Jul(?:y)?",
    "Aug(?:ust)?",
    "Sep(?:t(?:ember)?)?",
    "Oct(?:ober)?",
    "Nov(?:ember)?",
    "Dec(?:ember)?",
)
MONTH_REGEX = "|".join(MONTHS)

DATE_PATTERN = re.compile(
    rf'\b(?:"?)(?:\d{{1,2}}\s+(?:{MONTH_REGEX})|(?:{MONTH_REGEX})\.?\s*\d{{1,2}}),?\s*\d{{2,4}}(?:")?\b',
    flags=re.IGNORECASE,
)


# -------------------------------
# Utility functions
# -------------------------------
def is_valid_date_candidate(date_str):
    invalid_keywords = ["DECEASED", "of", "1,071", "No."]
    date_str_clean = date_str.replace("\n", " ").replace('"', "")
    if any(word.upper() in date_str_clean.upper() for word in invalid_keywords):
        return False
    return True


def normalize_date(date_str):
    date_str_clean = date_str.replace("\n", " ").replace('"', "").strip()
    try:
        dt = parser.parse(date_str_clean, fuzzy=True)
        return dt
    except (ValueError, OverflowError):
        return None


# -------------------------------
# Metadata extraction
# -------------------------------
def extract_metadata(text):
    # Dates
    clean_text = text.replace("\n", " ").replace('"', "")
    date_matches = DATE_PATTERN.findall(clean_text)

    valid_dates = []
    for d in date_matches:
        if not is_valid_date_candidate(d):
            continue
        dt = normalize_date(d)
        if dt:
            valid_dates.append(dt)

    valid_dates.sort()

    # OS-aware formatting
    day_format = "%#d" if os.name == "nt" else "%-d"
    date_format = f"{day_format}-%b-%y"

    if len(valid_dates) >= 2:
        application_date = valid_dates[0].strftime(date_format)
        patent_date = valid_dates[-1].strftime(date_format)
        date_missing = "NO"
    elif len(valid_dates) == 1:
        application_date = valid_dates[0].strftime(date_format)
        patent_date = ""
        date_missing = "INVALID"
    else:
        application_date = ""
        patent_date = ""
        date_missing = "INVALID"

    return {
        "application_date": application_date,
        "patent_date": patent_date,
        "date_missing": date_missing,
        "all_dates": ", ".join([d.strftime(date_format) for d in valid_dates]),
    }


# -------------------------------
# Main runner
# -------------------------------
def run_metadata_extraction(folder_path):
    text_files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not text_files:
        print("[ERROR] No text files found in folder:", folder_path)
        return

    for file_path in text_files:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        meta = extract_metadata(text)
        print(f"[OK] {os.path.basename(file_path)}")
        print(meta)


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    folder = (
        "C:/Users/shiri/OneDrive/Documents/Python/llm-projects/ocr-ai-engine/text_files"
    )
    run_metadata_extraction(folder)
