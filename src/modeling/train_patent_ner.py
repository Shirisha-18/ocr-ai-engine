import spacy
from spacy.tokens import DocBin
import json
from pathlib import Path

LABELS = [
    "PATENT_NUMBER",
    "SERIAL_NUMBER",
    "APPLICATION_DATE",
    "PATENT_DATE",
    "INVENTOR",
    "ASSIGNEE",
    "PATENT_TITLE",
]

nlp = spacy.blank("en")
ner = nlp.add_pipe("ner")
for label in LABELS:
    ner.add_label(label)

# Load silver labels
with open("../output/silver_labels.json", "r", encoding="utf-8") as f:
    silver_data = json.load(f)


def create_entities(text, item):
    entities = []

    # helper to add spans
    def add_entity(start, end, label):
        if start < end:
            entities.append((start, end, label))

    for label, key in [
        ("PATENT_NUMBER", "patent_number"),
        ("SERIAL_NUMBER", "serial_number"),
        ("APPLICATION_DATE", "application_date"),
        ("PATENT_DATE", "patent_date"),
        ("PATENT_TITLE", "title"),
    ]:
        if item[key]:
            start = text.find(item[key])
            if start != -1:
                add_entity(start, start + len(item[key]), label)
    # Inventors
    for inv in item["inventors"]:
        start = text.find(inv)
        if start != -1:
            add_entity(start, start + len(inv), "INVENTOR")
    # Assignees
    for ass in item["assignees"]:
        start = text.find(ass)
        if start != -1:
            add_entity(start, start + len(ass), "ASSIGNEE")
    return entities


db = DocBin()
for item in silver_data:
    text = item["header"]
    entities = create_entities(text, item)
    if entities:
        doc = nlp.make_doc(text)
        doc_bin_example = {"entities": entities}
        from spacy.training.example import Example

        example = Example.from_dict(doc, doc_bin_example)
        db.add(example.reference)

Path("./train.spacy").write_bytes(db.to_bytes())
print("Training data saved to train.spacy")

# Training loop
from spacy.util import minibatch, compounding

nlp.begin_training()
for i in range(30):
    losses = {}
    batches = minibatch(list(db.get_docs(nlp.vocab)), size=compounding(4.0, 32.0, 1.5))
    for batch in batches:
        nlp.update(batch, sgd=nlp.optimizer, losses=losses)
    print(f"Epoch {i + 1}, Losses: {losses}")

nlp.to_disk("./patent_ner")
print("Custom SpaCy NER model saved at ./patent_ner")
