# train_patent_ner.py
import re
import spacy
from spacy.tokens import DocBin
from spacy.training.example import Example
from pathlib import Path

# Custom labels
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

# Blank English model
nlp = spacy.blank("en")
ner = nlp.add_pipe("ner")
for label in CUSTOM_LABELS:
    ner.add_label(label)


# Function to safely map character offsets to spaCy tokens
def safe_entities(text, entities):
    doc = nlp.make_doc(text)
    valid_entities = []
    for start, end, label in entities:
        try:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is not None:
                valid_entities.append((span.start_char, span.end_char, span.label_))
        except:
            pass
    return valid_entities


def generate_training_example(text):
    entities = []

    # Patent numbers
    for m in re.finditer(
        r"(?:Patent No\.?|No\.|Appl\. No\.|Serial No\.):?\s*([\d,]+)",
        text,
        re.IGNORECASE,
    ):
        entities.append((m.start(1), m.end(1), "PATENT_NUMBER"))

    # Dates
    for m in re.finditer(
        r"(?:Patented|Issued|Specification dated|Mon\.?\s+\d{1,2},\s+\d{4}|Application filed|Filed):?\s*(Mon\.?\s+\d{1,2},\s+\d{4})?",
        text,
    ):
        label = (
            "PATENT_DATE"
            if "Patent" in m.group() or "Specification" in m.group()
            else "APPLICATION_DATE"
        )
        entities.append((m.start(), m.end(), label))

    # Inventor / Applicant / Assignee
    for match in re.finditer(
        r"(Inventor|Applicant|Assignee|Assignors?)[:\.]?\s*([A-Za-z.,\s]+)", text
    ):
        start, end = match.start(2), match.end(2)
        role = match.group(1).upper()
        if "INVENTOR" in role:
            entities.append((start, end, "INVENTOR"))
        elif "APPLICANT" in role:
            entities.append((start, end, "APPLICANT"))
        elif "ASSIGNEE" in role or "ASSIGNORS" in role:
            entities.append((start, end, "ASSIGNEE"))

    # Patent title heuristic
    for line in text.split("\n"):
        line_strip = line.strip()
        if len(line_strip) > 3 and line_strip.isupper() and "PATENT" not in line_strip:
            start = text.index(line_strip)
            entities.append((start, start + len(line_strip), "PATENT_TITLE"))
            break

    # Align entities safely
    entities = safe_entities(text, entities)
    return {"text": text, "entities": entities}


# Example training texts (replace with your OCR header dataset)
train_texts = [
    "HEADER\nName, City, State\nTITLE\nSpecification forming part of Letters Patent No. 1234567, dated January 1, 1900\nApplication filed January 1, 1899\nInventor: John Doe\nAssignee: Company X",
    "HEADER\nNo. 7654321 Patented March 3, 1920\nTitle\nApplicant: Jane Smith\nFiled: Feb. 1, 1919\n",
]

# Convert to DocBin
db = DocBin()
for text in train_texts:
    example_data = generate_training_example(text)
    doc = nlp.make_doc(example_data["text"])
    if example_data["entities"]:
        example = Example.from_dict(doc, {"entities": example_data["entities"]})
        db.add(example.reference)

Path("./train.spacy").write_bytes(db.to_bytes())
print("Training data saved to train.spacy")
