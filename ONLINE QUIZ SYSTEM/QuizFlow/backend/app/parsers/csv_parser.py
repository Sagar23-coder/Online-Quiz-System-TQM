"""CSV parser – expects columns: question, option_a, option_b, option_c, option_d, correct_option, marks?, explanation?
"""
from typing import List, Dict

def parse_csv(file_path: str) -> str:
    try:
        import pandas as pd
    except Exception as e:
        raise RuntimeError("pandas not installed: " + str(e))
    df = pd.read_csv(file_path)
    # Convert to a simple MCQ text format that the existing extractor can understand
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
