"""DOCX parser using python-docx.
"""
from typing import List

def parse_docx(file_path: str) -> str:
    try:
        import docx
    except Exception as e:
        raise RuntimeError("python-docx not installed: " + str(e))
    doc = docx.Document(file_path)
    paragraphs: List[str] = []
    for para in doc.paragraphs:
        paragraphs.append(para.text)
    # Include tables as plain text rows
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text for cell in row.cells]
            paragraphs.append(" | ".join(cells))
    return "\n".join(paragraphs)
