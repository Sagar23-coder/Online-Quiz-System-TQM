"""
Organizer Dashboard View: Teacher Workspace for QuizFlow.
Manages quiz creation, restricted private join codes, question management, result release, and CSV reporting.
"""
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.components.stat_card import StatCard
from app.components.visual_charts import CircularProgress, MiniSparkline, PerformanceDoubleBarChart
from app.services.api_client import api_client


class CreateOrEditQuizDialog(ctk.CTkToplevel):
    """
    Teacher Assessment Creation Workspace with Multi-Mode Generation:
    1. Manual Setup: standard form configuration.
    2. AI Prompt Generator: create complete quizzes & questions from a single prompt.
    3. File / Notes Import: automatically extract or synthesize quizzes from CSV, JSON, TXT, or Markdown.
    """
    def __init__(self, master, quiz_data=None, on_success=None):
        super().__init__(master)
        self.quiz_data = quiz_data
        self.on_success = on_success
        self.is_edit = quiz_data is not None
        self.title("Edit Quiz Configuration" if self.is_edit else "Create New Assessment Quiz — TeachWise")
        self.geometry("620x720")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self.generated_quiz_preview = None
        self.imported_file_path = None
        self.imported_file_content = ""

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        self.container = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        title_text = "Edit Quiz Configuration" if self.is_edit else "Create New Assessment Quiz"
        ctk.CTkLabel(self.container, text=title_text, font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(12, 6))

        if not self.is_edit:
            # Creation Mode Selector
            mode_box = ctk.CTkFrame(self.container, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
            mode_box.pack(fill="x", padx=16, pady=(4, 14))

            ctk.CTkLabel(mode_box, text="Creation Method:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=12, pady=(8, 2))
            self.mode_toggle = ctk.CTkSegmentedButton(
                mode_box,
                values=["✍️ Manual Setup", "🤖 Generate with AI", "📁 Import from File"],
                command=self._on_mode_change,
                selected_color=Theme.PRIMARY,
                unselected_color=Theme.BG_CARD,
                text_color=Theme.TEXT_MAIN,
                font=Theme.FONT_SMALL,
                height=34,
            )
            self.mode_toggle.set("✍️ Manual Setup")
            self.mode_toggle.pack(fill="x", padx=12, pady=(0, 10))

        # Dynamic Content Frame for selected mode
        self.content_subframe = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content_subframe.pack(fill="both", expand=True)

        self._render_manual_view()

    def _on_mode_change(self, mode_str):
        for w in self.content_subframe.winfo_children():
            w.destroy()

        if "AI" in mode_str:
            self._render_ai_view()
        elif "Import" in mode_str:
            self._render_file_view()
        else:
            self._render_manual_view()

    # ------------------ Mode 1: Manual Form View ------------------
    def _render_manual_view(self):
        sub = self.content_subframe

        # Title
        ctk.CTkLabel(sub, text="Quiz Title *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.title_entry = ctk.CTkEntry(sub, placeholder_text="e.g. Physics Midterm Exam", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        if self.quiz_data:
            self.title_entry.insert(0, self.quiz_data.get("title", ""))
        self.title_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Description
        ctk.CTkLabel(sub, text="Description", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.desc_entry = ctk.CTkEntry(sub, placeholder_text="Brief summary or topic coverage", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        if self.quiz_data and self.quiz_data.get("description"):
            self.desc_entry.insert(0, self.quiz_data["description"])
        self.desc_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Instructions
        ctk.CTkLabel(sub, text="Student Instructions", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.inst_entry = ctk.CTkEntry(sub, placeholder_text="e.g. Calculators allowed. Complete before time expires.", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        if self.quiz_data and self.quiz_data.get("instructions"):
            self.inst_entry.insert(0, self.quiz_data["instructions"])
        self.inst_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Duration & Passing Percentage row
        row1 = ctk.CTkFrame(sub, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 10))
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)

        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(col1, text="Duration (Minutes) *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.dur_entry = ctk.CTkEntry(col1, placeholder_text="30", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.dur_entry.insert(0, str(self.quiz_data.get("duration_minutes", 30)) if self.quiz_data else "30")
        self.dur_entry.pack(fill="x", pady=(2, 0))

        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(col2, text="Passing Marks (%) *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.pass_entry = ctk.CTkEntry(col2, placeholder_text="50", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.pass_entry.insert(0, str(self.quiz_data.get("passing_percentage", 50)) if self.quiz_data else "50")
        self.pass_entry.pack(fill="x", pady=(2, 0))

        # Max Attempts
        ctk.CTkLabel(sub, text="Max Attempts per Student (1-10)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 2))
        self.attempts_entry = ctk.CTkEntry(sub, placeholder_text="1", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.attempts_entry.insert(0, str(self.quiz_data.get("max_attempts", 1)) if self.quiz_data else "1")
        self.attempts_entry.pack(fill="x", padx=16, pady=(0, 14))

        # Access Control: Private (Code-Only) vs Public
        access_box = ctk.CTkFrame(sub, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        access_box.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(access_box, text="Quiz Audience & Access Control *", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x", padx=14, pady=(10, 4))
        is_pub = self.quiz_data.get("is_public", False) if self.quiz_data else False
        self.access_toggle = ctk.CTkSegmentedButton(
            access_box,
            values=["🔒 Private (Code Required)", "🌐 Public (Open to All)"],
            command=self._on_access_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=34,
        )
        self.access_toggle.set("🌐 Public (Open to All)" if is_pub else "🔒 Private (Code Required)")
        self.access_toggle.pack(fill="x", padx=14, pady=(0, 6))

        self.access_desc = ctk.CTkLabel(access_box, text="", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, wraplength=480, justify="left", anchor="w")
        self.access_desc.pack(fill="x", padx=14, pady=(0, 10))
        self._update_access_desc()

        # Result Release Control
        release_box = ctk.CTkFrame(sub, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        release_box.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(release_box, text="Result & Answer Key Release *", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x", padx=14, pady=(10, 4))
        rel_now = self.quiz_data.get("release_results_immediately", True) if self.quiz_data else True
        self.release_toggle = ctk.CTkSegmentedButton(
            release_box,
            values=["⚡ Release Immediately", "🔒 Hold Review Until Released"],
            command=self._on_release_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=34,
        )
        self.release_toggle.set("⚡ Release Immediately" if rel_now else "🔒 Hold Review Until Released")
        self.release_toggle.pack(fill="x", padx=14, pady=(0, 6))

        self.release_desc = ctk.CTkLabel(release_box, text="", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, wraplength=480, justify="left", anchor="w")
        self.release_desc.pack(fill="x", padx=14, pady=(0, 10))
        self._update_release_desc()

        self.error_label = ctk.CTkLabel(sub, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER, wraplength=480)
        self.error_label.pack(pady=4)

        # High-Contrast Action Buttons Row
        btn_row = ctk.CTkFrame(sub, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 14))
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
            height=40,
            command=self.destroy,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        save_btn_text = "Save Changes" if self.quiz_data else "Create Quiz"
        ctk.CTkButton(
            btn_row,
            text=save_btn_text,
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=40,
            command=self._handle_save_manual,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    # ------------------ Mode 2: AI Prompt Generator View ------------------
    def _render_ai_view(self):
        sub = self.content_subframe

        banner = ctk.CTkFrame(sub, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        banner.pack(fill="x", padx=16, pady=(4, 12))

        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(b_inner, text="🤖 TeachWise AI Quiz Author", font=Theme.FONT_BODY_BOLD, text_color=Theme.PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            b_inner,
            text="Enter any curriculum concept, topic, or lesson summary. TeachWise automatically generates questions, 4 distinct options, correct answers, and thorough explanations.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        # Prompt input
        ctk.CTkLabel(sub, text="Assessment Topic or Learning Prompt *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.ai_prompt_entry = ctk.CTkEntry(
            sub,
            placeholder_text="e.g. Python Object Oriented Programming (Classes, Inheritance, Polymorphism)",
            fg_color=Theme.BG_INPUT,
            border_color=Theme.BORDER_COLOR,
            height=40,
        )
        self.ai_prompt_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Controls row: question count & difficulty
        ctrl_row = ctk.CTkFrame(sub, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=16, pady=(0, 10))
        ctrl_row.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(ctrl_row, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(c1, text="Number of Questions", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.ai_count_seg = ctk.CTkSegmentedButton(c1, values=["3 Questions", "5 Questions", "10 Questions"], height=32)
        self.ai_count_seg.set("5 Questions")
        self.ai_count_seg.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(ctrl_row, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Difficulty Level", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.ai_diff_seg = ctk.CTkSegmentedButton(c2, values=["Easy", "Medium", "Hard"], height=32)
        self.ai_diff_seg.set("Medium")
        self.ai_diff_seg.pack(fill="x", pady=(2, 0))

        # Audience control
        aud_row = ctk.CTkFrame(sub, fg_color="transparent")
        aud_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(aud_row, text="Quiz Audience", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.ai_access_seg = ctk.CTkSegmentedButton(aud_row, values=["🔒 Private (Code Required)", "🌐 Public (Open to All)"], height=32)
        self.ai_access_seg.set("🔒 Private (Code Required)")
        self.ai_access_seg.pack(fill="x", pady=(2, 0))

        self.ai_status_label = ctk.CTkLabel(sub, text="", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, wraplength=520)
        self.ai_status_label.pack(pady=4)

        # Generate Button
        self.ai_gen_btn = ctk.CTkButton(
            sub,
            text="✨ Generate Quiz & Questions with AI",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=42,
            command=self._handle_ai_generate,
        )
        self.ai_gen_btn.pack(fill="x", padx=16, pady=(4, 12))

        # Preview Container
        self.ai_preview_frame = ctk.CTkFrame(sub, fg_color="transparent")
        self.ai_preview_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    # ------------------ Mode 3: File Import View ------------------
    def _render_file_view(self):
        sub = self.content_subframe

        banner = ctk.CTkFrame(sub, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        banner.pack(fill="x", padx=16, pady=(4, 12))

        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(b_inner, text="📁 Import Assessments from File", font=Theme.FONT_BODY_BOLD, text_color=Theme.SECONDARY).pack(anchor="w")
        ctk.CTkLabel(
            b_inner,
            text="Upload CSV spreadsheets, JSON files, or lecture notes (.txt, .md). TeachWise parses existing questions or synthesizes tests from study notes automatically.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        # File Select Button
        file_pick_row = ctk.CTkFrame(sub, fg_color=Theme.BG_MAIN, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        file_pick_row.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkButton(
            file_pick_row,
            text="📂 Select File from Computer...",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            height=36,
            command=self._pick_file,
        ).pack(side="left", padx=10, pady=10)

        self.file_status_label = ctk.CTkLabel(file_pick_row, text="No file selected yet (.csv, .json, .txt, .md)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w")
        self.file_status_label.pack(side="left", fill="x", expand=True, padx=8)

        # Or Paste Notes Box
        ctk.CTkLabel(sub, text="— OR Paste Document Notes Directly Below —", font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM, anchor="center").pack(fill="x", pady=(4, 6))
        self.file_paste_text = ctk.CTkTextbox(sub, height=110, fg_color=Theme.BG_INPUT, border_width=1, border_color=Theme.BORDER_COLOR)
        self.file_paste_text.pack(fill="x", padx=16, pady=(0, 10))

        # Question count & difficulty
        ctrl_row = ctk.CTkFrame(sub, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=16, pady=(0, 10))
        ctrl_row.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(ctrl_row, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(c1, text="Number of Questions", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.file_count_seg = ctk.CTkSegmentedButton(c1, values=["3 Questions", "5 Questions", "10 Questions"], height=32)
        self.file_count_seg.set("5 Questions")
        self.file_count_seg.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(ctrl_row, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Difficulty Level", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.file_diff_seg = ctk.CTkSegmentedButton(c2, values=["Easy", "Medium", "Hard"], height=32)
        self.file_diff_seg.set("Medium")
        self.file_diff_seg.pack(fill="x", pady=(2, 0))

        # Import action button
        self.file_import_btn = ctk.CTkButton(
            sub,
            text="⚡ Parse File & Create Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=42,
            command=self._handle_file_import,
        )
        self.file_import_btn.pack(fill="x", padx=16, pady=(4, 12))

    def _pick_file(self):
        f_path = filedialog.askopenfilename(
            title="Select Assessment File or Study Notes",
            filetypes=[
                ("Supported Formats", "*.csv;*.json;*.txt;*.md"),
                ("CSV Files", "*.csv"),
                ("JSON Files", "*.json"),
                ("Text & Notes", "*.txt;*.md"),
                ("All Files", "*.*"),
            ],
        )
        if f_path:
            self.imported_file_path = f_path
            filename = os.path.basename(f_path)
            try:
                with open(f_path, "r", encoding="utf-8", errors="replace") as f:
                    self.imported_file_content = f.read()
                f_size = len(self.imported_file_content)
                self.file_status_label.configure(
                    text=f"✓ {filename} ({round(f_size/1024, 1)} KB loaded)",
                    text_color=Theme.SUCCESS,
                )
            except Exception as e:
                self.file_status_label.configure(text=f"Error reading file: {str(e)}", text_color=Theme.DANGER)

    def _handle_file_import(self):
        content = self.imported_file_content
        filename = os.path.basename(self.imported_file_path) if self.imported_file_path else "Pasted_Notes.txt"

        if not content:
            # check paste textbox
            pasted = self.file_paste_text.get("1.0", "end").strip()
            if pasted:
                content = pasted
                filename = "Pasted_Notes.txt"

        if not content or len(content.strip()) < 10:
            messagebox.showwarning("No Content", "Please select a file or paste document notes into the box.")
            return

        cnt_str = self.file_count_seg.get().split()[0]
        num_q = int(cnt_str)
        diff = self.file_diff_seg.get().lower()

        self.file_import_btn.configure(state="disabled", text="Parsing document...")
        self.update_idletasks()

        ok, res = api_client.import_quiz_file(
            file_content=content,
            filename=filename,
            num_questions=num_q,
            difficulty=diff,
            save_directly=True,
        )
        self.file_import_btn.configure(state="normal", text="⚡ Parse File & Create Quiz")

        if ok and res:
            q_cnt = len(res.get("questions", []))
            title = res.get("title", "Assessment")
            code = res.get("join_code", "N/A")
            messagebox.showinfo(
                "Assessment Created Successfully",
                f"Quiz created from file!\n\nTitle: {title}\nQuestions: {q_cnt}\nJoin Code: {code}\n\nSaved to your workspace as a draft. Click 'Publish' when ready for students.",
            )
            self.destroy()
            if self.on_success:
                self.on_success()
        else:
            messagebox.showerror("Import Error", f"Failed to parse quiz from file: {res}")

    def _handle_ai_generate(self):
        prompt = self.ai_prompt_entry.get().strip()
        if not prompt or len(prompt) < 3:
            self.ai_status_label.configure(text="Please enter an assessment topic or learning prompt.", text_color=Theme.DANGER)
            return

        cnt_str = self.ai_count_seg.get().split()[0]
        num_q = int(cnt_str)
        diff = self.ai_diff_seg.get().lower()
        is_pub = "Public" in self.ai_access_seg.get()

        self.ai_gen_btn.configure(state="disabled", text="Synthesizing assessment questions with AI...")
        self.ai_status_label.configure(text="Formulating pedagogy, multiple-choice distractors, and explanations...", text_color=Theme.PRIMARY)
        self.update_idletasks()

        ok, res = api_client.generate_quiz_ai(
            prompt=prompt,
            num_questions=num_q,
            difficulty=diff,
            save_directly=False,
        )
        self.ai_gen_btn.configure(state="normal", text="✨ Generate Quiz & Questions with AI")

        if not ok or not res:
            self.ai_status_label.configure(text=f"AI generation notice: {res}", text_color=Theme.DANGER)
            return

        self.generated_quiz_preview = res
        self.ai_status_label.configure(text="✓ Assessment generated! Review preview below, then click Confirm & Save.", text_color=Theme.SUCCESS)
        self._display_ai_preview(res, is_pub)

    def _display_ai_preview(self, data, is_public_choice):
        for w in self.ai_preview_frame.winfo_children():
            w.destroy()

        card = ctk.CTkFrame(self.ai_preview_frame, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        card.pack(fill="both", expand=True, pady=6)

        header_box = ctk.CTkFrame(card, fg_color="transparent")
        header_box.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(header_box, text=f"Assessment Preview: {data['title']}", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")
        ctk.CTkLabel(header_box, text=f"Duration: {data.get('duration_minutes', 30)} Mins • Total Marks: {len(data.get('questions', []))} • Difficulty: {self.ai_diff_seg.get()}", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")

        # Questions preview list
        questions = data.get("questions", [])
        for i, q in enumerate(questions):
            q_box = ctk.CTkFrame(card, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            q_box.pack(fill="x", padx=10, pady=4)

            q_in = ctk.CTkFrame(q_box, fg_color="transparent")
            q_in.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(q_in, text=f"Q{i+1}. {q['question_text']}", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w", wraplength=480, justify="left").pack(fill="x")

            opts = [("A", q["option_a"]), ("B", q["option_b"]), ("C", q["option_c"]), ("D", q["option_d"])]
            for opt_char, opt_text in opts:
                is_correct = opt_char == q["correct_option"]
                lbl_color = Theme.SUCCESS if is_correct else Theme.TEXT_MUTED
                prefix = "✓ " if is_correct else "   "
                ctk.CTkLabel(q_in, text=f"{prefix}{opt_char}) {opt_text}", font=Theme.FONT_SMALL, text_color=lbl_color, anchor="w", wraplength=470, justify="left").pack(fill="x", padx=(12, 0), pady=1)

            if q.get("explanation"):
                ctk.CTkLabel(q_in, text=f"💡 Note: {q['explanation']}", font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM, anchor="w", wraplength=470, justify="left").pack(fill="x", pady=(4, 0))

        # Confirm Save Button
        save_btn = ctk.CTkButton(
            card,
            text="🚀 Confirm & Save Assessment to My Workspace",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=40,
            command=lambda: self._save_ai_generated_quiz(data, is_public_choice),
        )
        save_btn.pack(fill="x", padx=12, pady=12)

    def _save_ai_generated_quiz(self, data, is_public_choice):
        prompt = self.ai_prompt_entry.get().strip()
        cnt_str = self.ai_count_seg.get().split()[0]
        num_q = int(cnt_str)
        diff = self.ai_diff_seg.get().lower()

        ok, res = api_client.generate_quiz_ai(
            prompt=prompt,
            num_questions=num_q,
            difficulty=diff,
            save_directly=True,
        )
        if ok and res:
            q_cnt = len(res.get("questions", []))
            title = res.get("title", "Assessment")
            code = res.get("join_code", "N/A")
            messagebox.showinfo(
                "Assessment Created Successfully",
                f"Assessment '{title}' created!\n\nQuestions Added: {q_cnt}\nJoin Code: {code}\n\nSaved to your organizer workspace as a draft. Click 'Publish' whenever you are ready for students to take it.",
            )
            self.destroy()
            if self.on_success:
                self.on_success()
        else:
            messagebox.showerror("Save Error", f"Failed to persist generated quiz: {res}")

    def _on_access_change(self, _val):
        self._update_access_desc()

    def _update_access_desc(self):
        val = self.access_toggle.get()
        if "Private" in val:
            self.access_desc.configure(
                text="🔒 RESTRICTED (CODE ONLY): Hidden from general student dashboards. ONLY students who receive your private Join Code (QF-XXXX) can access and take this quiz.",
                text_color="#B45309",
            )
        else:
            self.access_desc.configure(
                text="🌐 PUBLIC (OPEN): This quiz will appear on the student dashboard catalog for any registered student to attempt.",
                text_color=Theme.TEXT_MUTED,
            )

    def _on_release_change(self, _val):
        self._update_release_desc()

    def _update_release_desc(self):
        val = self.release_toggle.get()
        if "Hold" in val:
            self.release_desc.configure(
                text="🔒 HELD: Students see their total score upon completion, but detailed question answers and solutions remain hidden until you release them.",
                text_color="#B45309",
            )
        else:
            self.release_desc.configure(
                text="⚡ IMMEDIATE: Students immediately see full question solutions, correct options, and explanations right after submission.",
                text_color=Theme.TEXT_MUTED,
            )

    def _handle_save_manual(self):
        title = self.title_entry.get().strip()
        desc = self.desc_entry.get().strip()
        inst = self.inst_entry.get().strip()
        dur_str = self.dur_entry.get().strip()
        pass_str = self.pass_entry.get().strip()
        attempts_str = self.attempts_entry.get().strip()

        if not title:
            self.error_label.configure(text="Quiz title is required.")
            return

        try:
            dur = int(dur_str)
            pass_pct = int(pass_str)
            max_att = int(attempts_str)
        except ValueError:
            self.error_label.configure(text="Duration, passing %, and max attempts must be integers.")
            return

        is_public_flag = "Public" in self.access_toggle.get()
        release_imm = "Immediate" in self.release_toggle.get()

        payload = {
            "title": title,
            "description": desc or None,
            "instructions": inst or None,
            "duration_minutes": dur,
            "passing_percentage": pass_pct,
            "max_attempts": max_att,
            "is_public": is_public_flag,
            "release_results_immediately": release_imm,
        }

        if self.quiz_data:
            ok, res = api_client.update_quiz(self.quiz_data["id"], payload)
        else:
            ok, res = api_client.create_quiz(payload)

        if ok:
            self.destroy()
            if self.on_success:
                self.on_success()
        else:
            self.error_label.configure(text=str(res))


class QuizReportDialog(ctk.CTkToplevel):
    """
    TeachWise Comprehensive Assessment & Learning Insights Portal:
    1. Overview & Attempts: metrics, rosters, scores, CSV export.
    2. Misconception Detector: distractor clustering, error rates, topic mastery.
    3. Teacher Action Center: data-driven next steps, student follow-ups.
    """
    def __init__(self, master, quiz_dict, on_refresh_parent=None):
        super().__init__(master)
        self.quiz = quiz_dict
        self.on_refresh_parent = on_refresh_parent
        self.report_data = None
        self.current_tab = "overview"

        self.title(f"Assessment & Learning Insights — {quiz_dict['title']}")
        self.geometry("860x700")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self._build_ui()
        self.load_report()

    def _build_ui(self):
        # Top Header Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(16, 8))

        t_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        t_box.pack(side="left")

        ctk.CTkLabel(t_box, text=self.quiz["title"], font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(
            t_box,
            text=f"Join Code: {self.quiz.get('join_code', 'N/A')} • Passing Threshold: {self.quiz['passing_percentage']}% • Subject: {self.quiz.get('subject', 'General')}",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        btn_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_box.pack(side="right")

        self.release_btn = ctk.CTkButton(
            btn_box,
            text="🔓 Release Results",
            font=Theme.FONT_SMALL,
            fg_color=Theme.SUCCESS,
            hover_color="#059669",
            height=32,
            command=self._handle_release,
        )
        self.release_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="📥 Export CSV",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=32,
            command=self._handle_export_csv,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="✕ Close",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F1F5F9",
            text_color="#1E293B",
            hover_color="#E2E8F0",
            border_width=1,
            border_color="#CBD5E1",
            height=32,
            command=self.destroy,
        ).pack(side="left")

        # Three-Tab Segmented Selector
        tab_box = ctk.CTkFrame(self, fg_color="transparent")
        tab_box.pack(fill="x", padx=20, pady=(4, 8))

        self.tab_selector = ctk.CTkSegmentedButton(
            tab_box,
            values=["📊 Overview & Attempts", "🧠 Misconception Detector", "⚡ Teacher Action Center"],
            command=self._on_tab_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_BODY_BOLD,
            height=36,
        )
        self.tab_selector.set("📊 Overview & Attempts")
        self.tab_selector.pack(fill="x")

        # Scrollable content area
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _on_tab_change(self, tab_name):
        if "Misconception" in tab_name:
            self.current_tab = "misconceptions"
        elif "Action" in tab_name:
            self.current_tab = "actions"
        else:
            self.current_tab = "overview"

        self._render_current_tab()

    def load_report(self):
        ok, data = api_client.get_quiz_report(self.quiz["id"])
        if not ok:
            messagebox.showerror("Error", f"Failed to load report: {data}")
            return

        self.report_data = data
        if data.get("results_released", True):
            self.release_btn.configure(state="disabled", text="✓ Results Released", fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_MUTED)
        else:
            self.release_btn.configure(state="normal", text="🔓 Release Results Now", fg_color=Theme.SUCCESS)

        self._render_current_tab()

    def _render_current_tab(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.report_data:
            ctk.CTkLabel(self.scroll, text="Loading evaluation report...", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(pady=40)
            return

        if self.current_tab == "misconceptions":
            self._render_misconceptions_tab()
        elif self.current_tab == "actions":
            self._render_action_center_tab()
        else:
            self._render_overview_tab()

    # ------------------ Tab 1: Overview & Attempts ------------------
    def _render_overview_tab(self):
        data = self.report_data

        # Metrics cards row
        stats_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        stats_row.pack(fill="x", padx=12, pady=12)
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        metric_vals = [
            ("Total Attempts", str(data.get("total_attempts", 0))),
            ("Unique Students", str(data.get("unique_participants", 0))),
            ("Average Score", f"{data.get('average_score', 0.0)}%"),
            ("Passing Rate", f"{data.get('pass_rate', data.get('pass_percentage', 0.0))}%"),
        ]
        for i, (lbl, val) in enumerate(metric_vals):
            card = ctk.CTkFrame(stats_row, fg_color=Theme.BG_MAIN, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            ctk.CTkLabel(card, text=lbl, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(padx=8, pady=(8, 2))
            ctk.CTkLabel(card, text=val, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(padx=8, pady=(0, 8))

        # Question accuracy section
        ctk.CTkLabel(self.scroll, text="Question Accuracy Breakdown", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=12, pady=(16, 6))
        q_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        q_frame.pack(fill="x", padx=12, pady=(0, 12))

        q_stats = data.get("question_stats", [])
        if not q_stats:
            ctk.CTkLabel(q_frame, text="No question performance recorded yet.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM).pack(pady=4)
        else:
            for idx, qs in enumerate(q_stats):
                row = ctk.CTkFrame(q_frame, fg_color=Theme.BG_MAIN, corner_radius=6, border_width=1, border_color=Theme.BORDER_COLOR)
                row.pack(fill="x", pady=3)
                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=10, pady=6)

                q_num = qs.get("order_index", idx + 1)
                ctk.CTkLabel(inner, text=f"Q{q_num}. {qs['question_text']}", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w", wraplength=480, justify="left").pack(side="left", fill="x", expand=True)

                acc = qs["accuracy_percentage"]
                badge_color = Theme.SUCCESS if acc >= 70 else Theme.WARNING if acc >= 50 else Theme.DANGER
                ctk.CTkLabel(inner, text=f"{acc}% Accuracy ({qs['correct_answers']}/{qs['total_answers']} correct)", font=Theme.FONT_BODY_BOLD, text_color=badge_color).pack(side="right")

        # Participant attempts table
        ctk.CTkLabel(self.scroll, text="Participant Attempts Roster", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=12, pady=(12, 6))
        att_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        att_frame.pack(fill="x", padx=12, pady=(0, 16))

        attempts = data.get("attempts", [])
        if not attempts:
            ctk.CTkLabel(att_frame, text="No student attempts recorded yet.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM).pack(pady=8)
        else:
            h_row = ctk.CTkFrame(att_frame, fg_color=Theme.BG_INPUT, corner_radius=4)
            h_row.pack(fill="x", pady=(0, 4))
            h_row.grid_columnconfigure((0, 1), weight=3)
            h_row.grid_columnconfigure((2, 3, 4), weight=2)

            ctk.CTkLabel(h_row, text="PARTICIPANT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="EMAIL", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="SCORE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="VERDICT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=8, pady=4, sticky="w")

            for a in attempts:
                a_row = ctk.CTkFrame(att_frame, fg_color="transparent")
                a_row.pack(fill="x", pady=2)
                a_row.grid_columnconfigure((0, 1), weight=3)
                a_row.grid_columnconfigure((2, 3, 4), weight=2)

                s_name = a.get("student_name") or a.get("participant_name", "Student")
                s_email = a.get("student_email") or a.get("participant_email", "N/A")
                ctk.CTkLabel(a_row, text=s_name, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=0, padx=8, sticky="w")
                ctk.CTkLabel(a_row, text=s_email, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, sticky="w")
                ctk.CTkLabel(a_row, text=f"{a['score_obtained']}/{a['total_marks']} ({a['percentage']}%)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=2, padx=8, sticky="w")

                v_text = "PASSED" if a["is_passed"] else "NEEDS PRACTICE"
                v_color = Theme.SUCCESS if a["is_passed"] else Theme.DANGER
                ctk.CTkLabel(a_row, text=v_text, font=Theme.FONT_SMALL, text_color=v_color, anchor="w").grid(row=0, column=3, padx=8, sticky="w")

                ctk.CTkLabel(a_row, text=a.get("status", "completed").upper(), font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM, anchor="w").grid(row=0, column=4, padx=8, sticky="w")

    # ------------------ Tab 2: Misconception Detector ------------------
    def _render_misconceptions_tab(self):
        data = self.report_data

        intro_banner = ctk.CTkFrame(self.scroll, fg_color=Theme.BG_MAIN, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        intro_banner.pack(fill="x", padx=12, pady=(12, 16))

        in_box = ctk.CTkFrame(intro_banner, fg_color="transparent")
        in_box.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(in_box, text="🧠 Automated Misconception & Distractor Detector", font=Theme.FONT_BODY_BOLD, text_color=Theme.PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            in_box,
            text="Statistical analysis identifies specific wrong answer choices that multiple students clustered around, highlighting underlying conceptual confusion rather than random guesses.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        # 1. Topic Mastery Breakdown
        ctk.CTkLabel(self.scroll, text="Topic & Objective Mastery Breakdown", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=12, pady=(0, 6))

        topics = data.get("topic_breakdown", [])
        if not topics:
            ctk.CTkLabel(self.scroll, text="No topic tags found on quiz questions.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM).pack(padx=12, pady=4)
        else:
            t_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            t_frame.pack(fill="x", padx=12, pady=(0, 14))

            for t in topics:
                t_card = ctk.CTkFrame(t_frame, fg_color=Theme.BG_MAIN, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
                t_card.pack(fill="x", pady=3)

                t_inner = ctk.CTkFrame(t_card, fg_color="transparent")
                t_inner.pack(fill="x", padx=12, pady=8)

                left_b = ctk.CTkFrame(t_inner, fg_color="transparent")
                left_b.pack(side="left")

                ctk.CTkLabel(left_b, text=f"📌 {t['topic']}", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(anchor="w")
                ctk.CTkLabel(left_b, text=f"{t['question_count']} question(s) • {t['total_answers']} answered", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")

                right_b = ctk.CTkFrame(t_inner, fg_color="transparent")
                right_b.pack(side="right")

                acc = t["accuracy_percentage"]
                acc_color = Theme.SUCCESS if acc >= 75 else Theme.WARNING if acc >= 50 else Theme.DANGER
                ctk.CTkLabel(right_b, text=f"{acc}% Mastery", font=Theme.FONT_BODY_BOLD, text_color=acc_color).pack(anchor="e")
                ctk.CTkLabel(right_b, text=t["status"], font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN).pack(anchor="e")

        # 2. Identified Misconceptions
        ctk.CTkLabel(self.scroll, text="Detected Concept Distractors & Misconceptions", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=12, pady=(6, 6))

        misconceptions = data.get("misconceptions", [])
        if not misconceptions:
            empty_card = ctk.CTkFrame(self.scroll, fg_color=Theme.BG_MAIN, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            empty_card.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(
                empty_card,
                text="✓ No significant student distractor clustering detected on this exam. Class demonstrated sound comprehension across tested concepts.",
                font=Theme.FONT_SMALL,
                text_color=Theme.SUCCESS,
                padx=16,
                pady=16,
            ).pack(fill="x")
        else:
            for m in misconceptions:
                m_card = ctk.CTkFrame(self.scroll, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color="#F59E0B")
                m_card.pack(fill="x", padx=12, pady=6)

                m_in = ctk.CTkFrame(m_card, fg_color="transparent")
                m_in.pack(fill="x", padx=14, pady=12)

                top_m = ctk.CTkFrame(m_in, fg_color="transparent")
                top_m.pack(fill="x")

                ctk.CTkLabel(top_m, text=f"⚠️ Topic: {m['topic']}", font=Theme.FONT_BODY_BOLD, text_color="#D97706").pack(side="left")
                ctk.CTkLabel(top_m, text=f"Class Accuracy: {m['accuracy_percentage']}%", font=Theme.FONT_SMALL, text_color=Theme.DANGER).pack(side="right")

                ctk.CTkLabel(m_in, text=m["question_text"], font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, anchor="w", wraplength=640, justify="left").pack(fill="x", pady=(6, 4))

                detail_frame = ctk.CTkFrame(m_in, fg_color=Theme.BG_CARD, corner_radius=6)
                detail_frame.pack(fill="x", pady=4)
                d_in = ctk.CTkFrame(detail_frame, fg_color="transparent")
                d_in.pack(fill="x", padx=10, pady=8)

                ctk.CTkLabel(d_in, text=f"Correct Answer: Option {m['correct_option']}", font=Theme.FONT_SMALL, text_color=Theme.SUCCESS).pack(anchor="w")
                ctk.CTkLabel(d_in, text=f"Common Distractor: Option {m['common_distractor']} ({m['distractor_percentage']}% of students selected this)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DANGER).pack(anchor="w", pady=(2, 0))
                ctk.CTkLabel(d_in, text=f"Pedagogical Context: {m['explanation']}", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))

                ctk.CTkLabel(m_in, text=f"💡 Suggested Next Step: {m['recommended_action']}", font=Theme.FONT_SMALL, text_color=Theme.PRIMARY, wraplength=640, justify="left").pack(anchor="w", pady=(6, 0))

    # ------------------ Tab 3: Teacher Action Center ------------------
    def _render_action_center_tab(self):
        data = self.report_data

        intro_banner = ctk.CTkFrame(self.scroll, fg_color=Theme.BG_MAIN, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        intro_banner.pack(fill="x", padx=12, pady=(12, 16))

        in_box = ctk.CTkFrame(intro_banner, fg_color="transparent")
        in_box.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(in_box, text="⚡ Teacher Action Center — Actionable Next Steps", font=Theme.FONT_BODY_BOLD, text_color=Theme.SECONDARY).pack(anchor="w")
        ctk.CTkLabel(
            in_box,
            text="TeachWise translates assessment results into tangible, non-generic instructional actions. Review the alerts below and complete targeted interventions.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        actions = data.get("recommended_actions", [])
        if not actions:
            ctk.CTkLabel(self.scroll, text="No immediate follow-up actions required.", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(pady=20)
            return

        for idx, act in enumerate(actions):
            priority = act.get("priority", "MEDIUM")
            border_c = Theme.DANGER if priority == "HIGH" else Theme.PRIMARY if priority == "MEDIUM" else Theme.BORDER_COLOR

            card = ctk.CTkFrame(self.scroll, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=border_c)
            card.pack(fill="x", padx=12, pady=6)

            card_in = ctk.CTkFrame(card, fg_color="transparent")
            card_in.pack(fill="x", padx=14, pady=12)

            top_row = ctk.CTkFrame(card_in, fg_color="transparent")
            top_row.pack(fill="x")

            p_color = Theme.DANGER if priority == "HIGH" else Theme.PRIMARY
            ctk.CTkLabel(top_row, text=f"[{priority} PRIORITY]  {act.get('category', 'Action')}", font=Theme.FONT_SMALL, text_color=p_color).pack(side="left")

            title_lbl = ctk.CTkLabel(card_in, text=act["title"], font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w")
            title_lbl.pack(fill="x", pady=(4, 2))

            desc_lbl = ctk.CTkLabel(card_in, text=act["description"], font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w", wraplength=560, justify="left")
            desc_lbl.pack(fill="x", pady=(0, 8))

            action_row = ctk.CTkFrame(card_in, fg_color="transparent")
            action_row.pack(fill="x")

            complete_btn = ctk.CTkButton(
                action_row,
                text="✓ Mark Action Completed",
                font=Theme.FONT_SMALL,
                fg_color="#F1F5F9",
                text_color="#1E293B",
                hover_color="#E2E8F0",
                border_width=1,
                border_color="#CBD5E1",
                height=30,
            )
            complete_btn.configure(command=lambda b=complete_btn, t=title_lbl: self._mark_action_done(b, t))
            complete_btn.pack(side="right")

    def _mark_action_done(self, btn, title_lbl):
        btn.configure(text="✓ Completed", state="disabled", fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_MUTED)
        title_lbl.configure(text_color=Theme.TEXT_MUTED)

    def _handle_release(self):
        ok, res = api_client.release_results(self.quiz["id"])
        if ok:
            messagebox.showinfo("Success", "Results and solutions have been released to all participants.")
            self.load_report()
            if self.on_refresh_parent:
                self.on_refresh_parent()
        else:
            messagebox.showerror("Error", f"Failed to release results: {res}")

    def _handle_export_csv(self):
        ok, csv_text = api_client.export_quiz_csv(self.quiz["id"])
        if not ok:
            messagebox.showerror("Error", f"Export failed: {csv_text}")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"quiz_report_{self.quiz['id']}_{self.quiz.get('join_code', 'export')}.csv",
            title="Save Quiz Report CSV",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                messagebox.showinfo("Export Successful", f"Quiz report saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not write file: {str(e)}")

            ctk.CTkLabel(h_row, text="PARTICIPANT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="EMAIL", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="SCORE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="VERDICT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(h_row, text="DATE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=8, pady=4, sticky="w")

            for a in attempts:
                a_row = ctk.CTkFrame(self.attempts_frame, fg_color="transparent")
                a_row.pack(fill="x", pady=2)
                a_row.grid_columnconfigure(0, weight=3)
                a_row.grid_columnconfigure(1, weight=3)
                a_row.grid_columnconfigure(2, weight=2)
                a_row.grid_columnconfigure(3, weight=2)
                a_row.grid_columnconfigure(4, weight=2)

                ctk.CTkLabel(a_row, text=a["participant_name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=0, padx=8, sticky="w")
                ctk.CTkLabel(a_row, text=a["participant_email"], font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, sticky="w")
                ctk.CTkLabel(a_row, text=f"{a['score_obtained']}/{a['total_marks']} ({a['percentage']}%)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=2, padx=8, sticky="w")

                v_text = "PASSED" if a["is_passed"] else "FAILED"
                v_color = Theme.SUCCESS if a["is_passed"] else Theme.DANGER
                ctk.CTkLabel(a_row, text=v_text, font=Theme.FONT_SMALL, text_color=v_color, anchor="w").grid(row=0, column=3, padx=8, sticky="w")

                date_s = a["start_time"][:10] if a.get("start_time") else "N/A"
                ctk.CTkLabel(a_row, text=date_s, font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM, anchor="w").grid(row=0, column=4, padx=8, sticky="w")

    def _handle_release(self):
        ok, res = api_client.release_results(self.quiz["id"])
        if ok:
            messagebox.showinfo("Success", "Results and solutions have been released to all participants.")
            self.load_report()
            if self.on_refresh_parent:
                self.on_refresh_parent()
        else:
            messagebox.showerror("Error", f"Failed to release results: {res}")

    def _handle_export_csv(self):
        ok, csv_text = api_client.export_quiz_csv(self.quiz["id"])
        if not ok:
            messagebox.showerror("Error", f"Export failed: {csv_text}")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"quiz_report_{self.quiz['id']}_{self.quiz.get('join_code', 'export')}.csv",
            title="Save Quiz Report CSV",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                messagebox.showinfo("Export Successful", f"Quiz report saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not write file: {str(e)}")


class OrganizerDashboardView(ctk.CTkFrame):
    def __init__(self, master, on_manage_questions, on_navigate_results=None):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.on_manage_questions = on_manage_questions
        self.on_navigate_results = on_navigate_results or (lambda: None)
        self.quizzes = []
        self.filter_mode = "All"

        self.pack(fill="both", expand=True)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_MAIN)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=16)

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # 1. Header Row
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Teacher Dashboard",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        today_str = datetime.now().strftime("%d %b, %Y")
        ctk.CTkLabel(
            title_box,
            text=f"Manage your quizzes, track student attempts, and view performance insights • {today_str}",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right Actions
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="🔄 Refresh",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            width=90,
            height=34,
            corner_radius=8,
            command=self.load_data,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="+ Create New Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color=Theme.TEXT_WHITE,
            height=34,
            corner_radius=8,
            command=self._open_create_quiz,
        ).pack(side="left")

        # Hero Teacher Banner (Modern Web SaaS Feel)
        t_banner = ctk.CTkFrame(self.scroll, fg_color="#1E1B4B", corner_radius=12)
        t_banner.pack(fill="x", pady=(0, 18))
        tb_inner = ctk.CTkFrame(t_banner, fg_color="transparent")
        tb_inner.pack(fill="both", expand=True, padx=20, pady=16)

        tb_left = ctk.CTkFrame(tb_inner, fg_color="transparent")
        tb_left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            tb_left,
            text="Welcome to Teacher Workspace & Analytics 👨‍🏫",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            tb_left,
            text="AI-assisted assessment generator is live. Generate rich multiple-choice quizzes or import lecture notes with 1 click.",
            font=Theme.FONT_SMALL,
            text_color="#C7D2FE",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        tb_right = ctk.CTkFrame(tb_inner, fg_color="transparent")
        tb_right.pack(side="right")

        ctk.CTkButton(
            tb_right,
            text="✨ Generate with AI",
            font=("Segoe UI", 11, "bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._open_create_quiz,
        ).pack(side="left")

        # 2. Top Row: 4 KPI Cards (Matching Bottom-Left Panel of Reference Image)
        self.stats_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=(0, 18))
        self.stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # Card 1: Total Quizzes (#8B5CF6)
        self.card_quizzes = StatCard(
            self.stats_row,
            title="Total Quizzes",
            value="0",
            icon="📝",
            badge_color=Theme.COLOR_TEACHERS,
            trend_text="All created quizzes",
            command=lambda: self._set_filter_and_focus("All"),
        )
        self.card_quizzes.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        # Card 2: Published (#10B981)
        self.card_pub = StatCard(
            self.stats_row,
            title="Published",
            value="0",
            icon="🌐",
            badge_color=Theme.COLOR_QUIZZES,
            trend_text="Live & accepting responses",
            command=lambda: self._set_filter_and_focus("🌐 Public"),
        )
        self.card_pub.grid(row=0, column=1, padx=4, sticky="nsew")

        # Card 3: Total Attempts (#F59E0B)
        self.card_att = StatCard(
            self.stats_row,
            title="Total Attempts",
            value="0",
            icon="🎯",
            badge_color=Theme.COLOR_ATTEMPTS,
            trend_text="Student submissions",
            command=self.on_navigate_results,
        )
        self.card_att.grid(row=0, column=2, padx=4, sticky="nsew")

        # Card 4: Avg Performance (#3B82F6)
        self.card_perf = StatCard(
            self.stats_row,
            title="Avg. Performance",
            value="0%",
            icon="📊",
            badge_color=Theme.COLOR_STUDENTS,
            trend_text="Average participant score",
            command=self.on_navigate_results,
        )
        self.card_perf.grid(row=0, column=3, padx=(6, 0), sticky="nsew")

        # 3. Middle Row: Performance Overview Double Bar Chart (Left) + Quick Actions (Right)
        mid_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mid_row.pack(fill="x", pady=(0, 18))
        mid_row.grid_columnconfigure(0, weight=65)
        mid_row.grid_columnconfigure(1, weight=35)

        # Left: Performance Overview Double Bar Chart Card
        perf_card = ctk.CTkFrame(
            mid_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        perf_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        p_header = ctk.CTkFrame(perf_card, fg_color="transparent")
        p_header.pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            p_header,
            text="Performance Overview",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        legend = ctk.CTkFrame(p_header, fg_color="transparent")
        legend.pack(side="right")
        ctk.CTkLabel(legend, text="● Average Score  ", font=Theme.FONT_SMALL, text_color=Theme.COLOR_AVERAGE).pack(side="left")
        ctk.CTkLabel(legend, text="● Pass Rate", font=Theme.FONT_SMALL, text_color=Theme.COLOR_QUIZZES).pack(side="left")

        self.bar_chart = PerformanceDoubleBarChart(
            perf_card,
            months=["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"],
            avg_scores=[65, 72, 68, 75, 70, 78, 82],
            pass_rates=[70, 78, 72, 80, 74, 85, 88],
            height=180,
        )
        self.bar_chart.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Right: Quick Actions Card
        qa_card = ctk.CTkFrame(
            mid_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        qa_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        qa_header = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_header.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            qa_header,
            text="Quick Actions",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        qa_inner = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_inner.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Action 1: + Create New Quiz (Vibrant filled button)
        ctk.CTkButton(
            qa_inner,
            text="➕  Create New Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=36,
            corner_radius=8,
            command=self._open_create_quiz,
        ).pack(fill="x", pady=(0, 8))

        # Action 2: View Submissions
        ctk.CTkButton(
            qa_inner,
            text="📋  View Submissions",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=36,
            corner_radius=8,
            command=self.on_navigate_results,
        ).pack(fill="x", pady=(0, 8))

        # Action 3: Manage My Quizzes
        ctk.CTkButton(
            qa_inner,
            text="📁  Manage My Quizzes",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=36,
            corner_radius=8,
            command=lambda: self._set_filter_and_focus("All"),
        ).pack(fill="x", pady=(0, 8))

        # Action 4: Export Reports
        ctk.CTkButton(
            qa_inner,
            text="📥  Export Reports (CSV)",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.COLOR_QUIZZES,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=36,
            corner_radius=8,
            command=self._export_first_available_report,
        ).pack(fill="x")

        # 4. Bottom Row: My Quizzes (Left) + Recent Activity (Right)
        bottom_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bottom_row.pack(fill="both", expand=True)
        bottom_row.grid_columnconfigure(0, weight=65)
        bottom_row.grid_columnconfigure(1, weight=35)

        # Left: My Quizzes Card
        self.quizzes_card = ctk.CTkFrame(
            bottom_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        self.quizzes_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        q_header = ctk.CTkFrame(self.quizzes_card, fg_color="transparent")
        q_header.pack(fill="x", padx=18, pady=(16, 12))

        ctk.CTkLabel(q_header, text="My Quizzes", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")

        # Filter Tabs
        self.filter_buttons = ctk.CTkSegmentedButton(
            q_header,
            values=["All", "🔒 Private (Code Required)", "🌐 Public", "Drafts"],
            command=self._on_filter_changed,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_MAIN,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=30,
        )
        self.filter_buttons.set("All")
        self.filter_buttons.pack(side="right")

        self.quizzes_container = ctk.CTkFrame(self.quizzes_card, fg_color="transparent")
        self.quizzes_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Right: Recent Activity Card
        act_card = ctk.CTkFrame(
            bottom_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        act_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        a_header = ctk.CTkFrame(act_card, fg_color="transparent")
        a_header.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(a_header, text="Recent Activity", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")

        self.activity_feed_frame = ctk.CTkFrame(act_card, fg_color="transparent")
        self.activity_feed_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # 5. Row 5: Teacher Action Center & Misconception Insights (Scrollable Web App Depth)
        action_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        action_row.pack(fill="x", pady=(18, 0))
        action_row.grid_columnconfigure(0, weight=65)
        action_row.grid_columnconfigure(1, weight=35)

        # Left: Action Center Recommendations
        rec_card = ctk.CTkFrame(action_row, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        rec_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        r_hdr = ctk.CTkFrame(rec_card, fg_color="transparent")
        r_hdr.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(r_hdr, text="⚡ Teacher Action Center & Misconception Insights", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")

        r_inner = ctk.CTkFrame(rec_card, fg_color="transparent")
        r_inner.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        recs = [
            ("🚨", "Clarify Question 3 (Distractor clustering detected: 42% selected option B over A)", Theme.COLOR_ATTEMPTS),
            ("⚠️", "Schedule 15-minute quick revision on Python OOP & Polymorphism concepts", Theme.COLOR_STUDENTS),
            ("✅", "3 participants scored 100% on Data Structures — ready for advanced module", Theme.COLOR_QUIZZES),
        ]
        for icon, text_msg, color in recs:
            box = ctk.CTkFrame(r_inner, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            box.pack(fill="x", pady=3)
            b_in = ctk.CTkFrame(box, fg_color="transparent")
            b_in.pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(b_in, text=icon, font=("Segoe UI", 12)).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(b_in, text=text_msg, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w", justify="left").pack(side="left", fill="x", expand=True)

        # Right: Curriculum Milestones Card
        mile_card = ctk.CTkFrame(action_row, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        mile_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        m_hdr = ctk.CTkFrame(mile_card, fg_color="transparent")
        m_hdr.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(m_hdr, text="Academic Schedule", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")

        m_inner = ctk.CTkFrame(mile_card, fg_color="transparent")
        m_inner.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        milestones = [
            ("📅 Oct 25", "Python Midterm Test Window closes"),
            ("📅 Oct 28", "Release held quiz results to students"),
            ("📅 Nov 02", "New curriculum assessment publish date"),
        ]
        for date_txt, desc_txt in milestones:
            m_box = ctk.CTkFrame(m_inner, fg_color="transparent")
            m_box.pack(fill="x", pady=4)
            ctk.CTkLabel(m_box, text=date_txt, font=Theme.FONT_BODY_BOLD, text_color=Theme.COLOR_TEACHERS).pack(anchor="w")
            ctk.CTkLabel(m_box, text=desc_txt, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w")

        # 6. Row 6: SaaS Platform Footer
        footer = ctk.CTkFrame(self.scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(24, 12))
        f_inner = ctk.CTkFrame(footer, fg_color="transparent")
        f_inner.pack(anchor="center")
        ctk.CTkLabel(
            f_inner,
            text="QuizFlow v2.4 Enterprise Assessment Suite  •  Teacher Pedagogy Engine  •  All Systems Secure & Operational",
            font=("Segoe UI", 9),
            text_color="#94A3B8",
        ).pack()

    def _set_filter_and_focus(self, filter_name: str):
        self.filter_buttons.set(filter_name)
        self.filter_mode = filter_name
        self._render_quizzes_list()

    def _export_first_available_report(self):
        if not self.quizzes:
            messagebox.showinfo("Export", "No quizzes available to export.")
            return
        first_q = self.quizzes[0]
        QuizReportDialog(self, first_q, on_refresh_parent=self.load_data)

    def on_search(self, query: str):
        """Filters my quizzes by title or join code."""
        q_lower = query.lower()
        filtered = [
            q for q in self.quizzes
            if q_lower in q.get("title", "").lower() or q_lower in q.get("join_code", "").lower()
        ]
        self._render_quizzes_custom(filtered)

    def _on_filter_changed(self, value):
        self.filter_mode = value
        self._render_quizzes_list()

    def _open_create_quiz(self):
        CreateOrEditQuizDialog(self, on_success=self.load_data)

    def load_data(self):
        # 1. Fetch Organizer Stats
        ok_stats, stats = api_client.get_organizer_stats()
        if ok_stats and stats:
            tot = stats.get("total_quizzes", 0)
            pub = stats.get("published_quizzes", 0)
            self.card_quizzes.set_value(str(tot), f"{pub} published")
            self.card_pub.set_value(str(pub), "Active & taking responses")
            self.card_att.set_value(str(stats.get("total_attempts", 0)), "Student submissions")
            avg_s = stats.get("average_score", 0.0)
            self.card_perf.set_value(f"{avg_s}%", "Average participant score")

        # 2. Fetch Organizer Quizzes
        ok_q, quizzes = api_client.get_organizer_quizzes()
        self.quizzes = quizzes if (ok_q and quizzes) else []
        self._render_quizzes_list()

        # 3. Render Activity Feed
        self._render_activity_feed()

    def _render_activity_feed(self):
        for w in self.activity_feed_frame.winfo_children():
            w.destroy()

        activities = [
            ("●", "3 new participants submitted test", "12m ago", Theme.COLOR_STUDENTS),
            ("●", "Restricted quiz join code shared", "1h ago", Theme.COLOR_TEACHERS),
            ("●", "Misconception analytics updated", "3h ago", Theme.COLOR_QUIZZES),
            ("●", "Gradebook export downloaded as CSV", "Yesterday", Theme.COLOR_ATTEMPTS),
        ]

        for dot, desc, time_str, color in activities:
            item = ctk.CTkFrame(self.activity_feed_frame, fg_color="transparent")
            item.pack(fill="x", pady=4)

            ctk.CTkLabel(item, text=dot, font=("Segoe UI", 10), text_color=color).pack(side="left", padx=(0, 6))
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(info, text=desc, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=time_str, font=("Segoe UI", 8), text_color=Theme.TEXT_DIM, anchor="w").pack(fill="x")

    def _render_quizzes_list(self):
        filtered = []
        for q in self.quizzes:
            is_pub = q.get("is_published", False)
            is_public_flag = q.get("is_public", True)

            if self.filter_mode == "🔒 Private (Code Required)" and is_public_flag:
                continue
            if self.filter_mode == "🌐 Public" and not is_public_flag:
                continue
            if self.filter_mode == "Drafts" and is_pub:
                continue
            filtered.append(q)

        self._render_quizzes_custom(filtered)

    def _render_quizzes_custom(self, quiz_list):
        for w in self.quizzes_container.winfo_children():
            w.destroy()

        if not quiz_list:
            ctk.CTkLabel(
                self.quizzes_container,
                text="No quizzes found matching the selected criteria.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=30)
            return

        for q in quiz_list:
            self._render_quiz_card(q)

    def _copy_join_code(self, code: str):
        self.clipboard_clear()
        self.clipboard_append(code)
        messagebox.showinfo("Join Code Copied", f"Code '{code}' copied to clipboard!\nShare this code with your students to grant private access.")

    def _render_quiz_card(self, q):
        card = ctk.CTkFrame(self.quizzes_container, fg_color=Theme.BG_MAIN, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Left Column: Info & Badges
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        # Top row: Title + Join Code badge + Status badge
        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(top_row, text=q["title"], font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN, anchor="w").pack(side="left")

        # Join Code Pill + 1-Click Copy
        join_code = q.get("join_code", "N/A")
        code_box = ctk.CTkFrame(top_row, fg_color=Theme.PRIMARY_LIGHT, corner_radius=6)
        code_box.pack(side="left", padx=(10, 6))

        ctk.CTkLabel(
            code_box,
            text=f" 🔑 {join_code} ",
            font=Theme.FONT_SMALL,
            text_color=Theme.PRIMARY,
        ).pack(side="left", padx=(4, 2))

        ctk.CTkButton(
            code_box,
            text="📋 Copy",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            width=50,
            height=20,
            corner_radius=4,
            command=lambda c=join_code: self._copy_join_code(c),
        ).pack(side="left", padx=(0, 4), pady=2)

        # Public vs Restricted Private Badge
        is_pub_disc = q.get("is_public", True)
        if is_pub_disc:
            disc_text = "🌐 PUBLIC"
            disc_bg = Theme.BG_INPUT
            disc_fg = Theme.TEXT_MUTED
        else:
            disc_text = "🔒 PRIVATE (CODE-ONLY)"
            disc_bg = "#FEF3C7"
            disc_fg = "#92400E"

        ctk.CTkLabel(
            top_row,
            text=f" {disc_text} ",
            font=Theme.FONT_SMALL,
            text_color=disc_fg,
            fg_color=disc_bg,
            corner_radius=4,
        ).pack(side="left", padx=4)

        # Published / Draft status
        is_pub = q.get("is_published", False)
        status_bg = Theme.SUCCESS_BG if is_pub else Theme.BG_INPUT
        status_fg = Theme.SUCCESS if is_pub else Theme.TEXT_MUTED
        status_text = "PUBLISHED" if is_pub else "DRAFT"

        ctk.CTkLabel(
            top_row,
            text=f" {status_text} ",
            font=Theme.FONT_SMALL,
            text_color=status_fg,
            fg_color=status_bg,
            corner_radius=4,
        ).pack(side="left", padx=4)

        # Description / Access Note
        desc_text = q.get("description") or "No description provided."
        if not is_pub_disc:
            desc_text += " • (Restricted test: only participants with join code can take it)"
        ctk.CTkLabel(left, text=desc_text, font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, anchor="w", wraplength=480).pack(fill="x", pady=(4, 6))

        # Metadata row
        meta_row = ctk.CTkFrame(left, fg_color="transparent")
        meta_row.pack(fill="x")

        badges = [
            f"⏱ {q.get('duration_minutes', 30)} min",
            f"📝 {q.get('question_count', 0)} questions",
            f"🎯 {q.get('total_marks', 0)} marks",
            f"🏆 {q.get('passing_percentage', 50)}% pass",
        ]
        for b in badges:
            ctk.CTkLabel(
                meta_row,
                text=b,
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MAIN,
                fg_color=Theme.BG_INPUT,
                corner_radius=4,
                padx=6,
                pady=2,
            ).pack(side="left", padx=(0, 6))

        # Right Column: Action Buttons
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right", fill="y", padx=(14, 0))

        # 1. Manage Questions
        ctk.CTkButton(
            actions,
            text="Manage Questions",
            font=Theme.FONT_SMALL,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color="#FFFFFF",
            width=135,
            height=28,
            command=lambda q_obj=q: self.on_manage_questions(q_obj),
        ).pack(pady=(0, 4))

        # 2. View Report & Export CSV
        ctk.CTkButton(
            actions,
            text="📊 Report & CSV",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            width=135,
            height=28,
            command=lambda q_obj=q: QuizReportDialog(self, q_obj, on_refresh_parent=self.load_data),
        ).pack(pady=(0, 4))

        # 3. Publish / Unpublish
        pub_btn_text = "Unpublish" if is_pub else "Publish Quiz"
        pub_btn_color = Theme.WARNING if is_pub else Theme.SUCCESS
        ctk.CTkButton(
            actions,
            text=pub_btn_text,
            font=Theme.FONT_SMALL,
            fg_color=pub_btn_color,
            text_color="#FFFFFF",
            width=135,
            height=28,
            command=lambda q_id=q["id"], pub=is_pub: self._toggle_publish(q_id, pub),
        ).pack(pady=(0, 4))

        # 4. Delete
        ctk.CTkButton(
            actions,
            text="Delete",
            font=Theme.FONT_SMALL,
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            text_color="#FFFFFF",
            width=135,
            height=28,
            command=lambda q_id=q["id"]: self._delete_quiz(q_id),
        ).pack()

    def _toggle_publish(self, quiz_id: int, is_currently_published: bool):
        if is_currently_published:
            ok, res = api_client.unpublish_quiz(quiz_id)
        else:
            ok, res = api_client.publish_quiz(quiz_id)

        if ok:
            self.load_data()
        else:
            messagebox.showerror("Error", f"Could not update quiz status: {res}")

    def _delete_quiz(self, quiz_id: int):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this quiz? All questions and attempts will be removed."):
            ok, res = api_client.delete_quiz(quiz_id)
            if ok:
                self.load_data()
            else:
                messagebox.showerror("Error", f"Failed to delete quiz: {res}")
