"""
Admin & Teacher Question Management View: Adding, Editing, Viewing, and Importing Questions for a Quiz.
Supports:
1. Universal Question Editing (for manual, imported, and AI-generated questions).
2. Question Import from any file format (.pdf, .ppt, .pptx, .docx, .xlsx, .csv, .txt, .md, images).
3. AI Generation of questions directly into the quiz.
4. Manual question creation form.
"""
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk

from app.services.api_client import api_client
from app.services.document_extractor import DocumentExtractor
from app.utils.theme import Theme


class EditQuestionDialog(ctk.CTkToplevel):
    """
    Universal Question Editor — works for all question types (manual, imported, AI-generated).
    Allows editing question statement, 4 choices, correct answer, marks, topic, difficulty, and explanation.
    """
    def __init__(self, master, question_data: dict, on_success):
        super().__init__(master)
        self.question = question_data
        self.question_id = question_data["id"]
        self.on_success = on_success

        self.title(f"Edit Question #{self.question_id}")
        self.geometry("580x700")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Title & Source Badge Row
        hdr_row = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(10, 12))

        ctk.CTkLabel(
            hdr_row,
            text="✏️ Edit Assessment Question",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        source_val = self.question.get("source", "manual")
        source_label = f"Source: {source_val}"
        ctk.CTkLabel(
            hdr_row,
            text=source_label,
            font=Theme.FONT_SMALL,
            text_color=Theme.PRIMARY,
            fg_color=Theme.BG_INPUT,
            corner_radius=6,
            padx=8,
            pady=3,
        ).pack(side="right")

        # Question Text
        ctk.CTkLabel(scroll, text="Question Statement *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.q_text = ctk.CTkTextbox(scroll, height=75, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.q_text.insert("1.0", self.question.get("question_text", ""))
        self.q_text.pack(fill="x", padx=16, pady=(0, 10))

        # Options A, B, C, D
        ctk.CTkLabel(scroll, text="Option A *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_a = ctk.CTkEntry(scroll, placeholder_text="Option A value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_a.insert(0, self.question.get("option_a", ""))
        self.opt_a.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Option B *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_b = ctk.CTkEntry(scroll, placeholder_text="Option B value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_b.insert(0, self.question.get("option_b", ""))
        self.opt_b.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Option C *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_c = ctk.CTkEntry(scroll, placeholder_text="Option C value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_c.insert(0, self.question.get("option_c", ""))
        self.opt_c.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(scroll, text="Option D *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.opt_d = ctk.CTkEntry(scroll, placeholder_text="Option D value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_d.insert(0, self.question.get("option_d", ""))
        self.opt_d.pack(fill="x", padx=16, pady=(0, 10))

        # Correct Option & Marks Row
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(row, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(c1, text="Correct Answer Choice *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.correct_opt = ctk.CTkSegmentedButton(c1, values=["A", "B", "C", "D"], selected_color=Theme.SUCCESS)
        corr_val = self.question.get("correct_option", "A").upper()
        self.correct_opt.set(corr_val if corr_val in ("A", "B", "C", "D") else "A")
        self.correct_opt.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(row, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Assigned Marks *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.marks_entry = ctk.CTkEntry(c2, placeholder_text="1", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.marks_entry.insert(0, str(self.question.get("marks", 1)))
        self.marks_entry.pack(fill="x", pady=(2, 0))

        # Topic & Difficulty Row
        top_diff_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_diff_row.pack(fill="x", padx=16, pady=(0, 10))
        top_diff_row.grid_columnconfigure((0, 1), weight=1)

        td1 = ctk.CTkFrame(top_diff_row, fg_color="transparent")
        td1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(td1, text="Topic / Concept Tag", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.topic_entry = ctk.CTkEntry(td1, placeholder_text="e.g. Algorithms", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.topic_entry.insert(0, self.question.get("topic", "General") or "General")
        self.topic_entry.pack(fill="x", pady=(2, 0))

        td2 = ctk.CTkFrame(top_diff_row, fg_color="transparent")
        td2.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(td2, text="Difficulty Level", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.diff_seg = ctk.CTkSegmentedButton(td2, values=["easy", "medium", "hard"])
        cur_diff = self.question.get("difficulty", "medium")
        self.diff_seg.set(cur_diff if cur_diff in ("easy", "medium", "hard") else "medium")
        self.diff_seg.pack(fill="x", pady=(2, 0))

        # Explanation
        ctk.CTkLabel(scroll, text="Pedagogical Explanation / Solution Note", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.exp_entry = ctk.CTkEntry(scroll, placeholder_text="Explain why this answer is correct", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        if self.question.get("explanation"):
            self.exp_entry.insert(0, self.question["explanation"])
        self.exp_entry.pack(fill="x", padx=16, pady=(0, 10))

        self.error_label = ctk.CTkLabel(scroll, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER, wraplength=460)
        self.error_label.pack(pady=4)

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 16))
        btn_row.grid_columnconfigure((0, 1), weight=1)

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
            text="💾 Save Changes",
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

        payload = {
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
        }

        ok, res = api_client.update_question(self.question_id, payload)
        if ok:
            messagebox.showinfo("Success", "Question updated successfully!")
            self.destroy()
            self.on_success()
        else:
            self.error_label.configure(text=str(res))


class ImportQuestionsDialog(ctk.CTkToplevel):
    """
    Universal File Importer for QuizFlow Assessments.
    Supports importing from ANY file format:
    - PowerPoint (.pptx, .ppt)
    - PDF (.pdf)
    - Microsoft Word (.docx)
    - Excel & CSV (.xlsx, .csv)
    - Plain text notes (.txt, .md, .rtf, .json)
    - Images (.png, .jpg, .jpeg, .webp)
    Automatically parses or synthesizes questions into the application format and adds them to this quiz.
    """
    def __init__(self, master, quiz_id: int, on_success):
        super().__init__(master)
        self.quiz_id = quiz_id
        self.on_success = on_success

        self.title("Import Questions from Document — QuizFlow")
        self.geometry("600x560")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self.selected_file_path = None
        self.extracted_text = ""

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="📁 Import Questions from Document", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(12, 4))
        ctk.CTkLabel(
            container,
            text="Upload any document (PDF, PowerPoint slides, Word DOCX, Excel/CSV, or notes). QuizFlow extracts questions or synthesizes tests formatted according to the application standards.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=520,
            justify="center",
        ).pack(pady=(0, 14))

        # File Select Card
        file_box = ctk.CTkFrame(container, fg_color=Theme.BG_INPUT, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        file_box.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            file_box,
            text="📂 Choose File from Computer...",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#FFFFFF",
            text_color="#0F172A",
            hover_color="#F1F5F9",
            border_width=1,
            border_color="#94A3B8",
            height=38,
            command=self._choose_file,
        ).pack(padx=14, pady=(12, 6))

        self.file_info_lbl = ctk.CTkLabel(
            file_box,
            text="Supported: .pdf, .ppt, .pptx, .docx, .xlsx, .csv, .txt, .md, images",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        )
        self.file_info_lbl.pack(padx=14, pady=(0, 12))

        # Or Paste Notes Box
        ctk.CTkLabel(container, text="— OR Paste Document Content / Questions Directly —", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(4, 4))
        self.paste_box = ctk.CTkTextbox(container, height=90, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.paste_box.pack(fill="x", padx=16, pady=(0, 10))

        # Options Row: Number of Questions & Difficulty
        c_row = ctk.CTkFrame(container, fg_color="transparent")
        c_row.pack(fill="x", padx=16, pady=(0, 10))
        c_row.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(c_row, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(c1, text="Target Questions", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.num_seg = ctk.CTkSegmentedButton(c1, values=["3", "5", "10", "15"], height=32)
        self.num_seg.set("5")
        self.num_seg.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(c_row, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Difficulty Level", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.diff_seg = ctk.CTkSegmentedButton(c2, values=["easy", "medium", "hard"], height=32)
        self.diff_seg.set("medium")
        self.diff_seg.pack(fill="x", pady=(2, 0))

        self.status_lbl = ctk.CTkLabel(container, text="", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, wraplength=500)
        self.status_lbl.pack(pady=4)

        # Action Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 14))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row,
            text="✕ Cancel",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            height=40,
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.import_btn = ctk.CTkButton(
            btn_row,
            text="⚡ Extract & Add to Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=40,
            command=self._handle_import,
        )
        self.import_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _choose_file(self):
        f_path = filedialog.askopenfilename(
            title="Select Assessment Document",
            filetypes=[
                ("All Supported Educational Documents", "*.pdf;*.ppt;*.pptx;*.docx;*.xlsx;*.csv;*.txt;*.md;*.json;*.png;*.jpg;*.jpeg;*.webp"),
                ("PowerPoint Presentations (*.pptx, *.ppt)", "*.pptx;*.ppt;*.ppsx"),
                ("PDF Documents (*.pdf)", "*.pdf"),
                ("Word Documents (*.docx)", "*.docx;*.dotx"),
                ("Spreadsheets (*.csv, *.xlsx)", "*.csv;*.xlsx;*.xls"),
                ("Text & Notes (*.txt, *.md, *.json)", "*.txt;*.md;*.json"),
                ("All Files (*.*)", "*.*"),
            ],
        )
        if f_path:
            self.selected_file_path = f_path
            filename = os.path.basename(f_path)
            try:
                self.extracted_text = DocumentExtractor.extract_text_from_file(f_path)
                char_count = len(self.extracted_text.strip())
                self.file_info_lbl.configure(
                    text=f"✓ Loaded: {filename} ({char_count} chars extracted)",
                    text_color=Theme.SUCCESS,
                )
            except Exception as e:
                self.file_info_lbl.configure(
                    text=f"Error reading file: {str(e)}",
                    text_color=Theme.DANGER,
                )

    def _handle_import(self):
        content = self.extracted_text
        filename = os.path.basename(self.selected_file_path) if self.selected_file_path else "Pasted_Content.txt"

        if not content:
            pasted = self.paste_box.get("1.0", "end-1c").strip()
            if pasted:
                content = pasted
                filename = "Pasted_Notes.txt"

        if not content or len(content.strip()) < 10:
            self.status_lbl.configure(text="Please choose a file or paste document content.", text_color=Theme.DANGER)
            return

        num_q = int(self.num_seg.get())
        diff = self.diff_seg.get()

        self.import_btn.configure(state="disabled", text="Extracting questions...")
        self.status_lbl.configure(text="Processing file and formatting questions...", text_color=Theme.PRIMARY)
        self.update_idletasks()

        ok, res = api_client.import_quiz_file(
            file_content=content,
            filename=filename,
            num_questions=num_q,
            difficulty=diff,
            save_directly=False,
        )
        self.import_btn.configure(state="normal", text="⚡ Extract & Add to Quiz")

        if not ok or not res:
            self.status_lbl.configure(text=f"Import notice: {res}", text_color=Theme.DANGER)
            return

        questions = res.get("questions", [])
        if not questions:
            self.status_lbl.configure(text="No questions could be extracted from this document.", text_color=Theme.DANGER)
            return

        added_count = 0
        for q in questions:
            add_ok, _ = api_client.add_question(self.quiz_id, {
                "question_text": q["question_text"],
                "option_a": q["option_a"],
                "option_b": q["option_b"],
                "option_c": q["option_c"],
                "option_d": q["option_d"],
                "correct_option": q.get("correct_option", "A"),
                "marks": q.get("marks", 1),
                "explanation": q.get("explanation", ""),
                "topic": q.get("topic", os.path.splitext(filename)[0]),
                "difficulty": q.get("difficulty", diff),
            })
            if add_ok:
                added_count += 1

        messagebox.showinfo("Import Successful", f"Successfully extracted and added {added_count} question(s) to this quiz!")
        self.destroy()
        self.on_success()


class AddQuestionDialog(ctk.CTkToplevel):
    """
    Standard Manual Question Form with direct shortcuts to AI Generation and File Import.
    """
    def __init__(self, master, quiz_id: int, on_success):
        super().__init__(master)
        self.quiz_id = quiz_id
        self.on_success = on_success
        self.title("Add Multiple-Choice Question — QuizFlow")
        self.geometry("580x700")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Quick Creation Shortcuts Banner
        shortcut_bar = ctk.CTkFrame(scroll, fg_color=Theme.BG_INPUT, corner_radius=8)
        shortcut_bar.pack(fill="x", padx=16, pady=(10, 10))

        ctk.CTkLabel(shortcut_bar, text="Quick Add Methods:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            shortcut_bar,
            text="🤖 AI Generate",
            font=Theme.FONT_SMALL,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=28,
            command=self._switch_to_ai,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            shortcut_bar,
            text="📁 Import File",
            font=Theme.FONT_SMALL,
            fg_color="#FFFFFF",
            text_color="#0F172A",
            hover_color="#F1F5F9",
            border_width=1,
            border_color="#94A3B8",
            height=28,
            command=self._switch_to_import,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(scroll, text="Add New Question (Manual Entry)", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(4, 10))

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

        ctk.CTkLabel(scroll, text="Option D *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 10))
        self.opt_d = ctk.CTkEntry(scroll, placeholder_text="Option D value", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.opt_d.pack(fill="x", padx=16, pady=(0, 10))

        # Correct Option & Marks Row
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)

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

        # Topic & Difficulty Row
        top_diff_row = ctk.CTkFrame(scroll, fg_color="transparent")
        top_diff_row.pack(fill="x", padx=16, pady=(0, 10))
        top_diff_row.grid_columnconfigure((0, 1), weight=1)

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
        self.exp_entry = ctk.CTkEntry(scroll, placeholder_text="Why this answer is correct", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.exp_entry.pack(fill="x", padx=16, pady=(0, 10))

        self.error_label = ctk.CTkLabel(scroll, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER, wraplength=460)
        self.error_label.pack(pady=4)

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 16))
        btn_row.grid_columnconfigure((0, 1), weight=1)

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

    def _switch_to_ai(self):
        self.destroy()
        AIAddQuestionsDialog(self.master, self.quiz_id, on_success=self.on_success)

    def _switch_to_import(self):
        self.destroy()
        ImportQuestionsDialog(self.master, self.quiz_id, on_success=self.on_success)

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
        self.title("AI Question Generator — QuizFlow")
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
        btn_row.grid_columnconfigure((0, 1), weight=1)

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
    """
    Dedicated Assessment Question Management View.
    Allows Teachers and Admins to view, add, edit, import, and delete questions for a quiz.
    """
    def __init__(self, master, quiz_dict, on_back):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.quiz = quiz_dict
        self.on_back = on_back
        self.questions = []

        self.pack(fill="both", expand=True, padx=24, pady=20)
        self._build_ui()
        self.load_questions()

    def _build_ui(self):
        # Header Row
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

        # Top-Right Toolbar: 3 Functional Buttons (AI Generate, Import File, + Add Question)
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        # 1. AI Generate Button
        ctk.CTkButton(
            btn_box,
            text="✨ AI Generate",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=34,
            corner_radius=8,
            command=self._open_ai_dialog,
        ).pack(side="left", padx=(0, 8))

        # 2. Import File Button
        ctk.CTkButton(
            btn_box,
            text="📁 Import File",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#FFFFFF",
            text_color="#0F172A",
            hover_color="#F1F5F9",
            border_width=1,
            border_color="#94A3B8",
            height=34,
            corner_radius=8,
            command=self._open_import_dialog,
        ).pack(side="left", padx=(0, 8))

        # 3. + Add Question Button
        ctk.CTkButton(
            btn_box,
            text="+ Add Question",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._open_add_dialog,
        ).pack(side="left")

        # Questions Scroll List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def _open_add_dialog(self):
        AddQuestionDialog(self, self.quiz["id"], on_success=self.load_questions)

    def _open_ai_dialog(self):
        AIAddQuestionsDialog(self, self.quiz["id"], on_success=self.load_questions)

    def _open_import_dialog(self):
        ImportQuestionsDialog(self, self.quiz["id"], on_success=self.load_questions)

    def _open_edit_dialog(self, question_data: dict):
        EditQuestionDialog(self, question_data, on_success=self.load_questions)

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
                text="No questions added to this quiz yet.\nClick '+ Add Question', '📁 Import File', or '✨ AI Generate' above to add questions.",
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

        # Question Header: Number, Text, Marks, Source
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            top_row,
            text=f"Q{idx}.  {q['question_text']}",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
            wraplength=580,
        ).pack(side="left", fill="x", expand=True)

        badge_box = ctk.CTkFrame(top_row, fg_color="transparent")
        badge_box.pack(side="right", padx=(8, 0))

        source_tag = q.get("source", "manual")
        if source_tag != "manual":
            ctk.CTkLabel(
                badge_box,
                text=source_tag,
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED,
                fg_color=Theme.BG_MAIN,
                corner_radius=4,
                padx=6,
                pady=2,
            ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            badge_box,
            text=f"{q['marks']} Mark(s)",
            font=Theme.FONT_SMALL,
            text_color=Theme.PRIMARY,
            fg_color=Theme.BG_INPUT,
            corner_radius=4,
            padx=8,
            pady=2,
        ).pack(side="left")

        # Options Grid (A, B, C, D)
        opt_grid = ctk.CTkFrame(inner, fg_color="transparent")
        opt_grid.pack(fill="x", pady=(4, 8))
        opt_grid.grid_columnconfigure((0, 1), weight=1)

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

        # Bottom row: Explanation on Left, Action Buttons (Edit + Delete) on Right
        bot_row = ctk.CTkFrame(inner, fg_color="transparent")
        bot_row.pack(fill="x", pady=(4, 0))

        if q.get("explanation"):
            ctk.CTkLabel(
                bot_row,
                text=f"💡 Explanation: {q['explanation']}",
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_DIM,
                anchor="w",
                wraplength=480,
            ).pack(side="left", fill="x", expand=True)
        else:
            ctk.CTkFrame(bot_row, fg_color="transparent").pack(side="left", fill="x", expand=True)

        # Action Buttons Box: Edit Question & Delete Question
        act_box = ctk.CTkFrame(bot_row, fg_color="transparent")
        act_box.pack(side="right")

        # Edit Question Button
        ctk.CTkButton(
            act_box,
            text="✏️ Edit",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            width=76,
            height=28,
            corner_radius=6,
            command=lambda q_data=q: self._open_edit_dialog(q_data),
        ).pack(side="left", padx=(0, 6))

        # Delete Question Button
        ctk.CTkButton(
            act_box,
            text="🗑️ Delete",
            font=Theme.FONT_SMALL,
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            text_color="#FFFFFF",
            width=76,
            height=28,
            corner_radius=6,
            command=lambda q_id=q["id"]: self._delete_question(q_id),
        ).pack(side="left")

    def _delete_question(self, question_id: int):
        confirm = messagebox.askyesno("Delete Question", "Are you sure you want to delete this question?")
        if confirm:
            api_client.delete_question(question_id)
            self.load_questions()
