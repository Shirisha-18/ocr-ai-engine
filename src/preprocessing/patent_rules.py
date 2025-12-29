import os
import re
from datetime import datetime

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"


def extract_header_text(folder):
    txt_files = [f for f in os.listdir(folder) if f.endswith("_text.txt")]
    if not txt_files:
        return ""
    txt_files.sort()
    with open(
        os.path.join(folder, txt_files[0]), "r", encoding="utf-8", errors="ignore"
    ) as f:
        lines = f.read().split("\n")[:30]  # header lines
    return "\n".join(lines)


def extract_patent_number(header):
    m = re.search(r"(?:Patent No\.?|No\.)\s*([\d,]+)", header)
    return m.group(1).replace(",", "") if m else ""


def extract_serial_number(header):
    m = re.search(
        r"(?:Serial|Application)\s*(?:No\.?|Number)?\s*[:#]?\s*([\d/,\-]{4,})", header
    )
    return m.group(1).strip() if m else ""


def extract_dates(header):
    app_date = ""
    pat_date = ""
    for m in re.finditer(
        r"(Application filed|Filed|Appl\. No\.)[:\s]*(\w+\.?\s\d{1,2},\s\d{4})", header
    ):
        app_date = m.group(2)
    for m in re.finditer(
        r"(Patented|Issued|Specification dated)[:\s]*(\w+\.?\s\d{1,2},\s\d{4})", header
    ):
        pat_date = m.group(2)
    return app_date, pat_date


def extract_inventor(header):
    m = re.search(r"Inventor[s]?:\s*([A-Za-z.,\s]+)", header)
    if m:
        return [name.strip() for name in m.group(1).split(",")]
    return []


def extract_assignee(header):
    m = re.search(r"Assignee[s]?:\s*([A-Za-z0-9.,\s]+)", header)
    if m:
        return [name.strip() for name in m.group(1).split(",")]
    return []


def extract_title(header):
    # Look for all caps lines, avoid noise
    blacklist = ["UNITED STATES PATENT", "PATENT", "ABSTRACT"]
    for line in header.split("\n"):
        line = line.strip()
        if len(line) > 3 and line.isupper() and not any(b in line for b in blacklist):
            return line
    return ""


def generate_silver_labels():
    data = []
    for folder in sorted(os.listdir(OCR_ROOT)):
        folder_path = os.path.join(OCR_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
        header = extract_header_text(folder_path)
        data.append(
            {
                "folder": folder,
                "header": header,
                "patent_number": extract_patent_number(header),
                "serial_number": extract_serial_number(header),
                "application_date": extract_dates(header)[0],
                "patent_date": extract_dates(header)[1],
                "inventors": extract_inventor(header),
                "assignees": extract_assignee(header),
                "title": extract_title(header),
            }
        )
    return data


if __name__ == "__main__":
    import json

    silver = generate_silver_labels()
    with open("../output/silver_labels.json", "w", encoding="utf-8") as f:
        json.dump(silver, f, indent=2)
    print("Silver labels saved!")
