import os
import spacy
import csv

OCR_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\random_sample"
OUTPUT_FILE = r"../output/final_patent_metadata.csv"

nlp = spacy.load("./patent_ner")

rows = []
for folder in sorted(os.listdir(OCR_ROOT)):
    folder_path = os.path.join(OCR_ROOT, folder)
    if not os.path.isdir(folder_path):
        continue
    txt_files = [f for f in os.listdir(folder_path) if f.endswith("_text.txt")]
    if not txt_files:
        continue
    txt_files.sort()
    with open(
        os.path.join(folder_path, txt_files[0]), "r", encoding="utf-8", errors="ignore"
    ) as f:
        text = f.read()

    doc = nlp(text)
    data = {
        "folder": folder,
        "first_page": txt_files[0],
        "patent_number": "",
        "serial_number": "",
        "application_date": "",
        "patent_date": "",
        "inventors": "",
        "assignees": "",
        "title": "",
    }

    for ent in doc.ents:
        if ent.label_ in data:
            if ent.label_ in ["INVENTOR", "ASSIGNEE"]:
                # Multiple values separated by comma
                if data[ent.label_]:
                    data[ent.label_] += ", " + ent.text
                else:
                    data[ent.label_] = ent.text
            else:
                data[ent.label_] = ent.text

    rows.append(data)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Extraction complete. CSV saved at {OUTPUT_FILE}")
