"""
AI Quiz & Question Generator Service for QuizFlow / TeachWise.
Supports dual-engine generation:
1. Cloud LLM generation (Google Gemini / OpenAI) when API keys are configured.
2. Local pedagogical rule-based / template generation (100% offline, zero-cost fallback).
Supports file import from CSV, JSON, TXT, and Markdown notes.
"""
import csv
import io
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.quiz import Quiz
from app.models.question import Question
from app.database.init_db import _generate_join_code

logger = logging.getLogger("quizflow.ai_generator")


# Rich Curated Domain Knowledge Base for Local Intelligent Fallback
KNOWLEDGE_BANK = {
    "python": [
        {
            "question_text": "In Python, which of the following statements correctly describes how arguments are passed to functions?",
            "option_a": "Arguments are passed strictly by value (deep copies are created).",
            "option_b": "Arguments are passed by object reference (call-by-sharing).",
            "option_c": "Arguments are passed strictly by pointer reference like C++.",
            "option_d": "Immutable types are passed by reference and mutable types by value.",
            "correct_option": "B",
            "explanation": "Python passes arguments by assignment, commonly known as 'call-by-object-reference'. The function receives a reference to the existing object in memory.",
            "topic": "Python Functions",
            "difficulty": "medium",
            "learning_objective": "Understand parameter passing semantics in Python",
        },
        {
            "question_text": "What is the time complexity of searching for an element in a Python dictionary by key on average?",
            "option_a": "O(1) Constant Time",
            "option_b": "O(n) Linear Time",
            "option_c": "O(log n) Logarithmic Time",
            "option_d": "O(n log n) Linearithmic Time",
            "correct_option": "A",
            "explanation": "Python dictionaries are implemented as hash tables with open addressing, yielding an average time complexity of O(1) for key lookups.",
            "topic": "Data Structures",
            "difficulty": "easy",
            "learning_objective": "Analyze dictionary performance characteristics",
        },
        {
            "question_text": "Which built-in Python function returns an iterator of tuples containing the index and item from an iterable?",
            "option_a": "zip()",
            "option_b": "range()",
            "option_c": "enumerate()",
            "option_d": "map()",
            "correct_option": "C",
            "explanation": "enumerate(iterable, start=0) adds a counter to an iterable and yields pairs of (index, item).",
            "topic": "Python Basics",
            "difficulty": "easy",
            "learning_objective": "Utilize built-in sequence iteration tools",
        },
        {
            "question_text": "What will happen if you modify a default mutable argument (e.g., def fn(lst=[])) across multiple calls?",
            "option_a": "A new empty list is created on every function invocation.",
            "option_b": "The default list is evaluated once at definition time and shared across subsequent calls.",
            "option_c": "Python raises a MutableDefaultArgumentException at runtime.",
            "option_d": "The list is automatically frozen into an immutable tuple.",
            "correct_option": "B",
            "explanation": "Default parameter values in Python are evaluated once when the function definition is executed, so mutable defaults persist mutations across calls.",
            "topic": "Python Scope & Functions",
            "difficulty": "hard",
            "learning_objective": "Avoid common Python pitfalls with mutable default arguments",
        },
        {
            "question_text": "Which module in Python's standard library provides decorators for creating immutable data classes and value objects?",
            "option_a": "collections.namedtuple",
            "option_b": "dataclasses",
            "option_c": "typing.TypedDict",
            "option_d": "functools.lru_cache",
            "correct_option": "B",
            "explanation": "The 'dataclasses' module (introduced in Python 3.7) provides the @dataclass decorator, which can also specify frozen=True for immutability.",
            "topic": "Object Oriented Python",
            "difficulty": "medium",
            "learning_objective": "Model structured data using Python dataclasses",
        },
    ],
    "database": [
        {
            "question_text": "Which SQL constraint ensures that all values in a specific column are unique and non-null?",
            "option_a": "UNIQUE KEY",
            "option_b": "PRIMARY KEY",
            "option_c": "FOREIGN KEY",
            "option_d": "CHECK CONSTRAINT",
            "correct_option": "B",
            "explanation": "A PRIMARY KEY uniquely identifies each record in a database table. It must contain unique values and cannot contain NULL values.",
            "topic": "Relational Databases",
            "difficulty": "easy",
            "learning_objective": "Define primary database constraints",
        },
        {
            "question_text": "In relational database design, what is the primary goal of Third Normal Form (3NF)?",
            "option_a": "Eliminate repeating groups and non-atomic values.",
            "option_b": "Remove partial functional dependencies on a composite primary key.",
            "option_c": "Eliminate transitive functional dependencies on non-prime attributes.",
            "option_d": "Denormalize data to maximize query throughput.",
            "correct_option": "C",
            "explanation": "A relation is in 3NF if it is in 2NF and every non-trivial functional dependency X -> A has X as a superkey or A as part of a candidate key (no transitive dependencies).",
            "topic": "Database Normalization",
            "difficulty": "hard",
            "learning_objective": "Understand database normalization principles",
        },
        {
            "question_text": "What does the 'I' stand for in the database ACID transaction properties?",
            "option_a": "Indexed",
            "option_b": "Isolation",
            "option_c": "Integrity",
            "option_d": "Idempotency",
            "correct_option": "B",
            "explanation": "ACID stands for Atomicity, Consistency, Isolation, and Durability. Isolation ensures concurrent transactions execute without interfering with one another.",
            "topic": "Database Transactions",
            "difficulty": "medium",
            "learning_objective": "Explain transactional ACID properties",
        },
    ],
    "oop": [
        {
            "question_text": "Which object-oriented principle refers to exposing only essential features while concealing internal implementation details?",
            "option_a": "Encapsulation / Abstraction",
            "option_b": "Polymorphism",
            "option_c": "Inheritance",
            "option_d": "Dynamic Binding",
            "correct_option": "A",
            "explanation": "Abstraction hides complexity and internal details, exposing a clean interface. Encapsulation bundles state and methods while restricting direct access to components.",
            "topic": "OOP Principles",
            "difficulty": "easy",
            "learning_objective": "Distinguish fundamental OOP pillars",
        },
        {
            "question_text": "What is the primary purpose of Polymorphism in software design?",
            "option_a": "To allow objects of different classes to respond to the same interface or method call.",
            "option_b": "To ensure variables cannot be reassigned after initialization.",
            "option_c": "To combine multiple unrelated classes into a monolithic module.",
            "option_d": "To force all subclasses to inherit private member variables.",
            "correct_option": "A",
            "explanation": "Polymorphism enables treating objects of different derived classes uniformly through a common base interface.",
            "topic": "Polymorphism",
            "difficulty": "medium",
            "learning_objective": "Apply polymorphic interfaces in class hierarchies",
        },
    ],
    "science": [
        {
            "question_text": "What primary organelle in eukaryotic cells is responsible for generating the majority of cellular ATP via cellular respiration?",
            "option_a": "Endoplasmic Reticulum",
            "option_b": "Mitochondria",
            "option_c": "Golgi Apparatus",
            "option_d": "Ribosome",
            "correct_option": "B",
            "explanation": "Mitochondria are often called the powerhouses of the cell because they produce adenosine triphosphate (ATP) through oxidative phosphorylation.",
            "topic": "Cell Biology",
            "difficulty": "easy",
            "learning_objective": "Identify eukaryotic organelle functions",
        },
        {
            "question_text": "According to Newton's Second Law of Motion, what is the mathematical relationship between net Force (F), mass (m), and acceleration (a)?",
            "option_a": "F = m / a",
            "option_b": "F = m * a",
            "option_c": "F = a / m",
            "option_d": "F = 0.5 * m * a^2",
            "correct_option": "B",
            "explanation": "Newton's second law states that the acceleration of an object is directly proportional to net force and inversely proportional to its mass: F = ma.",
            "topic": "Classical Mechanics",
            "difficulty": "easy",
            "learning_objective": "State and apply Newton's second law of motion",
        },
    ],
}


