"""
Universal Document Text Extractor for QuizFlow.
Robustly extracts clean readable text from ANY document format:
- PowerPoint (.pptx, .ppt)
- PDF (.pdf)
- Word (.docx)
- Excel (.xlsx, .xls)
- Plain Text & Notes (.txt, .md, .rtf, .html, .xml, .json, .csv)
- Pure Python fallback for binary files without external system dependencies.
"""
import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional


class DocumentExtractor:
    @classmethod
    def extract_text_from_file(cls, file_path: str) -> str:
        """Extract all text from any given file path based on its extension and content."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext in (".pptx", ".ppsx"):
                return cls.extract_from_pptx(file_path)
            elif ext == ".ppt":
                return cls.extract_from_legacy_ppt(file_path)
            elif ext in (".docx", ".dotx"):
                return cls.extract_from_docx(file_path)
            elif ext == ".pdf":
                return cls.extract_from_pdf(file_path)
            elif ext in (".xlsx", ".xlsm"):
                return cls.extract_from_xlsx(file_path)
            elif ext in (".csv", ".tsv"):
                return cls.extract_from_csv(file_path)
            elif ext in (".txt", ".md", ".json", ".rtf", ".html", ".htm", ".xml", ".log", ".ini", ".cfg"):
                return cls.extract_from_text_file(file_path)
            else:
                # Try zip first (many office formats are zip), then text, then binary strings fallback
                if zipfile.is_zipfile(file_path):
                    try:
                        return cls.extract_from_docx(file_path)
                    except Exception:
                        try:
                            return cls.extract_from_pptx(file_path)
                        except Exception:
                            pass
                return cls.extract_from_text_file(file_path)
        except Exception:
            # Ultimate resilient fallback: extract printable character sequences from binary
            return cls.extract_printable_strings(file_path)

    @classmethod
    def extract_from_pptx(cls, file_path: str) -> str:
        """Extract text from all slides and slide notes in a PowerPoint .pptx presentation."""
        # Try python-pptx if installed
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            text_runs = []
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_texts = [f"--- Slide {slide_num} ---"]
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            line = "".join(run.text for run in paragraph.runs).strip()
                            if line:
                                slide_texts.append(line)
                # Check for notes
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    if notes:
                        slide_texts.append(f"[Notes: {notes}]")
                text_runs.append("\n".join(slide_texts))
            if text_runs:
                return "\n\n".join(text_runs)
        except Exception:
            pass

        # Zero-dependency OpenXML extraction for PPTX
        text_lines = []
        with zipfile.ZipFile(file_path, "r") as z:
            # Find all slide xml files
            slide_names = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml", n)]
            # Sort naturally by slide number
            slide_names.sort(key=lambda s: int(re.search(r"\d+", s).group(0)) if re.search(r"\d+", s) else 0)

            for idx, s_name in enumerate(slide_names, 1):
                try:
                    xml_content = z.read(s_name)
                    tree = ET.fromstring(xml_content)
                    slide_runs = [f"--- Slide {idx} ---"]
                    # PPTX text runs use tag <a:t>
                    for elem in tree.iter():
                        if elem.tag.endswith("}t") or elem.tag == "t":
                            if elem.text and elem.text.strip():
                                slide_runs.append(elem.text.strip())
                    text_lines.append("\n".join(slide_runs))
                except Exception:
                    continue

        if text_lines:
            return "\n\n".join(text_lines)
        return cls.extract_printable_strings(file_path)

    @classmethod
    def extract_from_legacy_ppt(cls, file_path: str) -> str:
        """Extract printable text blocks from legacy binary PPT file."""
        return cls.extract_printable_strings(file_path)

    @classmethod
    def extract_from_docx(cls, file_path: str) -> str:
        """Extract text from Word .docx file with zero external dependencies."""
        # Try python-docx if installed
        try:
            import docx
            doc = docx.Document(file_path)
            lines = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_txt = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                    if row_txt:
                        lines.append(row_txt)
            if lines:
                return "\n".join(lines)
        except Exception:
            pass

        # Pure Python OpenXML extraction
        with zipfile.ZipFile(file_path, "r") as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            paragraphs = []
            for p in tree.iter():
                if p.tag.endswith("}p") or p.tag == "p":
                    p_text = "".join(
                        elem.text for elem in p.iter()
                        if (elem.tag.endswith("}t") or elem.tag == "t") and elem.text
                    ).strip()
                    if p_text:
                        paragraphs.append(p_text)
            return "\n\n".join(paragraphs)

    @classmethod
    def extract_from_pdf(cls, file_path: str) -> str:
        """Extract text from PDF using pypdf/pdfplumber if available, or native PDF stream decoding."""
        # 1. Try pypdf / pypdf2 / pdfplumber
        for mod_name in ("pypdf", "pypdf2", "pdfplumber"):
            try:
                if mod_name == "pdfplumber":
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        txt = "\n".join(page.extract_text() or "" for page in pdf.pages)
                        if txt.strip():
                            return txt
                else:
                    mod = __import__(mod_name)
                    reader = mod.PdfReader(file_path)
                    pages_text = [page.extract_text() or "" for page in reader.pages]
                    txt = "\n".join(pages_text).strip()
                    if txt:
                        return txt
            except Exception:
                continue

        # 2. Native Pure-Python PDF stream decompressor
        try:
            import zlib
            with open(file_path, "rb") as f:
                content = f.read()

            extracted_chunks = []
            # Find flate-decoded streams: stream\r?\n ... endstream
            stream_regex = re.compile(rb"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
            for match in stream_regex.finditer(content):
                data = match.group(1)
                decompressed = None
                try:
                    decompressed = zlib.decompress(data)
                except Exception:
                    try:
                        decompressed = zlib.decompress(data, -15)
                    except Exception:
                        pass

                if decompressed:
                    # Look for text inside parenthesis (Text) Tj or [ (Text1) (Text2) ] TJ
                    tj_matches = re.findall(rb"\((.*?)\)\s*Tj", decompressed)
                    for tj in tj_matches:
                        try:
                            s = tj.decode("utf-8", errors="ignore").strip()
                            if s:
                                extracted_chunks.append(s)
                        except Exception:
                            pass
                    # Also TJ array format
                    tj_array_matches = re.findall(rb"\[(.*?)\]\s*TJ", decompressed, re.DOTALL)
                    for arr in tj_array_matches:
                        inner_texts = re.findall(rb"\((.*?)\)", arr)
                        combined = "".join(t.decode("utf-8", errors="ignore") for t in inner_texts).strip()
                        if combined:
                            extracted_chunks.append(combined)

            if extracted_chunks:
                # Group text into reasonable paragraphs
                joined = " ".join(extracted_chunks)
                # Split at Q1., 1., etc. or newlines
                clean_lines = re.sub(r"(\bQ\d+[\.:\)]|\b\d+[\.:\)])", r"\n\1", joined)
                return clean_lines
        except Exception:
            pass

        # 3. Fallback: string scanning
        return cls.extract_printable_strings(file_path)

    @classmethod
    def extract_from_xlsx(cls, file_path: str) -> str:
        """Extract text and tabular data from Excel spreadsheets."""
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            lines = []
            for sheet_name in excel_file.sheet_names:
                df = excel_file.parse(sheet_name)
                lines.append(f"--- Sheet: {sheet_name} ---")
                lines.append(df.to_string(index=False))
            return "\n\n".join(lines)
        except Exception:
            pass

        # OpenXML sharedStrings extraction
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                if "xl/sharedStrings.xml" in z.namelist():
                    tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                    strings = [
                        elem.text.strip() for elem in tree.iter()
                        if elem.tag.endswith("}t") and elem.text and elem.text.strip()
                    ]
                    if strings:
                        return "\n".join(strings)
        except Exception:
            pass

        return cls.extract_printable_strings(file_path)

    @classmethod
    def extract_from_csv(cls, file_path: str) -> str:
        """Extract text from CSV/TSV file."""
        return cls.extract_from_text_file(file_path)

    @classmethod
    def extract_from_text_file(cls, file_path: str) -> str:
        """Read standard text file with multiple encoding fallbacks."""
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"):
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    @classmethod
    def extract_printable_strings(cls, file_path: str, min_length: int = 4) -> str:
        """Resilient fallback: extracts readable ASCII/Unicode character sequences from any binary file."""
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            # Match continuous readable text sequences
            pattern = re.compile(rb"[\x20-\x7E\t\r\n]{%d,}" % min_length)
            matches = pattern.findall(data)
            lines = []
            for m in matches:
                try:
                    s = m.decode("ascii", errors="ignore").strip()
                    if s and len(s) >= min_length and not s.startswith("<?xml") and not s.startswith("<w:"):
                        lines.append(s)
                except Exception:
                    pass
            return "\n".join(lines)
        except Exception as e:
            return f"Notice: Extracted content from {os.path.basename(file_path)}"
