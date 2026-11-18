"""Question extractor for raw text extracted from various documents.

The extractor looks for simple MCQ patterns:

    Q1. What is ...?
    A. Option A
    B. Option B
    C. Option C
    D. Option D
    Correct Answer: B
    (Marks: 2)
    Explanation: ...

It returns a list of dicts with keys:
- question_text
- option_a .. option_d
- correct_option (single uppercase letter)
- marks (int, default 1)
- explanation (optional)
- confidence (float 0‑1, based on how many parts were found)

The logic is tolerant – missing parts reduce confidence but the entry is still
included so the UI can let the teacher review and edit.
"""
import re
from typing import List, Dict

class QuestionExtractor:
    def __init__(self, raw_text: str):
        self.text = raw_text or ""

    def _split_questions(self) -> List[str]:
        # Split on blank lines separating question blocks.
        # Use two or more newlines as a separator.
        blocks = re.split(r"\n{2,}", self.text.strip())
        return [b.strip() for b in blocks if b.strip()]

    def _extract_from_block(self, block: str) -> Dict:
        # Initialize with defaults
        result = {
            "question_text": "",
            "option_a": "",
            "option_b": "",
            "option_c": "",
            "option_d": "",
            "correct_option": "",
            "marks": 1,
            "explanation": "",
            "confidence": 0.0,
        }
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        found = 0
        total = 6  # question, 4 options, correct answer
        for line in lines:
            # Question line – starts with Q or a number
            q_match = re.match(r"^(?:Q\d+\.?|\d+\.)\s*(.*)", line, re.I)
            if q_match and not result["question_text"]:
                result["question_text"] = q_match.group(1).strip()
                found += 1
                continue
            # Options A‑D (allow A., A) etc.
            opt_match = re.match(r"^(A|B|C|D)[\).:]\s*(.*)", line, re.I)
            if opt_match:
                opt = opt_match.group(1).lower()
                result[f"option_{opt}"] = opt_match.group(2).strip()
                found += 1
                continue
            # Correct answer line
            corr_match = re.search(r"Correct\s*Answer[:\s]+([ABCD])", line, re.I)
            if corr_match:
                result["correct_option"] = corr_match.group(1).upper()
                found += 1
                continue
            # Marks line – e.g., (Marks: 2) or Marks: 2
            marks_match = re.search(r"Marks?[:\s]+(\d+)", line, re.I)
            if marks_match:
                result["marks"] = int(marks_match.group(1))
                # marks not counted toward confidence
                continue
            # Explanation line – starts with Explanation:
            expl_match = re.match(r"Explanation[:\s]+(.*)", line, re.I)
            if expl_match:
                result["explanation"] = expl_match.group(1).strip()
                continue
        # Compute confidence as ratio of found mandatory parts
        result["confidence"] = round(found / total, 2) if total else 0.0
        return result

    def extract(self) -> List[Dict]:
        blocks = self._split_questions()
        extracted: List[Dict] = []
        for blk in blocks:
            item = self._extract_from_block(blk)
            # Only include if we have at least a question and one option
            if item["question_text"] and (item["option_a"] or item["option_b"]):
                extracted.append(item)
        return extracted
