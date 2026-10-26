"""
Admin Question Management View: Adding, Viewing, and Deleting Questions for a Quiz.
"""
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
from app.utils.theme import Theme
from app.services.api_client import api_client


class AddQuestionDialog(ctk.CTkToplevel):
    def __init__(self, master, quiz_id: int, on_success):
        super().__init__(master)
        self.quiz_id = quiz_id
        self.on_success = on_success
        self.title("Add Multiple-Choice Question")
        self.geometry("560x680")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="Add New Question", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(10, 12))

        # Question Text
        ctk.CTkLabel(scroll, text="Question Statement *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.q_text = ctk.CTkTextbox(scroll, height=70, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.q_text.pack(fill="x", padx=16, pady=(0, 10))

        # Options A, B, C, D
        ctk.CTkLabel(scroll, text="Option A *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_a = ctk.CTkEntry(scroll, placeholder_text="Option A value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_a.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Option B *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_b = ctk.CTkEntry(scroll, placeholder_text="Option B value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_b.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Option C *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_c = ctk.CTkEntry(scroll, placeholder_text="Option C value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_c.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Option D *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_d = ctk.CTkEntry(scroll, placeholder_text="Option D value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_d.pack(fill="x", padx=16, pady=(0, 10))

        # Correct Option & Marks Row
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 10))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        c1 = ctk.CTkFrame(row, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(c1, text="Correct Answer *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.correct_opt = ctk.CTkSegmentedButton(c1, values=["A", "B", "C", "D"], selected_color=Theme.SUCCESS)
        self.correct_opt.set("A")
        self.correct_opt.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(row, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Marks *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.marks_entry = ctk.CTkEntry(c2, placeholder_text="1", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.marks_entry.insert(0, "1")
        self.marks_entry.pack(fill="x", pady=(2, 0))

        # Topic & Difficulty Row (Pedagogy & Misconception tracking)
        top_diff_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_diff_row.pack(fill="x", padx=16, pady=(0, 10))
        top_diff_row.grid_columnconfigure(0, weight=1)
        top_diff_row.grid_columnconfigure(1, weight=1)

        td1 = ctk.CTkFrame(top_diff_row, fg_color="transparent")
        td1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(td1, text="Topic / Concept Tag", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.topic_entry = ctk.CTkEntry(td1, placeholder_text="e.g. Memory Management", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.topic_entry.insert(0, "General")
        self.topic_entry.pack(fill="x", pady=(2, 0))

        td2 = ctk.CTkFrame(top_diff_row, fg_color="transparent")
        td2.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(td2, text="Difficulty Level", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.diff_seg = ctk.CTkSegmentedButton(td2, values=["easy", "medium", "hard"])
        self.diff_seg.set("medium")
        self.diff_seg.pack(fill="x", pady=(2, 0))

        # Explanation
        ctk.CTkLabel(scroll, text="Pedagogical Explanation / Solution Note", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.exp_entry = ctk.CTkEntry(scroll, placeholder_text="Why this answer is correct & common misconceptions to avoid", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.exp_entry.pack(fill="x", padx=16, pady=(0, 10))

        self.error_label = ctk.CTkLabel(scroll, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER, wraplength=460)
        self.error_label.pack(pady=4)

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 16))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_row,
            text="✕ Cancel",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            height=38,
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Save Question",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=38,
            command=self._handle_save,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _handle_save(self):
        text = self.q_text.get("1.0", "end-1c").strip()
        a = self.opt_a.get().strip()
        b = self.opt_b.get().strip()
        c = self.opt_c.get().strip()
        d = self.opt_d.get().strip()
        correct = self.correct_opt.get()
        marks_str = self.marks_entry.get().strip()
        exp = self.exp_entry.get().strip()
        topic = self.topic_entry.get().strip() or "General"
        diff = self.diff_seg.get()

        if not text or not a or not b or not c or not d:
            self.error_label.configure(text="Please provide the question statement and all 4 options.")
            return

        try:
            marks = int(marks_str)
            if marks <= 0:
                raise ValueError()
        except ValueError:
            self.error_label.configure(text="Marks must be a positive integer.")
            return

        ok, res = api_client.add_question(self.quiz_id, {
            "question_text": text,
            "option_a": a,
            "option_b": b,
            "option_c": c,
            "option_d": d,
            "correct_option": correct,
            "marks": marks,
            "explanation": exp or None,
            "topic": topic,
            "difficulty": diff,
        })

        if ok:
            self.destroy()
            self.on_success()
        else:
            self.error_label.configure(text=str(res))


class AIAddQuestionsDialog(ctk.CTkToplevel):
    """Generate multiple questions via AI and append to existing quiz."""
    def __init__(self, master, quiz_id: int, on_success):
        super().__init__(master)
        self.quiz_id = quiz_id
        self.on_success = on_success
        self.title("AI Question Generator — TeachWise")
        self.geometry("560x520")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="🤖 Generate Questions with AI", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(12, 4))
        ctk.CTkLabel(
            container,
            text="Enter a topic or instructional prompt to generate questions with options, correct answer, and explanation.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=480,
        ).pack(pady=(0, 12))

        ctk.CTkLabel(container, text="Question Topic or Concept *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.prompt_entry = ctk.CTkEntry(container, placeholder_text="e.g. Python List Comprehension and Generator Expressions", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.prompt_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Controls
        c_row = ctk.CTkFrame(container, fg_color="transparent")
        c_row.pack(fill="x", padx=16, pady=(0, 10))
        c_row.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(c_row, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(c1, text="Number of Questions", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.cnt_seg = ctk.CTkSegmentedButton(c1, values=["1", "3", "5"], height=32)
        self.cnt_seg.set("3")
        self.cnt_seg.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(c_row, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Difficulty", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.diff_seg = ctk.CTkSegmentedButton(c2, values=["easy", "medium", "hard"], height=32)
        self.diff_seg.set("medium")
        self.diff_seg.pack(fill="x", pady=(2, 0))

        self.status_lbl = ctk.CTkLabel(container, text="", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, wraplength=480)
        self.status_lbl.pack(pady=6)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(12, 16))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_row,
            text="✕ Cancel",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            height=38,
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.generate_btn = ctk.CTkButton(
            btn_row,
            text="✨ Generate & Add",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=38,
            command=self._handle_generate,
        )
        self.generate_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _handle_generate(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            self.status_lbl.configure(text="Please enter a topic prompt.", text_color=Theme.DANGER)
            return

        cnt = int(self.cnt_seg.get())
        diff = self.diff_seg.get()

        self.generate_btn.configure(state="disabled", text="Generating questions...")
        self.status_lbl.configure(text="Synthesizing questions with AI...", text_color=Theme.PRIMARY)
        self.update_idletasks()

        ok, res = api_client.generate_quiz_ai(prompt=prompt, num_questions=cnt, difficulty=diff, save_directly=False)
        self.generate_btn.configure(state="normal", text="✨ Generate & Add")

        if not ok or not res:
            self.status_lbl.configure(text=f"Generation notice: {res}", text_color=Theme.DANGER)
            return

        questions = res.get("questions", [])
        added_count = 0
        for q in questions:
            add_ok, _ = api_client.add_question(self.quiz_id, {
                "question_text": q["question_text"],
                "option_a": q["option_a"],
                "option_b": q["option_b"],
                "option_c": q["option_c"],
                "option_d": q["option_d"],
                "correct_option": q["correct_option"],
                "marks": q.get("marks", 1),
                "explanation": q.get("explanation", ""),
                "topic": q.get("topic", prompt),
                "difficulty": q.get("difficulty", diff),
            })
            if add_ok:
                added_count += 1

        messagebox.showinfo("Success", f"Successfully generated and added {added_count} question(s) to this quiz!")
        self.destroy()
        self.on_success()


class AdminQuestionsView(ctk.CTkFrame):
    def __init__(self, master, quiz_dict, on_back):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.quiz = quiz_dict
        self.on_back = on_back
        self.questions = []

        self.pack(fill="both", expand=True, padx=24, pady=20)
        self._build_ui()
        self.load_questions()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        back_btn = ctk.CTkButton(
            header,
            text="← Back to Quizzes",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#FFFFFF",
            text_color="#0F172A",
            hover_color="#F1F5F9",
            border_width=1,
            border_color="#94A3B8",
            width=150,
            height=34,
            corner_radius=8,
            command=self.on_back,
        )
        back_btn.pack(side="left", padx=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=f"Questions: {self.quiz['title']}",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="✨ AI Generate",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=34,
            command=self._open_ai_dialog,
        ).pack(side="left", padx=(0, 8))

        add_btn = ctk.CTkButton(
            btn_box,
            text="+ Add Question",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=34,
            command=self._open_add_dialog,
        )
        add_btn.pack(side="left")

        # Questions Scroll List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def _open_add_dialog(self):
        AddQuestionDialog(self, self.quiz["id"], on_success=self.load_questions)

    def _open_ai_dialog(self):
        AIAddQuestionsDialog(self, self.quiz["id"], on_success=self.load_questions)

    def load_questions(self):
        ok, res = api_client.get_quiz_questions(self.quiz["id"])
        if not ok:
            return

        self.questions = res
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.questions:
            ctk.CTkLabel(
                self.scroll,
                text="No questions added to this quiz yet. Click '+ Add Question' above to add MCQs.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=40)
            return

        for idx, q in enumerate(self.questions, start=1):
            self._render_question_card(idx, q)

    def _render_question_card(self, idx: int, q: dict):
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        card.pack(fill="x", pady=8, padx=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Question Header
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            top_row,
            text=f"Q{idx}.  {q['question_text']}",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
            wraplength=620,
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            top_row,
            text=f"{q['marks']} Mark(s)",
            font=Theme.FONT_SMALL,
            text_color=Theme.PRIMARY,
            fg_color=Theme.BG_INPUT,
            corner_radius=4,
            padx=8,
            pady=2,
        ).pack(side="right", padx=(8, 0))

        # Options Grid
        opt_grid = ctk.CTkFrame(inner, fg_color="transparent")
        opt_grid.pack(fill="x", pady=(4, 8))
        opt_grid.grid_columnconfigure(0, weight=1)
        opt_grid.grid_columnconfigure(1, weight=1)

        options = [
            ("A", q["option_a"]),
            ("B", q["option_b"]),
            ("C", q["option_c"]),
            ("D", q["option_d"]),
        ]
        correct = q["correct_option"]

        for i, (letter, text) in enumerate(options):
            r = i // 2
            c = i % 2
            is_correct = letter == correct

            bg_col = Theme.SUCCESS_BG if is_correct else Theme.BG_INPUT
            fg_col = Theme.SUCCESS if is_correct else Theme.TEXT_MUTED
            prefix = "✓ " if is_correct else "   "

            lbl = ctk.CTkLabel(
                opt_grid,
                text=f"{prefix}({letter}) {text}",
                font=Theme.FONT_BODY,
                text_color=fg_col,
                fg_color=bg_col,
                corner_radius=6,
                anchor="w",
                padx=10,
                pady=6,
            )
            lbl.grid(row=r, column=c, padx=4, pady=3, sticky="ew")

        # Bottom row: Explanation + Delete Button
        bot_row = ctk.CTkFrame(inner, fg_color="transparent")
        bot_row.pack(fill="x", pady=(4, 0))

        if q.get("explanation"):
            ctk.CTkLabel(
                bot_row,
                text=f"💡 Explanation: {q['explanation']}",
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_DIM,
                anchor="w",
                wraplength=540,
            ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            bot_row,
            text="Delete Question",
            font=Theme.FONT_SMALL,
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            width=110,
            height=26,
            command=lambda q_id=q["id"]: self._delete_question(q_id),
        ).pack(side="right")

    def _delete_question(self, question_id: int):
        api_client.delete_question(question_id)
        self.load_questions()

