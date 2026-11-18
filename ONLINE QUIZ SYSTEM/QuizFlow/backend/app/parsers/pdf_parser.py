"""PDF parser using pdfplumber with OCR fallback.
"""
import os, io, secrets
import pdfplumber
from typing import List

def _ocr_fallback(file_path: str) -> str:
    """Run pytesseract on each page image as a fallback for scanned PDFs.
    Requires Tesseract OCR installed on the system.
    """
    try:
        from PIL import Image
        import pytesseract
    except Exception as e:
        raise RuntimeError("OCR dependencies not installed: " + str(e))
    text_pages: List[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # Render page to image
            img = page.to_image(resolution=150).original
            txt = pytesseract.image_to_string(img)
            text_pages.append(txt)
    return "\n".join(text_pages)

def parse_pdf(file_path: str) -> str:
    """Extract raw text from a PDF.
    For searchable PDFs we use pdfplumber; for scanned PDFs we fall back to OCR.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if not all_text.strip():
            # Possibly scanned – use OCR
            all_text = _ocr_fallback(file_path)
        return all_text
    except Exception as exc:
        raise RuntimeError(f"Failed to parse PDF {file_path}: {exc}")
