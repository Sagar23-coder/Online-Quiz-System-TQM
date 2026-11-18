"""Image parser – runs pytesseract OCR on image files.
"""
from typing import List

def parse_image(file_path: str) -> str:
    try:
        from PIL import Image
        import pytesseract
    except Exception as e:
        raise RuntimeError("Pillow or pytesseract not installed: " + str(e))
    img = Image.open(file_path)
    # Simple preprocessing – convert to grayscale and increase contrast could be added
    return pytesseract.image_to_string(img)
