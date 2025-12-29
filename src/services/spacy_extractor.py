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
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_spacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

HEADER_MAX_LINES = 20
BODY_SNIPPET_CHARS = 3000
MAX_SCAN_LINES = 40  # for patent title

# Load spaCy once
nlp = spacy.load("en_core_web_sm")


# -----------------------------
# DATE HELPERS
# -----------------------------
def fix_month_typo(raw_date: str) -> str:
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
            pass
    return raw_date


# -----------------------------
# FILE / TEXT HELPERS
# -----------------------------
def split_header_body(text: str, max_header_lines: int = HEADER_MAX_LINES):
    lines = text.split("\n")
    header = "\n".join(lines[:max_header_lines])
    body = "\n".join(lines[max_header_lines:])
    return header, body, lines[:max_header_lines]


def get_first_text_file(folder_path: str):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    return sorted(txt_files, key=lambda x: int(re.findall(r"(\d+)_text\.txt", x)[0]))[0]


# -----------------------------
# IDENTIFIERS (RULE-BASED)
# -----------------------------
def extract_patent_number(text: str) -> str:
    patterns = [
        r"(?:U\.?\s*S\.?\s*)?Patent\s*(?:No\.?|Number)?\s*[:#]?\s*([\d,]{4,})",
        r"Patented\s*[:#]?\s*([\d,]{4,})",
        r"US\s*([\d,]{4,})",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).replace(",", "").strip()
    return ""


def extract_serial_number(text: str) -> str:
    patterns = [
        r"(?:Serial|Application)\s*(?:No\.?|Number)?\s*[:#]?\s*([\d/,\-]{4,})",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


# -----------------------------
# TITLE EXTRACTION (RULE-BASED)
# -----------------------------
def extract_patent_title(body_lines):
    """
    Extract ALL-CAPS patent title near top of body.
    """
    blacklist = {
        "UNITED STATES PATENT",
        "UNITED STATES OF AMERICA",
        "PATENT",
        "ABSTRACT",
        "BACKGROUND",
        "SPECIFICATION",
    }

    for line in body_lines[:MAX_SCAN_LINES]:
        line = line.strip()

        if not line:
            continue
        if not line.isupper():
            continue
        if len(line) < 5:
            continue
        if any(char.isdigit() for char in line):
            continue
        if any(b in line for b in blacklist):
            continue

        return re.sub(r"\s{2,}", " ", line)

    return ""


# -----------------------------
# DATE EXTRACTION (spaCy)
# -----------------------------
def extract_application_and_patent_dates(text: str) -> tuple[str, str]:
    doc = nlp(text)
    app_date = ""
    pat_date = ""

    for ent in doc.ents:
        if ent.label_ != "DATE":
            continue

        start = max(0, ent.start_char - 60)
        end = min(len(text), ent.end_char + 60)
        window = text[start:end].lower()

        if any(k in window for k in ["application filed", "filed", "filcd", "filad"]):
            if not app_date:
                app_date = normalize_date(ent.text)

        if any(k in window for k in ["patented", "date of patent", "issued"]):
            if not pat_date:
                pat_date = normalize_date(ent.text)

    return app_date, pat_date


# -----------------------------
# OPTIONAL spaCy PERSON / GPE
# -----------------------------
def extract_people_gpe_from_header(header: str) -> tuple[str, str]:
    doc = nlp(header)
    person = ""
    gpe = ""

    for ent in doc.ents:
        if ent.label_ == "PERSON" and not person:
            person = ent.text.strip()
        if ent.label_ in ("GPE", "LOC") and not gpe:
            gpe = ent.text.strip()
        if person and gpe:
            break

    return person, gpe


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

        header, body, header_lines = split_header_body(text)
        body_lines = body.split("\n")

        header_for_spacy = header
        body_snippet = body[:BODY_SNIPPET_CHARS]

        patent_title = extract_patent_title(body_lines)
        patent_number = extract_patent_number(header_for_spacy + "\n" + body_snippet)
        serial_number = extract_serial_number(header_for_spacy + "\n" + body_snippet)
        application_filed_date, patented_date = extract_application_and_patent_dates(
            header_for_spacy + "\n" + body_snippet
        )

        name_spacy, location_spacy = extract_people_gpe_from_header(header_for_spacy)

        rows.append(
            {
                "folder": folder,
                "first_page": first_page,
                "patent_title": patent_title,
                "patent_title_missing": "YES" if not patent_title else "NO",
                "patent_number": patent_number,
                "serial_number": serial_number,
                "serial_missing": "YES" if not serial_number else "NO",
                "application_filed_date": application_filed_date,
                "patented_date": patented_date,
                "application_filed_missing": "YES"
                if not application_filed_date
                else "NO",
                "patented_date_missing": "YES" if not patented_date else "NO",
                "name_spacy": name_spacy,
                "location_spacy": location_spacy,
            }
        )

        print(f"[OK] {folder} → {first_page}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "folder",
                "first_page",
                "patent_title",
                "patent_title_missing",
                "patent_number",
                "serial_number",
                "serial_missing",
                "application_filed_date",
                "patented_date",
                "application_filed_missing",
                "patented_date_missing",
                "name_spacy",
                "location_spacy",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved to:\n{OUTPUT_FILE}\n")


if __name__ == "__main__":
    run_extraction()
