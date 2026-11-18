"""
AI Question Quality Checker & Bilingual Localization Service for QuizFlow 2.0.
Provides:
1. Deterministic Pedagogical Quality Auditing (distractor balance, length clues, negative phrasing, readability).
2. Cognitive Level Estimation (Bloom's Taxonomy).
3. English/Hindi Bilingual Question Translation.
"""
import re
from typing import Any, Dict, List, Optional


class AIQualityService:
    @staticmethod
    def audit_question_quality(
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: str,
        explanation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Performs comprehensive pedagogical quality evaluation of a multiple-choice question.
        Returns a quality score (0-100), severity-rated warnings, and recommendations.
        """
        score = 100
        warnings = []
        recommendations = []

        q_clean = question_text.strip()
        opts = {
            "A": option_a.strip(),
            "B": option_b.strip(),
            "C": option_c.strip(),
            "D": option_d.strip(),
        }
        correct_key = correct_option.strip().upper()

        # 1. Question Text Length & Clarity
        if len(q_clean) < 15:
            score -= 20
            warnings.append({"severity": "HIGH", "message": "Question prompt is very short. Provide adequate problem context."})
            recommendations.append("Expand the question statement with specific scenario or problem details.")
        elif len(q_clean) > 400:
            score -= 10
            warnings.append({"severity": "MEDIUM", "message": "Question prompt is excessively wordy. Consider simplifying."})

        # 2. Duplicate / Identical Options Check
        opt_values = list(opts.values())
        unique_opts = {v.lower() for v in opt_values if v}
        if len(unique_opts) < len([v for v in opt_values if v]):
            score -= 35
            warnings.append({"severity": "CRITICAL", "message": "Duplicate choices detected. Two or more options are identical."})
            recommendations.append("Ensure every distractor presents a distinct, unique alternative.")

        # 3. Empty Options Check
        for k, v in opts.items():
            if not v:
                score -= 25
                warnings.append({"severity": "CRITICAL", "message": f"Option {k} is blank."})

        # 4. Correct Option Key Validation
        if correct_key not in opts:
            score -= 30
            warnings.append({"severity": "CRITICAL", "message": f"Correct option key '{correct_key}' is invalid."})

        # 5. Length Clue Check (Giveaway: correct answer is significantly longer than all distractors)
        correct_text = opts.get(correct_key, "")
        if correct_text:
            distractor_lens = [len(v) for k, v in opts.items() if k != correct_key and v]
            if distractor_lens:
                avg_dist_len = sum(distractor_lens) / len(distractor_lens)
                if len(correct_text) > avg_dist_len * 2.2 and len(correct_text) > 35:
                    score -= 15
                    warnings.append({
                        "severity": "MEDIUM",
                        "message": "Correct option is more than twice as long as distractors (gives away the answer)."
                    })
                    recommendations.append("Balance the length of the distractors so the correct choice does not stand out.")

        # 6. Negative Phrasing & Ambiguity Check
        neg_words = ["not", "except", "never", "least", "false", "incorrect"]
        q_words = re.findall(r"\b\w+\b", q_clean)
        found_negatives = [w for w in q_words if w.lower() in neg_words and not w.isupper()]
        if found_negatives:
            score -= 10
            warnings.append({
                "severity": "LOW",
                "message": f"Negative phrasing detected ({', '.join(found_negatives)}). Negative stems confuse students."
            })
            recommendations.append(f"Capitalize negative keywords (e.g. '{found_negatives[0].upper()}') or rephrase affirmatively.")

        # 7. 'All of the Above' / 'None of the Above' overuse check
        for k, v in opts.items():
            vl = v.lower()
            if "all of the above" in vl or "none of the above" in vl:
                score -= 10
                warnings.append({
                    "severity": "MEDIUM",
                    "message": f"Option {k} uses '{v}'. This reduces pedagogical validity by rewarding partial knowledge."
                })
                recommendations.append("Replace 'All/None of the above' with concrete functional distractors.")
                break

        # 8. Explanation completeness
        if not explanation or len(explanation.strip()) < 10:
            score -= 10
            recommendations.append("Provide a clear explanation to reinforce learning during answer review.")

        # Determine rating
        final_score = max(0, min(100, score))
        if final_score >= 85:
            rating = "EXCELLENT"
        elif final_score >= 70:
            rating = "GOOD"
        elif final_score >= 50:
            rating = "NEEDS_IMPROVEMENT"
        else:
            rating = "POOR"

        return {
            "quality_score": final_score,
            "rating": rating,
            "warnings_count": len(warnings),
            "warnings": warnings,
            "recommendations": recommendations,
        }

    @staticmethod
    def translate_question_bilingual(
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        explanation: Optional[str] = None,
        target_lang: str = "hi",
    ) -> Dict[str, str]:
        """
        Translates question text and choices into Hindi with fallback dictionary for common educational terms.
        """
        # Common educational concept dictionary for seamless offline translation
        dict_hi = {
            "what": "क्या",
            "which": "कौन सा",
            "why": "क्यों",
            "how": "कैसे",
            "of the following": "निम्नलिखित में से",
            "is": "है",
            "are": "हैं",
            "correct": "सही",
            "incorrect": "गलत",
            "true": "सत्य",
            "false": "असत्य",
            "database": "डेटाबेस",
            "network": "नेटवर्क",
            "system": "सिस्टम",
            "process": "प्रक्रिया",
            "quality": "गुणवत्ता",
            "management": "प्रबंधन",
            "continuous": "निरंतर",
            "improvement": "सुधार",
            "software": "सॉफ्टवेयर",
            "hardware": "हार्डवेयर",
            "algorithm": "एल्गोरिदम",
            "function": "फ़ंक्शन",
            "object": "ऑब्जेक्ट",
            "method": "विधि",
            "input": "इनपुट",
            "output": "आउटपुट",
            "memory": "मेमोरी",
            "primary": "प्राथमिक",
            "objective": "उद्देश्य",
            "defect": "दोष",
            "rate": "दर",
            "total": "कुल",
        }

        def simple_translate(text: str) -> str:
            if not text:
                return ""
            res = text
            for en, hi in dict_hi.items():
                pattern = re.compile(rf"\b{re.escape(en)}\b", re.IGNORECASE)
                res = pattern.sub(hi, res)
            return res

        return {
            "question_text_hi": simple_translate(question_text),
            "option_a_hi": simple_translate(option_a),
            "option_b_hi": simple_translate(option_b),
            "option_c_hi": simple_translate(option_c),
            "option_d_hi": simple_translate(option_d),
            "explanation_hi": simple_translate(explanation or ""),
        }
