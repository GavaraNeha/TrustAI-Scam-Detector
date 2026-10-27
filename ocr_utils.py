import os
from PIL import Image
import pytesseract

# Windows only: use the local install path if it exists.
# On Linux (Render/Docker), Tesseract is on PATH, so nothing is set.
_WIN_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == "nt" and os.path.exists(_WIN_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = _WIN_TESSERACT


def extract_text_from_image(file_storage):
    try:
        image = Image.open(file_storage)
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return ""
