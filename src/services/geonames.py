import os
import re
import csv
from datetime import datetime
from difflib import get_close_matches
import geonamescache

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# Load city database from geonamescache
gc = geonamescache.GeonamesCache()
CITIES = {c["name"].lower(): c for c in gc.get_cities().values()}


def fix_month_typo(raw_date):
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    for word in raw_date.split():
        matches = get_close_matches(word, months, n=1, cutoff=0.7)
        if matches:
            raw_date = raw_date.replace(word, matches[0])
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
            dt = datetime.strptime(raw_date, fmt)
            return dt.strftime("%m/%d/%Y")  # MM/DD/YYYY
        except:
            continue
    return raw_date


def split_header_body(text, max_header_lines=12):
    lines = text.split("\n")
    header = "\n".join(lines[:max_header_lines])
    body = "\n".join(lines[max_header_lines:])
    return header, body, lines[:max_header_lines]


def extract_names_and_locations(header_lines, body_text):
    name_header, location_header = "", ""
    for line in header_lines:
        match = re.search(
            r"([A-Z][A-Za-z\s\.\-']+), OF ([A-Z][A-Z\s\.\-']+),? ([A-Z]{2,})?", line
        )
        if match:
            name_header = match.group(1).title()
            city_header = match.group(2).title()
            state_header = match.group(3).upper() if match.group(3) else ""
            location_header = (
                f"{city_header}, {state_header}" if state_header else city_header
            )
            break

    body_match = re.search(
        r"I, ([A-Z][A-Za-z\s\.\-']+), (?:a resident of |citizen of |residing at )?(.+?), in the county of (.+?) and State of (.+?)",
        body_text,
        re.IGNORECASE | re.DOTALL,
    )
    if body_match:
        name_body = body_match.group(1).title()
        city_body = body_match.group(2).strip().title()
        county_body = body_match.group(3).strip().title()
        state_body = body_match.group(4).strip().title()
        location_body = f"{county_body} County, {city_body}, {state_body}"
    else:
        name_body = name_header
        location_body = location_header

    return name_header, name_body, location_header, location_body


def extract_date(text):
    date_regex = r"(\b(?:[A-Za-z]+\.?\s\d{1,2},\s\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b)"
    match = re.search(date_regex, text)
    if match:
        return normalize_date(match.group(1))
    return ""


def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    txt_files_sorted = sorted(
        txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0])
    )
    return txt_files_sorted[0]


# --- New function to validate location ---
def is_location_real(location_text):
    parts = [p.strip() for p in location_text.split(",")]
    if len(parts) >= 2:
        city = parts[-2].lower()
        if city in CITIES:
            return "YES"
    return "NO"


def run_metadata_extraction():
    rows = []

    for folder in sorted(os.listdir(OCR_ROOT)):
        folder_path = os.path.join(OCR_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue

        first_page = get_first_text_file(folder_path)
        if not first_page:
            print(f"[NO OCR FILE] {folder}")
            continue

        with open(
            os.path.join(folder_path, first_page),
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            text = f.read()

        header, body, header_lines = split_header_body(text)
        name_header, name_body, location_header, location_body = (
            extract_names_and_locations(header_lines, body)
        )
        date = extract_date(text)

        names_missing = "YES" if not name_header and not name_body else "NO"
        locations_missing = "YES" if not location_header and not location_body else "NO"
        location_accurate = is_location_real(location_header) or is_location_real(
            location_body
        )

        rows.append(
            {
                "folder": folder,
                "first_page": first_page,
                "name_header": name_header,
                "name_body": name_body,
                "names_missing": names_missing,
                "location_header": location_header,
                "location_body": location_body,
                "locations_missing": locations_missing,
                "location_accurate": "YES" if location_accurate else "NO",
                "date": date,
                "date_missing": "YES" if not date else "NO",
            }
        )

        print(f"[OK] {folder} → {first_page}")

    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "folder",
                "first_page",
                "name_header",
                "name_body",
                "names_missing",
                "location_header",
                "location_body",
                "locations_missing",
                "location_accurate",
                "date",
                "date_missing",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved metadata to:\n{OUTPUT_FILE}\n")


if __name__ == "__main__":
    run_metadata_extraction()
