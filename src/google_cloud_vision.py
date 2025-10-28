import os
import time
from google.cloud import vision
import xml.etree.ElementTree as ET
from tqdm import tqdm
from my_timer import my_timer

# Suppress gRPC debug messages
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"

# Set your Google Cloud Vision credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/vision_key.json"

# === Absolute paths to Dropbox folders ===
SOURCE_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\patent_images_sample\480"
OUTPUT_ROOT = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\480"
LOG_DIR = r"C:\Users\shiri\Dropbox\ocr_patents\processed"

os.makedirs(LOG_DIR, exist_ok=True)

# Log files
DETAILED_LOG = os.path.join(LOG_DIR, "detailed_log.txt")
SUMMARY_LOG = os.path.join(LOG_DIR, "summary_report.txt")


def detect_text(image_path):
    """Uses Google Cloud Vision OCR to extract text from an image."""
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    texts = response.text_annotations
    return texts[0].description if texts else ""


def get_page_ranges(xml_path):
    """Extracts page ranges from XML based on rules: skip drawings, choose abstract or description, then claims."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    def extract_range(tag):
        elem = root.find(f".//{tag}")
        if elem is not None:
            begin = elem.find("begin")
            end = elem.find("end")
            if begin is not None and end is not None:
                return (int(begin.text), int(end.text))
        return None

    abstract = extract_range("abstract-pages")
    claims = extract_range("claims-pages")
    description = extract_range("description-pages")
    drawings = extract_range("drawing-pages")

    ranges = []
    # Rule: abstract -> claims, else description -> claims
    if abstract:
        ranges.append(abstract)
    elif description:
        ranges.append(description)
    if claims:
        ranges.append(claims)

    # Skip drawings
    if drawings:
        ranges = [r for r in ranges if r != drawings]

    return ranges


@my_timer
def main():
    start_time = time.time()

    total_folders = 0
    total_pages_processed = 0
    total_skipped = 0
    total_failed = 0

    # Open detailed log file
    with open(DETAILED_LOG, "w", encoding="utf-8") as log_file:
        folders = [
            f
            for f in os.listdir(SOURCE_ROOT)
            if os.path.isdir(os.path.join(SOURCE_ROOT, f))
        ]

        for folder in tqdm(folders, desc="Processing Folders", unit="folder"):
            folder_path = os.path.join(SOURCE_ROOT, folder)
            xml_files = [
                f for f in os.listdir(folder_path) if f.lower().endswith(".xml")
            ]

            if not xml_files:
                total_skipped += 1
                log_file.write(f"[SKIPPED] Folder '{folder}' - no XML found\n")
                continue

            xml_path = os.path.join(folder_path, xml_files[0])
            page_ranges = get_page_ranges(xml_path)

            out_folder = os.path.join(OUTPUT_ROOT, folder)
            os.makedirs(out_folder, exist_ok=True)

            all_pages = [
                page for start, end in page_ranges for page in range(start, end + 1)
            ]

            for page_num in tqdm(all_pages, desc=f"{folder}", leave=False, unit="page"):
                filename = f"{page_num:08d}.tif"
                image_path = os.path.join(folder_path, filename)

                if not os.path.exists(image_path):
                    total_skipped += 1
                    log_file.write(f"[MISSING] {folder}/{filename}\n")
                    continue

                try:
                    text = detect_text(image_path)
                    total_pages_processed += 1
                except Exception as e:
                    total_failed += 1
                    log_file.write(f"[FAILED] {folder}/{filename} - {str(e)}\n")
                    continue

                out_file = os.path.join(
                    out_folder, f"{os.path.splitext(filename)[0]}_text.txt"
                )
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(text)

                log_file.write(f"[SUCCESS] {folder}/{filename} -> {out_file}\n")

            total_folders += 1

    # Summary
    elapsed = time.time() - start_time
    summary_lines = [
        "\nSUMMARY REPORT",
        "=" * 50,
        f"{'Folders Processed:':25} {total_folders:>10}",
        f"{'Pages Extracted:':25} {total_pages_processed:>10}",
        f"{'Pages Skipped:':25} {total_skipped:>10}",
        f"{'Pages Failed OCR:':25} {total_failed:>10}",
        "-" * 50,
        f"{'Total Time:':25} {elapsed:.2f} sec",
        "=" * 50,
        "\nExtraction Completed Successfully!\n",
    ]

    # Print summary in terminal
    print("\n".join(summary_lines))

    # Save summary report
    with open(SUMMARY_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))


if __name__ == "__main__":
    main()
