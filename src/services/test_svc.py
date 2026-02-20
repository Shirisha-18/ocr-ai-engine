import os
import csv
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher

from dateparser import parse

# =================================================
# CONFIG
# =================================================

OCR_ROOT = r"C:\Users\shirisha.biyyala\Dropbox\ocr_patents\ocr_patents\random_sample"
REFERENCE_CSV = r"C:\Users\shirisha.biyyala\Dropbox\ocr_patents\patents_fyear_iyear.csv"
OUTPUT_CSV = rf"C:\Users\shirisha.biyyala\Dropbox\ocr_patents\info\patent_dates_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

EARLY_PATENT_NUM = 137279
FILING_START_DATE = datetime(1873, 4, 1)


# =================================================
# HELPERS
# =================================================
def normalize_patnum(patnum):
    return patnum.lstrip("0")


def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    return sorted(txt_files)[0] if txt_files else None


def normalize_text(text):
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def split_date(date_str):
    if not date_str or date_str in ["NA", ""]:
        return date_str, date_str, date_str
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        return str(dt.year), str(dt.month), str(dt.day)
    except ValueError:
        return "", "", ""


def fuzzy_contains(line, target, threshold=0.72):
    words = re.findall(r"[A-Za-z]{3,}", line.lower())
    for word in words:
        if SequenceMatcher(None, word, target).ratio() >= threshold:
            return True
    return False


# =================================================
# DATE EXTRACTION
# =================================================
def extract_date_from_line(line):
    """
    Flexible regex to capture dates like:
    November 6,1894
    Nov 6. 1894
    October 26, 1893
    """
    pattern = r"([A-Za-z]{3,9})\s*(\d{1,2})\s*[,\.]?\s*(\d{4})"
    m = re.search(pattern, line)
    if m:
        month, day, year = m.groups()
        dt = parse(f"{month} {day} {year}")
        if dt:
            return dt.strftime("%m/%d/%Y")
    return ""