class AIGeneratorService:
    """Service that coordinates AI generation and file parsing for assessment quizzes."""

    @classmethod
    def generate_quiz_from_prompt(
        cls,
        prompt: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        topic: Optional[str] = None,
        subject: Optional[str] = "General",
    ) -> Dict[str, Any]:
        """
        Generate complete quiz title, description, time limit, and questions.
        Tries Cloud LLM first if configured; falls back reliably to local pedagogical engine.
        """
        clean_prompt = prompt.strip()
        num_questions = max(1, min(20, num_questions))
        diff_clean = difficulty.lower() if difficulty in ("easy", "medium", "hard") else "medium"

        # 1. Attempt Cloud LLM if API Key is configured
        llm_result = cls._try_llm_generation(clean_prompt, num_questions, diff_clean, topic)
        if llm_result:
            return llm_result

        # 2. Local Intelligent Pedagogical Fallback Engine
        return cls._generate_local_quiz(clean_prompt, num_questions, diff_clean, topic, subject)

    @classmethod
    def _try_llm_generation(
        cls,
        prompt: str,
        num_questions: int,
        difficulty: str,
        topic: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Attempt generating via Google Gemini or OpenAI if API key exists."""
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")

        if gemini_key:
            try:
                return cls._call_gemini_api(gemini_key, prompt, num_questions, difficulty, topic)
            except Exception as e:
                logger.warning("Gemini generation notice: %s. Falling back to local engine.", e)

        if openai_key:
            try:
                return cls._call_openai_api(openai_key, prompt, num_questions, difficulty, topic)
            except Exception as e:
                logger.warning("OpenAI generation notice: %s. Falling back to local engine.", e)

        return None

    @classmethod
    def _call_gemini_api(
        cls, api_key: str, prompt: str, num_questions: int, difficulty: str, topic: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini generateContent endpoint with JSON output mode."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        sys_instructions = (
            f"You are a professional educational assessment author. Generate a high-quality quiz with {num_questions} "
            f"multiple-choice questions at '{difficulty}' difficulty. Topic/Prompt: '{prompt}'.\n"
            "Return ONLY raw valid JSON with structure:\n"
            "{\n"
            '  "title": "Quiz Title",\n'
            '  "description": "Brief description",\n'
            '  "duration_minutes": 20,\n'
            '  "passing_percentage": 50,\n'
            '  "subject": "Main Subject",\n'
            '  "questions": [\n'
            "    {\n"
            '      "question_text": "Question statement?",\n'
            '      "option_a": "Option A text",\n'
            '      "option_b": "Option B text",\n'
            '      "option_c": "Option C text",\n'
            '      "option_d": "Option D text",\n'
            '      "correct_option": "A",\n'
            '      "explanation": "Detailed pedagogical explanation",\n'
            '      "topic": "Subtopic",\n'
            '      "difficulty": "medium",\n'
            '      "learning_objective": "Specific objective"\n'
            "    }\n"
            "  ]\n"
            "}"
        )
        payload = {
            "contents": [{"parts": [{"text": sys_instructions}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text)
            parsed["source"] = "gemini_ai"
            return parsed

    @classmethod
    def _call_openai_api(
        cls, api_key: str, prompt: str, num_questions: int, difficulty: str, topic: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Call OpenAI chat completions API."""
        url = "https://api.openai.com/v1/chat/completions"
        messages = [
            {
                "role": "system",
                "content": "You are an expert assessment writer. Return valid JSON only with quiz title, duration_minutes, and questions list.",
            },
            {
                "role": "user",
                "content": f"Create {num_questions} questions for prompt: {prompt}. Difficulty: {difficulty}. Return JSON format with title, description, and questions (question_text, option_a, option_b, option_c, option_d, correct_option, explanation, topic, difficulty, learning_objective).",
            },
        ]
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_text = res_data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_text)
            parsed["source"] = "openai_gpt"
            return parsed

    @classmethod
    def _generate_local_quiz(
        cls,
        prompt: str,
        num_questions: int,
        difficulty: str,
        topic: Optional[str],
        subject: Optional[str],
    ) -> Dict[str, Any]:
        """
        Intelligent Local Generation Engine.
        Matches keywords against domain banks or generates dynamic pedagogical items from user prompt keywords.
        """
        p_lower = prompt.lower()
        matched_items: List[Dict[str, Any]] = []

        # Check domain bank matches
        for domain, bank_questions in KNOWLEDGE_BANK.items():
            if domain in p_lower:
                for q in bank_questions:
                    if q not in matched_items:
                        matched_items.append(dict(q))

        # If not enough matched items from bank, generate dynamic items based on prompt concepts
        if len(matched_items) < num_questions:
            needed = num_questions - len(matched_items)
            dynamic_items = cls._generate_dynamic_concepts(prompt, needed, difficulty)
            matched_items.extend(dynamic_items)

        # Slice to exact count requested
        final_questions = matched_items[:num_questions]

        # Format clean title
        words = [w.capitalize() for w in re.findall(r"[A-Za-z0-9]+", prompt)]
        clean_title_core = " ".join(words[:5]) if words else "Assessment"
        title = f"{clean_title_core} Assessment Quiz"

        calc_duration = max(10, num_questions * 3)

        return {
            "title": title,
            "description": f"AI-generated assessment evaluating core concepts: {prompt}",
            "subject": subject or (words[0] if words else "General"),
            "duration_minutes": calc_duration,
            "passing_percentage": 50,
            "questions": final_questions,
            "source": "teachwise_local_ai",
        }

    @classmethod
    def _generate_dynamic_concepts(
        cls, prompt: str, count: int, difficulty: str
    ) -> List[Dict[str, Any]]:
        """Dynamically construct pedagogically sound questions for arbitrary user prompts."""
        words = re.findall(r"[A-Za-z0-9_]+", prompt)
        concept = " ".join(words[:4]) if words else "Core Concept"
        key_term = words[0] if words else "Concept"

        templates = [
            {
                "text": f"What is the primary defining characteristic or purpose of {concept}?",
                "opt_a": f"It establishes the fundamental structure and verified behavior for {concept}.",
                "opt_b": f"It is a legacy mechanism that is deprecated in modern implementations of {key_term}.",
                "opt_c": f"It prevents all runtime state modifications regardless of configuration.",
                "opt_d": f"It doubles execution throughput by eliminating system validation.",
                "correct": "A",
                "explanation": f"The core function of {concept} is providing foundational structure, consistency, and standard operation.",
            },
            {
                "text": f"When implementing or applying {concept}, which of the following is considered an industry best practice?",
                "opt_a": "Maintaining clear separation of concerns, explicit validation, and modular decomposition.",
                "opt_b": "Coupling state variables directly across all components without interfaces.",
                "opt_c": "Hardcoding configuration parameters directly into execution routines.",
                "opt_d": "Suppressing error messages and unhandled exceptions globally.",
                "correct": "A",
                "explanation": "Separation of concerns, explicit input validation, and modular architecture are standard best practices across modern systems.",
            },
            {
                "text": f"Which common misconception should be avoided when evaluating {concept}?",
                "opt_a": f"Assuming {concept} provides a universal replacement for all alternative design strategies without trade-offs.",
                "opt_b": f"Recognizing that {concept} requires verification and testing before deployment.",
                "opt_c": f"Validating requirements prior to production release of {key_term}.",
                "opt_d": "Documenting interfaces for team maintainability.",
                "correct": "A",
                "explanation": f"A frequent misconception is assuming {concept} is a silver bullet without considering specific domain trade-offs and complexity.",
            },
            {
                "text": f"Under which condition would a system benefit MOST from adopting {concept}?",
                "opt_a": "When scalability, testability, and deterministic results are critical requirements.",
                "opt_b": "When memory usage must be minimized by eliminating all error handling.",
                "opt_c": "Only when working with single-threaded command-line scripts.",
                "opt_d": "When random non-repeatable behavior is desired.",
                "correct": "A",
                "explanation": "Architectural principles like modularity and rigorous assessment shine when scalability, predictability, and verification are required.",
            },
            {
                "text": f"How does {concept} handle edge cases or unexpected input anomalies?",
                "opt_a": "Through structured validation, error boundaries, and informative diagnostics.",
                "opt_b": "By terminating the host operating system immediately.",
                "opt_c": "By silently corrupting adjacent memory buffers.",
                "opt_d": "By discarding all previous transaction history without notice.",
                "correct": "A",
                "explanation": "Robust systems implement guarded error boundaries and structured validation to handle anomalies reliably.",
            },
        ]

        items = []
        for i in range(count):
            t = templates[i % len(templates)]
            items.append(
                {
                    "question_text": t["text"],
                    "option_a": t["opt_a"],
                    "option_b": t["opt_b"],
                    "option_c": t["opt_c"],
                    "option_d": t["opt_d"],
                    "correct_option": t["correct"],
                    "explanation": t["explanation"],
                    "topic": concept,
                    "difficulty": difficulty,
                    "learning_objective": f"Understand principles and applications of {concept}",
                    "marks": 1,
                }
            )
        return items

    @classmethod
    def parse_and_generate_from_file(
        cls,
        file_content: str,
        filename: str,
        num_questions: int = 5,
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        """
        Parse an uploaded file (.csv, .json, .txt, .md) and produce a ready-to-save Quiz.
        """
        ext = os.path.splitext(filename)[1].lower()
        title = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").replace("-", " ").title()

        if ext == ".csv":
            return cls._parse_csv_file(file_content, title)
        elif ext == ".json":
            return cls._parse_json_file(file_content, title)
        else:
            return cls._parse_text_file(file_content, title, num_questions, difficulty)

    @classmethod
    def _parse_csv_file(cls, content: str, default_title: str) -> Dict[str, Any]:
        """Parse CSV questions."""
        f = io.StringIO(content.strip())
        reader = csv.DictReader(f)
        questions = []

        for row in reader:
            # Normalize keys to lower
            r = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            q_text = r.get("question") or r.get("question_text") or r.get("prompt")
            opt_a = r.get("option_a") or r.get("a") or r.get("opt_a")
            opt_b = r.get("option_b") or r.get("b") or r.get("opt_b")
            opt_c = r.get("option_c") or r.get("c") or r.get("opt_c")
            opt_d = r.get("option_d") or r.get("d") or r.get("opt_d")
            corr = (r.get("correct_option") or r.get("correct") or r.get("answer") or "A").upper()[:1]
            exp = r.get("explanation") or r.get("note") or f"Correct answer is {corr}."
            top = r.get("topic") or "General"
            diff = r.get("difficulty") or "medium"

            if q_text and opt_a and opt_b and opt_c and opt_d:
                questions.append(
                    {
                        "question_text": q_text,
                        "option_a": opt_a,
                        "option_b": opt_b,
                        "option_c": opt_c,
                        "option_d": opt_d,
                        "correct_option": corr if corr in ("A", "B", "C", "D") else "A",
                        "explanation": exp,
                        "topic": top,
                        "difficulty": diff,
                        "learning_objective": r.get("learning_objective", ""),
                        "marks": 1,
                    }
                )

        if not questions:
            raise ValueError("No valid questions found in CSV. Headers required: question, option_a, option_b, option_c, option_d, correct_option")

        return {
            "title": f"{default_title} (Imported)",
            "description": f"Imported quiz containing {len(questions)} questions from CSV file.",
            "subject": "Imported Assessment",
            "duration_minutes": max(15, len(questions) * 3),
            "passing_percentage": 50,
            "questions": questions,
            "source": "csv_import",
        }

    @classmethod
    def _parse_json_file(cls, content: str, default_title: str) -> Dict[str, Any]:
        """Parse JSON quiz or list of questions."""
        data = json.loads(content)
        if isinstance(data, list):
            questions = []
            for item in data:
                questions.append(
                    {
                        "question_text": item.get("question_text") or item.get("question", ""),
                        "option_a": item.get("option_a") or item.get("a", ""),
                        "option_b": item.get("option_b") or item.get("b", ""),
                        "option_c": item.get("option_c") or item.get("c", ""),
                        "option_d": item.get("option_d") or item.get("d", ""),
                        "correct_option": (item.get("correct_option") or item.get("answer") or "A").upper()[:1],
                        "explanation": item.get("explanation", ""),
                        "topic": item.get("topic", "General"),
                        "difficulty": item.get("difficulty", "medium"),
                        "learning_objective": item.get("learning_objective", ""),
                        "marks": item.get("marks", 1),
                    }
                )
            return {
                "title": f"{default_title} (JSON Import)",
                "description": f"Imported {len(questions)} questions from JSON.",
                "subject": "Imported",
                "duration_minutes": max(15, len(questions) * 3),
                "passing_percentage": 50,
                "questions": questions,
                "source": "json_import",
            }
        elif isinstance(data, dict):
            # Already a structured quiz dict
            qs = data.get("questions", [])
            return {
                "title": data.get("title", f"{default_title} (JSON)"),
                "description": data.get("description", "Imported assessment"),
                "subject": data.get("subject", "General"),
                "duration_minutes": data.get("duration_minutes", max(15, len(qs) * 3)),
                "passing_percentage": data.get("passing_percentage", 50),
                "questions": qs,
                "source": "json_import",
            }
        else:
            raise ValueError("Invalid JSON format. Expected an array of questions or a quiz object.")

    @classmethod
    def _parse_text_file(
        cls, content: str, default_title: str, num_questions: int, difficulty: str
    ) -> Dict[str, Any]:
        """
        Parse text notes or structured Q&A text.
        If structured (Q1... A) ... Ans: B), extracts directly.
        If unformatted text (notes/articles), extracts key facts and generates MCQs.
        """
        # Look for explicit Q/A pattern: Q1. ... A) ... B) ... C) ... D) ... Ans: ...
        q_blocks = re.split(r"\n\s*(?:Q\d+[\.:\)]|\d+[\.:\)])\s*", content, flags=re.IGNORECASE)
        structured_questions = []

        for block in q_blocks:
            if not block.strip():
                continue
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            q_text = lines[0] if lines else ""

            # Extract options A, B, C, D
            opt_a = re.search(r"(?:A[\)\.:]\s*|\[A\]\s*)(.*?)(?=(?:B[\)\.:]|\[B\])|$)", block, re.DOTALL | re.IGNORECASE)
            opt_b = re.search(r"(?:B[\)\.:]\s*|\[B\]\s*)(.*?)(?=(?:C[\)\.:]|\[C\])|$)", block, re.DOTALL | re.IGNORECASE)
            opt_c = re.search(r"(?:C[\)\.:]\s*|\[C\]\s*)(.*?)(?=(?:D[\)\.:]|\[D\])|$)", block, re.DOTALL | re.IGNORECASE)
            opt_d = re.search(r"(?:D[\)\.:]\s*|\[D\]\s*)(.*?)(?=(?:Ans|Answer|Explanation|\n\n|$))", block, re.DOTALL | re.IGNORECASE)
            ans = re.search(r"(?:Ans|Answer|Correct)[\s\.:=]+([A-Da-d])", block, re.IGNORECASE)

            if q_text and opt_a and opt_b and opt_c and opt_d:
                structured_questions.append(
                    {
                        "question_text": q_text[:200],
                        "option_a": opt_a.group(1).strip()[:150],
                        "option_b": opt_b.group(1).strip()[:150],
                        "option_c": opt_c.group(1).strip()[:150],
                        "option_d": opt_d.group(1).strip()[:150],
                        "correct_option": ans.group(1).upper() if ans else "A",
                        "explanation": f"Extracted from document notes for question: {q_text[:80]}",
                        "topic": default_title,
                        "difficulty": difficulty,
                        "learning_objective": f"Review key material from {default_title}",
                        "marks": 1,
                    }
                )

        if structured_questions:
            return {
                "title": f"{default_title} (Extracted Quiz)",
                "description": f"Extracted {len(structured_questions)} questions from document.",
                "subject": default_title,
                "duration_minutes": max(15, len(structured_questions) * 3),
                "passing_percentage": 50,
                "questions": structured_questions,
                "source": "text_extracted",
            }

        # Otherwise: unformatted study notes or document text
        # Extract informative sentences and generate questions
        sentences = [s.strip() for s in re.split(r"[\.\?\!]\s+", content) if len(s.strip()) > 35]
        if not sentences:
            sentences = [content.strip()[:120]]

        generated_from_text = []
        for i, sentence in enumerate(sentences[:num_questions]):
            words = sentence.split()
            subject_phrase = " ".join(words[:4])
            fact_summary = sentence[:180]

            generated_from_text.append(
                {
                    "question_text": f"According to the provided document, which statement regarding '{subject_phrase}' is correct?",
                    "option_a": fact_summary,
                    "option_b": f"The document notes that {subject_phrase} is strictly avoided in all scenarios.",
                    "option_c": f"The document states that {subject_phrase} has no measurable effect on the subject.",
                    "option_d": f"The document replaces {subject_phrase} with an incompatible legacy protocol.",
                    "correct_option": "A",
                    "explanation": f"Source reference from document text: \"{fact_summary}\"",
                    "topic": default_title,
                    "difficulty": difficulty,
                    "learning_objective": f"Recall and comprehend key points from {default_title}",
                    "marks": 1,
                }
            )

        return {
            "title": f"{default_title} — Document Assessment",
            "description": f"Automatically generated quiz synthesized from uploaded document notes.",
            "subject": default_title,
            "duration_minutes": max(15, len(generated_from_text) * 3),
            "passing_percentage": 50,
            "questions": generated_from_text,
            "source": "text_synthesized",
        }

    @classmethod
    def save_quiz_to_database(
        cls,
        db: Session,
        quiz_data: Dict[str, Any],
        creator_id: int,
        is_public: bool = True,
    ) -> Quiz:
        """
        Persist an AI-generated or imported quiz and all its questions into the database.
        Calculates total marks automatically and assigns a unique join code.
        """
        questions_raw = quiz_data.get("questions", [])
        total_marks = sum(q.get("marks", 1) for q in questions_raw)

        join_code = _generate_join_code()

        quiz = Quiz(
            title=quiz_data.get("title", "AI Generated Assessment"),
            subject=quiz_data.get("subject", "General"),
            description=quiz_data.get("description", "AI Assessment"),
            instructions="Read each question carefully. Select the best answer among the options provided.",
            duration_minutes=quiz_data.get("duration_minutes", 30),
            passing_percentage=quiz_data.get("passing_percentage", 50),
            total_marks=total_marks,
            is_published=False,  # Saved as draft initially so teacher can review/publish!
            join_code=join_code,
            is_public=is_public,
            max_attempts=1,
            release_results_immediately=True,
            results_released=True,
            created_by_id=creator_id,
        )
        db.add(quiz)
        db.flush()

        for idx, q in enumerate(questions_raw):
            new_q = Question(
                quiz_id=quiz.id,
                question_text=q["question_text"],
                option_a=q["option_a"],
                option_b=q["option_b"],
                option_c=q["option_c"],
                option_d=q["option_d"],
                correct_option=q["correct_option"],
                marks=q.get("marks", 1),
                explanation=q.get("explanation", ""),
                topic=q.get("topic", "General"),
                difficulty=q.get("difficulty", "medium"),
                learning_objective=q.get("learning_objective", ""),
                order_index=idx,
            )
            db.add(new_q)

        db.commit()
        db.refresh(quiz)
        return quiz

