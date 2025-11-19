import re
import os
import csv
from datetime import datetime
from dateutil import parser

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


# ----- Split header and body -----
def split_header_body(text, max_header_lines=12):
    lines = text.split("\n")
    header = "\n".join(lines[:max_header_lines])
    body = "\n".join(lines[max_header_lines:])
    return header, body


# ----- REGEX patterns -----
NAME_PATTERN = re.compile(r"\b([A-Z][A-Za-z'\-]+(?: [A-Z][A-Za-z'\-]+)*)\b")
LOCATION_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z .'-]+,\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY))\b"
)
DATE_PATTERN = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
    r"January|February|March|April|May|June|July|August|September|October|November|December)"
    r"[a-z]*\.?\s+\d{1,2},\s+\d{2,4}"  # Feb 11, 1873
    r"|\d{1,2}-[A-Za-z]{3}-\d{2,4}"  # 2-Jul-12
    r"|\d{1,2}\s+[A-Za-z]+,?\s+\d{4}",  # 7 June 1870
    re.IGNORECASE,
)


# ----- Normalize date safely -----
def normalize_date(raw_date):
    try:
        dt = parser.parse(raw_date, fuzzy=True, default=datetime(1900, 1, 1))
        return dt
    except Exception:
        return None  # Invalid date


# ----- Check if a string is a valid date candidate -----
def is_valid_date_candidate(s):
    s = s.strip()
    # Skip obvious non-dates
    invalid_keywords = ["DECEASED", "PATENT", "APPLICATION", "FIG", "NO", "OF"]
    if any(word in s.upper() for word in invalid_keywords):
        return False
    # Must contain at least a month name and a year
    if not re.search(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)",
        s,
        re.IGNORECASE,
    ):
        return False
    if not re.search(r"\d{2,4}", s):
        return False
    return True


# ----- Extract metadata -----
def extract_metadata(text):
    header, body = split_header_body(text)

    # Names
    name_header = ", ".join(sorted(set(NAME_PATTERN.findall(header))))
    name_body = ", ".join(sorted(set(NAME_PATTERN.findall(body))))
    names_missing = "NO" if name_header or name_body else "INVALID"

    # Locations
    location_header = ", ".join(sorted(set(LOCATION_PATTERN.findall(header))))
    location_body = ", ".join(sorted(set(LOCATION_PATTERN.findall(body))))
    locations_missing = "NO" if location_header or location_body else "INVALID"

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

    # Sort dates ascending
    valid_dates.sort()

    # Assign dates
    if len(valid_dates) >= 2:
        application_date = valid_dates[0].strftime("%-d-%b-%y")
        patent_date = valid_dates[-1].strftime("%-d-%b-%y")
        date_missing = "NO"
    elif len(valid_dates) == 1:
        application_date = valid_dates[0].strftime("%-d-%b-%y")
        patent_date = ""
        date_missing = "INVALID"
    else:
        application_date = ""
        patent_date = ""
        date_missing = "INVALID"

    all_dates = ", ".join([d.strftime("%-d-%b-%y") for d in valid_dates])

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


# ----- Get first OCR text file -----
def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    txt_files_sorted = sorted(
        txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0])
    )
    return txt_files_sorted[0]


# ----- Main loop -----
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

        meta = extract_metadata(text)
        rows.append({"folder": folder, "first_page": first_page, **meta})
        print(f"[OK] {folder} → {first_page}")

    # Write CSV
    fieldnames = [
        "folder",
        "first_page",
        "name_header",
        "name_body",
        "names_missing",
        "location_header",
        "location_body",
        "locations_missing",
        "application_date",
        "patent_date",
        "all_dates",
        "date_missing",
    ]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved metadata to:\n{OUTPUT_FILE}\n")


if __name__ == "__main__":
    run_metadata_extraction()
