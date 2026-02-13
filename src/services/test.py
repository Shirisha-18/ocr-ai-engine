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

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
REFERENCE_CSV = r"C:\Users\shiri\Dropbox\ocr_patents\patents_fyear_iyear.csv"
OUTPUT_CSV = rf"C:\Users\shiri\Dropbox\ocr_patents\info\patent_dates_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# =================================================
# HELPERS
# =================================================


def normalize_patnum(patnum):
    """Normalize patent numbers ONLY for matching"""
    return patnum.lstrip("0")


def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    return sorted(txt_files)[0] if txt_files else None


def split_date(date_str):
    if not date_str:
        return "", "", ""

    dt = datetime.strptime(date_str, "%m/%d/%Y")
    return str(dt.year), str(dt.month), str(dt.day)


def normalize_text(text):
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def fuzzy_contains(line, target, threshold=0.72):
    words = re.findall(r"[A-Za-z]{3,}", line.lower())
    for word in words:
        if SequenceMatcher(None, word, target).ratio() >= threshold:
            return True
    return False


def extract_patent_dates(text):
    text = normalize_text(text)
    lines = text.splitlines()

    combined_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        combined_lines.append(line)

        if i + 1 < len(lines):
            combined_lines.append(line + " " + lines[i + 1].strip())

    patent_date = ""
    filed_date = ""

    patent_patterns = [
        r"patented\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
        r"letters patent.*?dated\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
        r"dated\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
    ]

    filed_patterns = [
        r"application.*?filed\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
        r"application filed\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
        r"filed\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
        r"application\s+([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})",
    ]

    # =================================================
    # ORIGINAL WORKING LOGIC (UNCHANGED)
    # =================================================
    for line in combined_lines:
        if not patent_date:
            for pat in patent_patterns:
                m = re.search(pat, line, re.I)
                if m:
                    dt = parse(m.group(1))
                    if dt:
                        patent_date = dt.strftime("%m/%d/%Y")
                        break

        if not filed_date:
            for pat in filed_patterns:
                m = re.search(pat, line, re.I)
                if m:
                    dt = parse(m.group(1))
                    if dt:
                        filed_date = dt.strftime("%m/%d/%Y")
                        break

        if patent_date and filed_date:
            break

    # =================================================
    # GENERIC FUZZY RESCUE LAYER (ONLY IF MISSING)
    # =================================================
    if not patent_date or not filed_date:
        flexible_date = r"([A-Za-z]{3,9}\.?\s+\d{1,2}[,\.]?\s+\d{4})"

        for i, line in enumerate(lines):
            m = re.search(flexible_date, line, re.I)
            if not m:
                continue

            dt = parse(m.group(1))
            if not dt:
                continue

            formatted = dt.strftime("%m/%d/%Y")

            lower_line = line.lower()

            # --- Filed detection (fuzzy) ---
            if not filed_date:
                if (
                    fuzzy_contains(lower_line, "filed")
                    or fuzzy_contains(lower_line, "application")
                    or "[22]" in line
                ):
                    filed_date = formatted
                    continue

            # --- Patent detection (fuzzy) ---
            if not patent_date:
                if (
                    fuzzy_contains(lower_line, "patented")
                    or fuzzy_contains(lower_line, "issued")
                    or "[45]" in line
                ):
                    patent_date = formatted
                    continue

            # --- Positional fallback ---
            if not filed_date:
                filed_date = formatted
            elif not patent_date:
                patent_date = formatted

            if patent_date and filed_date:
                break

    # =================================================
    # SANITY CHECK
    # =================================================
    if patent_date and filed_date:
        if parse(filed_date) > parse(patent_date):
            filed_date = ""

    return patent_date, filed_date


def load_csv_dict(path):
    """Reference CSV keyed by normalized patent number"""
    data = {}

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = normalize_patnum(row["patnum"])
            data[key] = row

    return data


def compare_dates_with_flags(extracted_row, reference_row):
    # -------------------------
    # Missing patent entirely
    # -------------------------
    if not reference_row:
        return "Missing", "Missing", "Missing in Reference"

    # -------------------------
    # PATENT (ISSUE) DATE
    # -------------------------
    if not (
        reference_row.get("iyear")
        and reference_row.get("imonth")
        and reference_row.get("iday")
    ):
        patent_status = "Missing"
    else:
        patent_status = "No"
        if (
            extracted_row["iyear"] != reference_row["iyear"]
            or extracted_row["imonth"] != reference_row["imonth"]
            or extracted_row["iday"] != reference_row["iday"]
        ):
            patent_status = "Yes"

    # -------------------------
    # FILED (APPLICATION) DATE
    # -------------------------
    if not (
        reference_row.get("fyear")
        and reference_row.get("fmonth")
        and reference_row.get("fday")
    ):
        filed_status = "Missing"
    else:
        filed_status = "No"
        if (
            extracted_row["fyear"] != reference_row["fyear"]
            or extracted_row["fmonth"] != reference_row["fmonth"]
            or extracted_row["fday"] != reference_row["fday"]
        ):
            filed_status = "Yes"

    # -------------------------
    # OVERALL FLAG
    # -------------------------
    if "Yes" in (patent_status, filed_status):
        flag = "Wrong"
    elif "Missing" in (patent_status, filed_status):
        flag = "Missing"
    else:
        flag = "Correct"

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

        patent_date, filed_date = extract_patent_dates(text)
        pyear, pmonth, pday = split_date(patent_date)
        fyear, fmonth, fday = split_date(filed_date)

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

        print(
            f"[OK] {folder} | "
            f"Patent: {patent_date or 'N/A'} | "
            f"Filed: {filed_date or 'N/A'}"
        )

    reference_dict = load_csv_dict(REFERENCE_CSV)

    final_rows = []
    for row in extracted_rows:
        ref_row = reference_dict.get(normalize_patnum(row["patnum"]))
        pw, fw, flag = compare_dates_with_flags(row, ref_row)
        final_rows.append(
            {
                **row,
                "patent_wrong": pw,
                "filed_wrong": fw,
                "flag": flag,
            }
        )

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