def extract_patent_dates(text, patnum=None):
    text = normalize_text(text)
    lines = text.splitlines()

    combined_lines = []
    for i in range(len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        combined_lines.append(line)
        if i + 1 < len(lines):
            combined_lines.append(line + " " + lines[i + 1].strip())
        if i + 2 < len(lines):
            combined_lines.append(
                line + " " + lines[i + 1].strip() + " " + lines[i + 2].strip()
            )

    patent_date = ""
    filed_date = ""
    try:
        patnum_int = int(normalize_patnum(patnum)) if patnum else 0
    except:
        patnum_int = 0

    # -------- Early patents before filing rules --------
    if patnum_int < EARLY_PATENT_NUM:
        filed_date = "NA"

    # -------- Extract strong pattern dates --------
    for line in combined_lines:
        # Patent date detection
        if not patent_date and (
            fuzzy_contains(line, "patent")
            or fuzzy_contains(line, "issued")
            or "[45]" in line
            or "(45)" in line
        ):
            dt = extract_date_from_line(line)
            if dt:
                patent_date = dt
        # Filing date detection
        if (
            patnum_int >= EARLY_PATENT_NUM
            and not filed_date
            and (
                fuzzy_contains(line, "filed")
                or fuzzy_contains(line, "application")
                or "[22]" in line
                or "(22)" in line
            )
        ):
            dt = extract_date_from_line(line)
            if dt:
                filed_date = dt
        if patent_date and (filed_date or patnum_int < EARLY_PATENT_NUM):
            break

    # -------- Fuzzy rescue for missing dates --------
    if not patent_date or (patnum_int >= EARLY_PATENT_NUM and not filed_date):
        for line in combined_lines:
            m = re.search(r"([A-Za-z]{3,9})\s*(\d{1,2})\s*[,\.]?\s*(\d{4})", line)
            if not m:
                continue
            dt = parse(" ".join(m.groups()))
            if not dt:
                continue
            formatted = dt.strftime("%m/%d/%Y")
            if not patent_date and (
                fuzzy_contains(line.lower(), "patent") or "[45]" in line
            ):
                patent_date = formatted
            if (
                patnum_int >= EARLY_PATENT_NUM
                and not filed_date
                and (fuzzy_contains(line.lower(), "filed") or "[22]" in line)
            ):
                filed_date = formatted
            if patent_date and (filed_date or patnum_int < EARLY_PATENT_NUM):
                break

    # -------- Sanity check --------
    if patent_date and filed_date and filed_date != "NA":
        if parse(filed_date) > parse(patent_date):
            filed_date = ""

    return patent_date, filed_date


# =================================================
# REFERENCE LOADER
# =================================================
def load_csv_dict(path):
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = normalize_patnum(row["patnum"])
            data[key] = row
    return data


# =================================================
# VALIDATION + CONFLICT RESOLUTION
# =================================================
def compare_dates_with_flags(extracted_row, reference_row):
    patnum_int = int(normalize_patnum(extracted_row["patnum"]))

    if not reference_row:
        return "Missing in reference", "Missing in reference", "Missing"

    # -------- Early patents --------
    if patnum_int < EARLY_PATENT_NUM:
        patent_status = "No"
        if (
            extracted_row["iyear"] != reference_row.get("iyear")
            or extracted_row["imonth"] != reference_row.get("imonth")
            or extracted_row["iday"] != reference_row.get("iday")
        ):
            patent_status = "Yes"
        return patent_status, "NA", "Correct" if patent_status == "No" else "Wrong"

    # -------- Missing reference --------
    if not (
        reference_row.get("iyear")
        and reference_row.get("imonth")
        and reference_row.get("iday")
    ):
        return "Missing in reference", "Missing in reference", "Missing"
    if not (
        reference_row.get("fyear")
        and reference_row.get("fmonth")
        and reference_row.get("fday")
    ):
        return "Missing in reference", "Missing in reference", "Missing"

    # -------- Normal comparison --------
    patent_status = "No"
    if (
        extracted_row["iyear"] != reference_row["iyear"]
        or extracted_row["imonth"] != reference_row["imonth"]
        or extracted_row["iday"] != reference_row["iday"]
    ):
        patent_status = "Yes"

    filed_status = "No"
    if (
        extracted_row["fyear"] != reference_row["fyear"]
        or extracted_row["fmonth"] != reference_row["fmonth"]
        or extracted_row["fday"] != reference_row["fday"]
    ):
        filed_status = "Yes"

    flag = "Wrong" if "Yes" in (patent_status, filed_status) else "Correct"

    # -------- Conflict resolution: same dates --------
    if extracted_row["iyear"] == extracted_row["fyear"] and extracted_row[
        "iyear"
    ] not in ["", "NA"]:
        if patent_status == "No" and filed_status == "Yes":
            filed_status = "Yes-Recheck"
        elif patent_status == "Yes" and filed_status == "No":
            patent_status = "Yes-Recheck"
        elif patent_status == "Yes" and filed_status == "Yes":
            patent_status = "ERROR"

    return patent_status, filed_status, flag


# =================================================
# MAIN
# =================================================
def run():
    extracted_rows = []

    for folder in sorted(os.listdir(OCR_ROOT)):
        folder_path = os.path.join(OCR_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
        first_page = get_first_text_file(folder_path)
        if not first_page:
            continue
        with open(
            os.path.join(folder_path, first_page),
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            text = f.read()

        patent_date, filed_date = extract_patent_dates(text, folder)
        pyear, pmonth, pday = split_date(patent_date)
        if filed_date != "NA":
            fyear, fmonth, fday = split_date(filed_date)
        else:
            fyear, fmonth, fday = "NA", "NA", "NA"

        extracted_rows.append(
            {
                "patnum": folder,
                "iyear": pyear,
                "imonth": pmonth,
                "iday": pday,
                "fyear": fyear,
                "fmonth": fmonth,
                "fday": fday,
            }
        )

        print(f"[OK] {folder} | Patent: {patent_date or 'N/A'} | Filed: {filed_date}")

    reference_dict = load_csv_dict(REFERENCE_CSV)

    final_rows = []
    for row in extracted_rows:
        ref_row = reference_dict.get(normalize_patnum(row["patnum"]))
        pw, fw, flag = compare_dates_with_flags(row, ref_row)
        final_rows.append({**row, "patent_wrong": pw, "filed_wrong": fw, "flag": flag})

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=final_rows[0].keys())
        writer.writeheader()
        writer.writerows(final_rows)

    print(f"\n✅ Done! Comparison CSV saved to:\n{OUTPUT_CSV}")


# =================================================
# ENTRY POINT
# =================================================
if __name__ == "__main__":
    run()
