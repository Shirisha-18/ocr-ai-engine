import os
import re
import csv
from datetime import datetime
from difflib import get_close_matches
import spacy

# -----------------------------
# CONFIG
# -----------------------------
OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

HEADER_MAX_LINES = 25
nlp = spacy.load("en_core_web_sm")  # spaCy NER

# -----------------------------
# DATE HELPERS
# -----------------------------
MONTHS = [
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


def fix_month_typo(raw_date: str) -> str:
    for word in raw_date.split():
        matches = get_close_matches(word, MONTHS, n=1, cutoff=0.7)
        if matches:
            raw_date = raw_date.replace(word, matches[0])
    return raw_date


def normalize_date(raw_date: str) -> str:
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
        except Exception:
            continue
    return raw_date


# -----------------------------
# FILE HELPERS
# -----------------------------
def get_first_text_file(folder_path: str):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    return sorted(txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0]))[0]


def split_header(text: str):
    lines = text.split("\n")[:HEADER_MAX_LINES]
    return lines


# -----------------------------
# RULES & EXTRACTION
# -----------------------------
def extract_patent_number(text: str) -> str:
    patterns = [
        r"(?:Patent No\.?|No\.|Appl\. No\.|Serial No\.):?\s*([\d,]+)",
        r"US\s*([\d,]{4,})",
        r"Patented\s*[:#]?\s*([\d,]{4,})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).replace(",", "").strip()
    return ""


def extract_serial_number(text: str) -> str:
    patterns = [
        r"(?:Serial|Application|Appl\.?)\s*(?:No\.?|Number)?\s*[:#]?\s*([\d/,\-]{4,})"
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def extract_dates(text: str):
    doc = nlp(text)
    app_date = ""
    pat_date = ""
    for ent in doc.ents:
        if ent.label_ != "DATE":
            continue
        start = max(0, ent.start_char - 60)
        end = min(len(text), ent.end_char + 60)
        window = text[start:end].lower()
        if any(k in window for k in ["application filed", "filed", "appl"]):
            if not app_date:
                app_date = normalize_date(ent.text)
        if any(k in window for k in ["patented", "date of patent", "issued"]):
            if not pat_date:
                pat_date = normalize_date(ent.text)
    return app_date, pat_date


def extract_names_and_locations(header_lines):
    header_text = "\n".join(header_lines)
    doc = nlp(header_text)
    persons, locations = [], []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            persons.append(ent.text)
        if ent.label_ in ("GPE", "LOC"):
            locations.append(ent.text)
    # Deduplicate and join by comma
    persons = ", ".join(list(dict.fromkeys(persons)))
    locations = ", ".join(list(dict.fromkeys(locations)))
    return persons, locations


def extract_title(header_lines):
    """
    Heuristic: First ALL-CAPS line that is NOT noise (ignore PATENT OFFICE / SPECIFICATION)
    """
    blacklist = [
        "UNITED STATES",
        "PATENT",
        "OFFICE",
        "SPECIFICATION",
        "ABSTRACT",
        "BACKGROUND",
    ]
    for line in header_lines:
        line_strip = line.strip()
        if len(line_strip) < 3:
            continue
        if line_strip.isupper() and not any(b in line_strip for b in blacklist):
            return line_strip.title()
    return ""


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_extraction():
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
        header_lines = split_header(text)
        header_text = "\n".join(header_lines)

        title = extract_title(header_lines)
        patent_number = extract_patent_number(header_text)
        serial_number = extract_serial_number(header_text)
        application_date, patent_date = extract_dates(header_text)
        names, locations = extract_names_and_locations(header_lines)

        rows.append(
            {
                "folder": folder,
                "first_page": first_page,
                "title": title,
                "names": names,
                "locations": locations,
                "patent_number": patent_number,
                "serial_number": serial_number,
                "application_date": application_date,
                "patent_date": patent_date,
            }
        )
        print(f"[OK] {folder} → {first_page}")

    # Save CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "folder",
                "first_page",
                "title",
                "names",
                "locations",
                "patent_number",
                "serial_number",
                "application_date",
                "patent_date",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to:\n{OUTPUT_FILE}\n")


if __name__ == "__main__":
    run_extraction()
