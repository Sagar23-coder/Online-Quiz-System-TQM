"""Utility to select the correct parser based on mime type.
"""
import os
from typing import Callable

from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .text_parser import parse_text
from .csv_parser import parse_csv
from .xlsx_parser import parse_xlsx
from .image_parser import parse_image

MIME_MAP = {
    "application/pdf": parse_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": parse_docx,
    "text/plain": parse_text,
    "text/csv": parse_csv,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": parse_xlsx,
    "image/png": parse_image,
    "image/jpeg": parse_image,
    "image/webp": parse_image,
}

def parse_file(path: str, mime: str) -> str:
    """Return raw extracted text for supported file types.
    Raises RuntimeError for unknown mime types.
    """
    parser: Callable[[str], str] = MIME_MAP.get(mime)
    if not parser:
        raise RuntimeError(f"Unsupported mime type: {mime}")
    return parser(path)
