import os
import re
import csv
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

MONTH_CORRECTIONS = {
    "Januaray": "January",
    "Febuary": "February",
    "Decemeber": "December",
}


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


NAME_BODY_REGEX = re.compile(
    r"I,\s*((?:[A-Z][A-Za-z\.\-']+\s?)+(?:,?\s?(?:and\s)?(?:[A-Z][A-Za-z\.\-']+\s?)+)*)"
    r", (?:a resident of |citizen of |residing at )?(.+?), in the county of (.+?) and State of (.+?)",
    re.IGNORECASE | re.DOTALL,
)


def extract_names_and_locations(header_lines, body_text):
    name_header, location_header = "", ""

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

    body_match = NAME_BODY_REGEX.search(body_text)
    if body_match:
        name_body = body_match.group(1)
        city_body = body_match.group(2).strip().title()
        county_body = body_match.group(3).strip().title()
        state_body = body_match.group(4).strip().title()
        location_body = f"{county_body} County, {city_body}, {state_body}"
    else:
        name_body = name_header
        location_body = location_header

    return name_header, name_body, location_header, location_body


def extract_date(text):
    date_regex = re.compile(
        r"\b(?:[A-Za-z]+\.?\s\d{1,2},\s\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b"
    )
    match = date_regex.search(text)
    if match:
        return normalize_date(match.group(0))
    return ""


def extract_patent_title(text):
    match = re.search(r"Title[:\.\s]+(.+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    return sorted(txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0]))[0]


# ------------------ PROCESS ONE FOLDER ------------------ #
def process_folder(folder):
    start = time.time()

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

    name_header, name_body, location_header, location_body = (
        extract_names_and_locations(header_lines, body)
    )
    date = extract_date(text)
    patent_title = extract_patent_title(text)

    elapsed = time.time() - start
    print(f"[OK] {folder} → {elapsed:.2f} sec")

    return {
        "folder": folder,
        "first_page": first_page,
        "patent_title": patent_title,
        "name_header": name_header,
        "name_body": name_body,
        "names_missing": "YES" if not name_header and not name_body else "NO",
        "location_header": location_header,
        "location_body": location_body,
        "locations_missing": "YES"
        if not location_header and not location_body
        else "NO",
        "date": date,
        "date_missing": "YES" if not date else "NO",
    }


# ------------------ MAIN ------------------ #
def run():
    folders = sorted(os.listdir(OCR_ROOT))

    # Use CPU count but not all (Windows stays stable with 4–8)
    workers = max(4, cpu_count() // 2)

    print(f"\n🚀 Using {workers} parallel processes...\n")

    with Pool(workers) as pool:
        results = pool.map(process_folder, folders)

    # Filter None results
    rows = [r for r in results if r]

    if rows:
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        print(f"\nSaved metadata to:\n{OUTPUT_FILE}\n")
    else:
        print("No OCR files processed.")


if __name__ == "__main__":
    run()
