import os
import re
import csv
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import geonamescache

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
LOCK_FILE = r"C:\Users\shiri\Dropbox\ocr_patents\metadata_extraction.lock"

MAX_SCAN_LINES = 100  # scan only first 100 lines for names/title
THREADS = 4  # number of parallel threads for speed


# ------------------ Lock Mechanism ------------------ #
def acquire_lock():
    if os.path.exists(LOCK_FILE):
        print("Another instance is running. Exiting.")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# ------------------ Geonames & Month Corrections ------------------ #
gc = geonamescache.GeonamesCache()
CITIES = {
    (c["name"].lower(), c["countrycode"].upper()): c for c in gc.get_cities().values()
}

MONTH_CORRECTIONS = {
    "Januaray": "January",
    "Febuary": "February",
    "Decemeber": "December",
}

# ------------------ Precompiled Regex ------------------ #
NAME_BODY_PATTERN = re.compile(
    r"I,\s*((?:[A-Z][A-Za-z\.\-']+\s?)+(?:,?\s?(?:and\s)?(?:[A-Z][A-Za-z\.\-']+\s?)+)*)"
    r"(?:,?\s*(?:a resident of|citizen of|residing at)\s(.+?)),?\s*in the county of\s(.+?)\s*and\s*State of\s(.+?)",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(
    r"\b(?:[A-Za-z]+\.?\s\d{1,2},\s\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b"
)


# ------------------ Utility Functions ------------------ #
def fix_month_typo(raw_date):
    for wrong, correct in MONTH_CORRECTIONS.items():
        raw_date = raw_date.replace(wrong, correct)
    return raw_date


def normalize_date(raw_date):
    if not raw_date:
        return ""
    raw_date = fix_month_typo(raw_date)
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%b-%y",
        "%d-%B-%y",
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(raw_date, fmt).strftime("%m/%d/%Y")
        except:
            continue
    return raw_date


def split_header_body(text, max_header_lines=12):
    lines = text.split("\n")
    return (
        "\n".join(lines[:max_header_lines]),
        "\n".join(lines[max_header_lines:]),
        lines[:max_header_lines],
    )


def is_location_real(location_text):
    parts = [p.strip() for p in location_text.split(",")]
    if len(parts) >= 2:
        city, state = parts[-2].lower(), parts[-1].upper()
        if (city, state) in CITIES:
            return "YES"
    return "NO"


# ------------------ Extraction Functions ------------------ #
def extract_names_and_locations(header_lines, body_lines):
    name_header = location_header = ""
    name_body = location_body = ""

    # Header scan
    for line in header_lines:
        match = re.search(
            r"([A-Z][A-Za-z\s\.\-']+), OF ([A-Z][A-Z\s\.\-']+),? ([A-Z]{2,})?", line
        )
        if match:
            name_header = match.group(1)
            city_header = match.group(2).title()
            state_header = match.group(3).upper() if match.group(3) else ""
            location_header = (
                f"{city_header}, {state_header}" if state_header else city_header
            )
            break

    # Body scan (first MAX_SCAN_LINES)
    for line in body_lines[:MAX_SCAN_LINES]:
        line = line.strip()
        match = NAME_BODY_PATTERN.search(line)
        if match:
            name_body = match.group(1)
            city_body = match.group(2).title()
            county_body = match.group(3).title()
            state_body = match.group(4).upper()
            location_body = f"{county_body} County, {city_body}, {state_body}"
            break

    if not name_body:
        name_body = name_header
        location_body = location_header

    return name_header, name_body, location_header, location_body


def extract_date(text):
    match = DATE_PATTERN.search(text)
    if match:
        return normalize_date(match.group(0))
    return ""


def extract_patent_title(body_lines):
    for line in body_lines[:MAX_SCAN_LINES]:
        line = line.strip()
        if (
            line.isupper()
            and len(line) > 3
            and not any(char.isdigit() for char in line)
        ):
            return re.sub(r"\s{2,}", " ", line)
    return ""


def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    return sorted(txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0]))[0]


# ------------------ Process Single Folder ------------------ #
def process_folder(folder):
    folder_path = os.path.join(OCR_ROOT, folder)
    if not os.path.isdir(folder_path):
        return None

    first_page = get_first_text_file(folder_path)
    if not first_page:
        print(f"[NO OCR FILE] {folder}")
        return None

    with open(
        os.path.join(folder_path, first_page), "r", encoding="utf-8", errors="ignore"
    ) as f:
        text = f.read()

    header, body, header_lines = split_header_body(text)
    body_lines = body.split("\n")
    name_header, name_body, location_header, location_body = (
        extract_names_and_locations(header_lines, body_lines)
    )
    date = extract_date(text)
    title = extract_patent_title(body_lines)

    print(f"[OK] {folder} → {first_page}")

    return {
        "folder": folder,
        "first_page": first_page,
        "patent_title": title,
        "name_header": name_header,
        "name_body": name_body,
        "names_missing": "YES" if not name_header and not name_body else "NO",
        "location_header": location_header,
        "location_body": location_body,
        "locations_missing": "YES"
        if not location_header and not location_body
        else "NO",
        "location_accurate": "YES"
        if is_location_real(location_header) or is_location_real(location_body)
        else "NO",
        "date": date,
        "date_missing": "YES" if not date else "NO",
    }


# ------------------ Main Function ------------------ #
def run_metadata_extraction():
    acquire_lock()
    try:
        folders = sorted(os.listdir(OCR_ROOT))
        rows = []

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            results = executor.map(process_folder, folders)
            for r in results:
                if r:
                    rows.append(r)

        if rows:
            with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            print(f"\nSaved metadata to:\n{OUTPUT_FILE}\n")
        else:
            print("No OCR files processed.")
    finally:
        release_lock()


if __name__ == "__main__":
    run_metadata_extraction()
