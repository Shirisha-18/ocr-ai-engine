import re
import os
import csv
from datetime import datetime

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"


def split_header_body(text, max_header_lines=12):
    lines = text.split("\n")
    header = "\n".join(lines[:max_header_lines])
    body = "\n".join(lines[max_header_lines:])
    return header, body


# ----- REGEX patterns -----

TITLE_PATTERN = re.compile(
    r"(United States Patent.*?)\n([A-Z0-9 ,.'\-:()]+)", re.IGNORECASE | re.DOTALL
)

NAME_PATTERN = re.compile(r"\b([A-Z][A-Za-z'\-]+(?: [A-Z][A-Za-z'\-]+)*)\b")

LOCATION_PATTERN = re.compile(
    r"\b([A-Za-z .'-]+,\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY))\b"
)

DATE_PATTERN = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, \d{4}\b",
    re.IGNORECASE,
)


def extract_metadata(text):
    header, body = split_header_body(text)

    # ----- Title -----
    title_header_match = TITLE_PATTERN.search(header)
    title_header = title_header_match.group(2).strip() if title_header_match else ""

    title_body_match = TITLE_PATTERN.search(body)
    title_body = title_body_match.group(2).strip() if title_body_match else ""

    # final title
    title = title_header if title_header else title_body

    # ----- Names -----
    name_header = ", ".join(sorted(set(NAME_PATTERN.findall(header))))
    name_body = ", ".join(sorted(set(NAME_PATTERN.findall(body))))

    # ----- Locations -----
    location_header = ", ".join(sorted(set(LOCATION_PATTERN.findall(header))))
    location_body = ", ".join(sorted(set(LOCATION_PATTERN.findall(body))))

    # ----- Date -----
    date_header = DATE_PATTERN.findall(header)
    date_body = DATE_PATTERN.findall(body)

    if date_header:
        date = date_header[0]
    elif date_body:
        date = date_body[0]
    else:
        date = ""

    # ----- Missing Flags -----
    title_missing = "YES" if title.strip() == "" else "NO"
    names_missing = "YES" if name_header == "" and name_body == "" else "NO"
    locations_missing = "YES" if location_header == "" and location_body == "" else "NO"
    date_missing = "YES" if date == "" else "NO"

    return {
        "title": title,
        "name_header": name_header,
        "name_body": name_body,
        "location_header": location_header,
        "location_body": location_body,
        "date": date,
        "title_missing": title_missing,
        "names_missing": names_missing,
        "locations_missing": locations_missing,
        "date_missing": date_missing,
    }


def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None

    # Sort numerically e.g., 00000002_text.txt
    txt_files_sorted = sorted(
        txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0])
    )
    return txt_files_sorted[0]


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

    # ----- Write CSV -----
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "folder",
                "first_page",
                "title",
                "title_missing",
                "name_header",
                "name_body",
                "names_missing",
                "location_header",
                "location_body",
                "locations_missing",
                "date",
                "date_missing",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved metadata to:\n{OUTPUT_FILE}\n")


if __name__ == "__main__":
    run_metadata_extraction()
