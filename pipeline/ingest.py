"""
Turns whatever the user submitted (typed text and/or a screenshot)
into one clean text string, and pulls out any URLs mentioned so
url_intel can check them.
"""
import re
from ocr_utils import extract_text_from_image

URL_RE = re.compile(r"https?://\S+")


def build_text(message, screenshot_file):
    text = (message or "").strip()

    if screenshot_file and screenshot_file.filename:
        ocr_text = extract_text_from_image(screenshot_file)
        text = (text + "\n" + ocr_text).strip()

    return text


def extract_urls(text):
    return list(dict.fromkeys(URL_RE.findall(text)))  # de-duplicated, order preserved
