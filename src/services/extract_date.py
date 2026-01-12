import os
import csv
from datetime import datetime
import spacy
from date_spacy import find_dates

# =================================================
# CONFIG
# =================================================
OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = rf"C:\Users\shiri\Dropbox\ocr_patents\info\patent_dates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# =================================================
# spaCy pipeline (NO ML, date-only)
# =================================================
nlp = spacy.blank("en")
nlp.add_pipe("find_dates")


# =================================================
# Helpers
# =================================================
def get_first_text_file(folder_path):
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        return None
    return sorted(txt_files)[0]


def extract_dates_spacy(text):
    """
    Extract patent date and application/filed date using spaCy context.
    Returns:
        patent_date (MM/DD/YYYY or "")
        filed_date  (MM/DD/YYYY or "")
    """
    doc = nlp(text)

    patent_date = None
    filed_date = None

    for ent in doc.ents:
        if ent.label_ != "DATE" or not ent._.date:
            continue

        sent_text = ent.sent.text.lower()
        parsed_date = ent._.date.strftime("%m/%d/%Y")

        # Patent date anchors (1832 → present)
        if patent_date is None and any(
            kw in sent_text for kw in ["dated", "patented", "letters patent"]
        ):
            patent_date = parsed_date

        # Application / Filed date anchors (appear later historically)
        elif filed_date is None and any(
            kw in sent_text for kw in ["application", "filed", "applied"]
        ):
            filed_date = parsed_date

    return patent_date or "", filed_date or ""


# =================================================
# Main runner
# =================================================
def run_date_extraction():
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

        patent_date, filed_date = extract_dates_spacy(text)

        rows.append(
            {
                "folder_or_patent_number": folder,
                "patent_date": patent_date,
                "filed_date": filed_date,
            }
        )

        print(
            f"[OK] {folder} → "
            f"Patent: {patent_date or 'N/A'} | "
            f"Filed: {filed_date or 'N/A'}"
        )

    # =================================================
    # Save CSV
    # =================================================
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "patent_number",
                "patent_date",
                "filed_date",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved CSV to:\n{OUTPUT_FILE}\n")


# =================================================
# Entry point
# =================================================
if __name__ == "__main__":
    run_date_extraction()
