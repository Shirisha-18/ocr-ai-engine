# extract_patent_entities.py
import os
import csv
from pathlib import Path
import spacy

# Paths
OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_CSV = r"C:\Users\shiri\Dropbox\ocr_patents\info\metadata_summary_custom_ner.csv"
OUTPUT_JSON_FOLDER = r"C:\Users\shiri\Dropbox\ocr_patents\info\patent_jsons"

os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)

# Load trained model
nlp = spacy.load("./output/model-best")

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

        with open(
            os.path.join(folder_path, first_page),
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as file:
            text = file.read()

        # NER inference
        doc = nlp(text)
        row = {"folder": folder, "first_page": first_page}
        entities_dict = {label: [] for label in CUSTOM_LABELS}

        for ent in doc.ents:
            if ent.label_ in entities_dict:
                entities_dict[ent.label_].append(ent.text)

        for label in CUSTOM_LABELS:
            row[label] = "; ".join(entities_dict[label])

        writer.writerow(row)

        # Save per-patent JSON for verification (filename = patent number)
        patent_number = (
            entities_dict["PATENT_NUMBER"][0]
            if entities_dict["PATENT_NUMBER"]
            else folder
        )
        import json

        with open(
            os.path.join(OUTPUT_JSON_FOLDER, f"{patent_number}.json"),
            "w",
            encoding="utf-8",
        ) as jf:
            json.dump(
                {"folder": folder, "first_page": first_page, **entities_dict},
                jf,
                indent=2,
            )

        print(f"[OK] {folder} → {first_page}")
