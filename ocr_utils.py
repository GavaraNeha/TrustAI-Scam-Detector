from PIL import Image
import pytesseract

# Windows only: point this at your actual Tesseract install if it's
# not on your PATH. Mac/Linux users installed via brew/apt usually
# don't need this line at all -- comment it out if so.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(file_storage):
    try:
        image = Image.open(file_storage)
        return pytesseract.image_to_string(image)
    except Exception:
        return ""
