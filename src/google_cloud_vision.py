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
    mypath = "data/raw/"
    # Filter only images
    only_files = [
        f
        for f in listdir(mypath)
        if isfile(join(mypath, f)) and f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not only_files:
        print("[INFO] No image files found in data/raw/")
        return

    for image_file in only_files:
        image_path = join(mypath, image_file)
        try:
            text = detect_text(image_path)
            print("\n==============================")
            print(f"Image: {image_file}")
            print(text[:500])  # print first 500 characters
        except Exception as e:
            print(f"[ERROR] Failed to process {image_file}: {e}")


if __name__ == "__main__":
    main()
