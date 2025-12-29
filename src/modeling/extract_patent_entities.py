# extract_patent_entities.py
import os
import csv
import json
import spacy

# Paths
OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_CSV = r"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_custom_ner.csv"
OUTPUT_JSON_FOLDER = r"C:\Users\shiri\Dropbox\ocr_patents\info\patent_jsons"

os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)

# Load trained model
nlp = spacy.load(
    r"C:\Users\shiri\OneDrive\Documents\Python\llm-projects\ocr-ai-engine\src\modeling\output\model-best"
)

CUSTOM_LABELS = [
    "PATENT_NUMBER",
    "SERIAL_NUMBER",
    "APPLICATION_DATE",
    "PATENT_DATE",
    "PATENT_TITLE",
    "INVENTOR",
    "ASSIGNEE",
    "APPLICANT",
]

fieldnames = ["folder", "first_page"] + CUSTOM_LABELS

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for folder in sorted(os.listdir(OCR_ROOT)):
        folder_path = os.path.join(OCR_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue

        txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
        if not txt_files:
            continue
        first_page = sorted(txt_files)[0]

        # Read first page
        with open(
            os.path.join(folder_path, first_page),
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as file:
            text = file.read()

        # Run NER
        doc = nlp(text)
        entities_dict = {label: [] for label in CUSTOM_LABELS}
        for ent in doc.ents:
            if ent.label_ in entities_dict:
                entities_dict[ent.label_].append(ent.text)

        # Prepare row for CSV
        row = {"folder": folder, "first_page": first_page}
        for label in CUSTOM_LABELS:
            row[label] = "; ".join(entities_dict[label])
        writer.writerow(row)

        # Save per-patent JSON (filename = folder = patent number)
        json_path = os.path.join(OUTPUT_JSON_FOLDER, f"{folder}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(
                {"folder": folder, "first_page": first_page, **entities_dict},
                jf,
                indent=2,
            )

        print(f"[OK] {folder} → {first_page}")
