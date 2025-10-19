import os
from os import listdir
from os.path import isfile, join
from google.cloud import vision
from my_timer import my_timer  # works because both files are in src/


# Set your Google Cloud Vision credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/vision_key.json"


def detect_text(path):
    """Detect text in a single image using Google Cloud Vision API."""
    client = vision.ImageAnnotatorClient()
    with open(path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nFor more info: https://cloud.google.com/apis/design/errors"
        )

    return texts[0].description if texts else ""


@my_timer
def main():
    # Determine project root relative to this script
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("[DEBUG] Project root:", project_root)

    # Path to images
    mypath = join(project_root, "data", "raw")
    print("[DEBUG] Looking for images in:", mypath)

    # List all image files
    all_files = [
        f
        for f in listdir(mypath)
        if isfile(join(mypath, f))
        and f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff"))
    ]
    print("[DEBUG] Found files:", all_files)

    if not all_files:
        print("[INFO] No image files found in data/raw/")
        return

    # Show available images
    print("\nAvailable image files:")
    for i, f in enumerate(all_files, start=1):
        print(f"{i}. {f}")

    # Ask user which ones to process
    selected = input(
        "\nEnter image numbers to process (comma-separated, e.g. 1,3,5) or 'all': "
    ).strip()

    if selected.lower() == "all":
        chosen_files = all_files
    else:
        try:
            indices = [int(i.strip()) - 1 for i in selected.split(",")]
            chosen_files = [all_files[i] for i in indices if 0 <= i < len(all_files)]
        except ValueError:
            print("[ERROR] Invalid input format.")
            return

    if not chosen_files:
        print("[INFO] No valid files selected.")
        return

    # Process selected files
    for image_file in chosen_files:
        image_path = join(mypath, image_file)
        try:
            text = detect_text(image_path)
            print("\n==============================")
            print(f"Image: {image_file}")
            print(text[:500])  # print first 500 characters

            # Save text to file
            text_file = join(
                project_root,
                "data",
                "interim",
                f"{os.path.splitext(image_file)[0]}_text.txt",
            )
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[INFO] OCR text saved to {text_file}")

        except Exception as e:
            print(f"[ERROR] Failed to process {image_file}: {e}")


if __name__ == "__main__":
    main()
