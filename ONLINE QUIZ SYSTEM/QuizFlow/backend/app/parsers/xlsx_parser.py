"""XLSX parser – similar to CSV, uses pandas.read_excel.
"""
from typing import List

def parse_xlsx(file_path: str) -> str:
    try:
        import pandas as pd
    except Exception as e:
        raise RuntimeError("pandas not installed: " + str(e))
    df = pd.read_excel(file_path)
    lines: List[str] = []
    for _, row in df.iterrows():
        q = str(row.get('question') or '')
        lines.append(q)
        for opt in ['option_a','option_b','option_c','option_d']:
            opt_val = str(row.get(opt) or '')
            if opt_val:
                lines.append(f"{opt[-1].upper()}. {opt_val}")
        correct = str(row.get('correct_option') or '')
        if correct:
            lines.append(f"Correct Answer: {correct.upper()}")
        marks = row.get('marks')
        if not pd.isna(marks):
            lines.append(f"(Marks: {int(marks)})")
        expl = row.get('explanation')
        if expl and not pd.isna(expl):
            lines.append(f"Explanation: {expl}")
        lines.append('')
    return "\n".join(lines)
