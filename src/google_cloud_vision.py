import os
from google.cloud import vision
import xml.etree.ElementTree as ET
from my_timer import my_timer

# Set your Google Cloud Vision credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/vision_key.json"


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
    """Extracts page ranges from XML based on logic described."""
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

    # Rule:
    if abstract:
        return [abstract, claims]
    else:
        return [description, claims]


@my_timer
def main():
    source_root = r"C:\Users\shiri\Dropbox\ocr_patents\patent_images_sample\480"
    output_root = r"C:\Users\shiri\Dropbox\ocr_patents\ocr_patents\480"

    for folder in os.listdir(source_root):
        folder_path = os.path.join(source_root, folder)
        if not os.path.isdir(folder_path):
            continue

        print(f"\n📁 Processing folder: {folder}")

        # Find XML
        xml_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".xml")]
        if not xml_files:
            print("⚠ No XML file found — skipping folder.")
            continue

        xml_path = os.path.join(folder_path, xml_files[0])
        page_ranges = get_page_ranges(xml_path)

        # Create output folder
        out_folder = os.path.join(output_root, folder)
        os.makedirs(out_folder, exist_ok=True)

        for start, end in page_ranges:
            for page_num in range(start, end + 1):
                filename = f"{page_num:08d}.tif"
                image_path = os.path.join(folder_path, filename)

                if not os.path.exists(image_path):
                    print(f"⚠ Missing page: {filename}")
                    continue

                print(f"🔍 OCR Processing: {filename}")
                try:
                    text = detect_text(image_path)
                except Exception as e:
                    print(f"❌ Error OCR on {filename}: {e}")
                    continue

                # Save text file
                out_file = os.path.join(
                    out_folder, f"{os.path.splitext(filename)[0]}_text.txt"
                )
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(text)

                print(f"✅ Saved: {out_file}")

    print("\n🎉 Extraction completed successfully!")


if __name__ == "__main__":
    main()