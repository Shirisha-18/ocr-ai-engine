import os
from google.cloud import vision
from contextlib import redirect_stderr
from io import StringIO

# Suppress gRPC debug messages
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"

# Set Google Cloud Vision credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/vision_key.json"

# === Test paths ===
SOURCE_ROOT = r"data/raw"  # Folder containing selected test files
OUTPUT_ROOT = r"data/interim"  # Folder where extracted text files will be saved

os.makedirs(OUTPUT_ROOT, exist_ok=True)


def detect_text(image_path):
    """Uses Google Cloud Vision OCR to extract text from an image, suppressing gRPC warnings."""
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    # Suppress gRPC warnings
    f = StringIO()
    with redirect_stderr(f):
        response = client.text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    texts = response.text_annotations
    return texts[0].description if texts else ""


def main():
    # Specify selected folders or files for testing
    selected_folders = [
        "patent1",
        "patent2",
    ]  # Replace with actual folder names in data/raw

    for folder in selected_folders:
        folder_path = os.path.join(SOURCE_ROOT, folder)
        if not os.path.exists(folder_path):
            continue

        # Get all image files in the folder (e.g., .tif)
        image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".tif")]
        if not image_files:
            continue

        # Create output folder for this patent
        out_folder = os.path.join(OUTPUT_ROOT, folder)
        os.makedirs(out_folder, exist_ok=True)

        for filename in image_files:
            image_path = os.path.join(folder_path, filename)
            try:
                text = detect_text(image_path)
            except Exception:
                continue  # Skip failures silently

            out_file = os.path.join(
                out_folder, f"{os.path.splitext(filename)[0]}_text.txt"
            )
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text)


if __name__ == "__main__":
    main()
