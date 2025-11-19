import re
import os
from dateutil import parser
from datetime import datetime

# -------------------------------
# Patterns
# -------------------------------
DATE_PATTERN = re.compile(
    r"(\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s*\d{1,2},?\s*\d{2,4})",
    flags=re.IGNORECASE,
)
NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b")
LOCATION_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b")


# -------------------------------
# Utility functions
# -------------------------------
def is_valid_date_candidate(date_str):
    """Return False for known OCR garbage or invalid patterns"""
    invalid_keywords = ["DECEASED", "of", "1,071"]
    date_str_clean = date_str.replace("\n", " ").replace('"', "")
    if any(word in date_str_clean.upper() for word in invalid_keywords):
        return False
    return True


def normalize_date(date_str):
    """Return datetime object or None if parsing fails"""
    date_str_clean = date_str.replace("\n", " ").replace('"', "").strip()
    try:
        dt = parser.parse(date_str_clean, dayfirst=False, fuzzy=True)
        return dt
    except (ValueError, OverflowError):
        return None


def split_header_body(text):
    """Optionally split header and body for names/locations"""
    lines = text.splitlines()
    header = " ".join(lines[:10])  # First 10 lines as header
    body = " ".join(lines[10:])
    return header, body


# -------------------------------
# Metadata extraction
# -------------------------------
def extract_metadata(text):
    header, body = split_header_body(text)

    # --- Names ---
    name_header = ", ".join(sorted(set(NAME_PATTERN.findall(header))))
    name_body = ", ".join(sorted(set(NAME_PATTERN.findall(body))))
    names_missing = "NO" if name_header or name_body else "INVALID"

    # --- Locations ---
    location_header = ", ".join(sorted(set(LOCATION_PATTERN.findall(header))))
    location_body = ", ".join(sorted(set(LOCATION_PATTERN.findall(body))))
    locations_missing = "NO" if location_header or location_body else "INVALID"

    # --- Dates ---
    clean_text = text.replace("\n", " ").replace('"', "")
    date_matches = DATE_PATTERN.findall(clean_text)

    valid_dates = []
    for d in date_matches:
        if not is_valid_date_candidate(d):
            continue
        dt = normalize_date(d)
        if dt:
            valid_dates.append(dt)

    # Sort ascending
    valid_dates.sort()

    # Safe day format for Windows vs Unix
    day_format = "%#d" if os.name == "nt" else "%-d"
    date_format = f"{day_format}-%b-%y"

    # Determine application date (earliest) and patent date (latest)
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

    all_dates = ", ".join([d.strftime(date_format) for d in valid_dates])

    return {
        "name_header": name_header,
        "name_body": name_body,
        "names_missing": names_missing,
        "location_header": location_header,
        "location_body": location_body,
        "locations_missing": locations_missing,
        "application_date": application_date,
        "patent_date": patent_date,
        "all_dates": all_dates,
        "date_missing": date_missing,
    }


# -------------------------------
# Main runner
# -------------------------------
def run_metadata_extraction(file_paths=None):
    if file_paths is None:
        file_paths = ["00000002_text.txt", "00000003_text.txt"]  # example

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        meta = extract_metadata(text)
        print(f"[OK] {file_path}")
        print(meta)


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    run_metadata_extraction()
