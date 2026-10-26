"""
Student Quizzes View - Dedicated Available Assessments & Exam Catalog.
Provides rich quiz discovery, category filters, private join code entry, and start assessment actions.
"""
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client


class StudentQuizzesView(ctk.CTkFrame):
    def __init__(self, master, student_user, on_start_quiz):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.user = student_user
        self.on_start_quiz = on_start_quiz
        self.all_quizzes = []
        self.category_filter = "All"
        self.search_query = ""

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
            text="Exams & Quizzes Catalog",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Explore active assessments, unlock private teacher tests, and test your knowledge.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right Action Buttons
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
            text="🔑  Enter Join Code",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._open_join_code_dialog,
        ).pack(side="left")

        # 2. Search & Category Filter Bar
        filter_card = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        filter_card.pack(fill="x", pady=(0, 16))

        fc_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        fc_inner.pack(fill="x", padx=16, pady=12)

        # Search Entry
        search_box = ctk.CTkFrame(fc_inner, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Search quizzes by title, subject, or join code...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            border_width=0,
            height=36,
        )
        self.search_entry.pack(fill="x", padx=8)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Category Filter Pills
        self.category_seg = ctk.CTkSegmentedButton(
            fc_inner,
            values=["All", "Computer Science", "Mathematics", "Science", "General"],
            command=self._on_category_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_INPUT,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=34,
        )
        self.category_seg.set("All")
        self.category_seg.pack(side="right")

        # 3. Main Quizzes Grid Container
        self.grid_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_container.pack(fill="both", expand=True, pady=(0, 20))

        # 4. Private Access Callout Card
        private_card = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        private_card.pack(fill="x", pady=(0, 20))

        pc_inner = ctk.CTkFrame(private_card, fg_color="transparent")
        pc_inner.pack(fill="x", padx=20, pady=16)

        left_p = ctk.CTkFrame(pc_inner, fg_color="transparent")
        left_p.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            left_p,
            text="🔒 Private Classroom Tests",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_p,
            text="Has your teacher given you a private examination code? Unlock restricted assessments instantly.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            pc_inner,
            text="🔑 Unlock with Code",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.COLOR_TEACHERS,
            hover_color="#7C3AED",
            text_color="#FFFFFF",
            height=36,
            corner_radius=8,
            command=self._open_join_code_dialog,
        ).pack(side="right")

    def _on_search_key(self, event=None):
        self.search_query = self.search_entry.get().strip().lower()
        self._filter_and_render()

    def _on_category_change(self, value):
        self.category_filter = value
        self._filter_and_render()

    def load_data(self):
        ok, quizzes = api_client.get_published_quizzes()
        self.all_quizzes = quizzes if (ok and quizzes) else []
        self._filter_and_render()

    def _filter_and_render(self):
        for w in self.grid_container.winfo_children():
            w.destroy()

        filtered = []
        for q in self.all_quizzes:
            # Category filter
            subj = q.get("subject", "General")
            if self.category_filter != "All" and subj.lower() != self.category_filter.lower():
                continue
            # Search query filter
            if self.search_query:
                t = q.get("title", "").lower()
                d = q.get("description", "").lower()
                c = q.get("join_code", "").lower()
                if self.search_query not in t and self.search_query not in d and self.search_query not in c:
                    continue
            filtered.append(q)

        if not filtered:
            empty_box = ctk.CTkFrame(self.grid_container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
            empty_box.pack(fill="x", pady=20)
            ctk.CTkLabel(
                empty_box,
                text="No assessments found matching the selected filter or search.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=40)
            return

        # Render quiz cards
        for q in filtered:
            self._render_quiz_card(q)

    def _render_quiz_card(self, q):
        card = ctk.CTkFrame(
            self.grid_container,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Left Info
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(fill="x")

        # Title
        ctk.CTkLabel(
            top_row,
            text=q.get("title", "Assessment"),
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
        ).pack(side="left")

        # Subject pill
        subj = q.get("subject", "General")
        ctk.CTkLabel(
            top_row,
            text=f" {subj} ",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY_LIGHT,
            text_color=Theme.PRIMARY,
            corner_radius=6,
        ).pack(side="left", padx=8)

        # Join Code Pill
        jcode = q.get("join_code", "N/A")
        ctk.CTkLabel(
            top_row,
            text=f" CODE: {jcode} ",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_INPUT,
            text_color=Theme.TEXT_MUTED,
            corner_radius=6,
        ).pack(side="left", padx=2)

        # Description
        desc = q.get("description") or "Complete this assessment to evaluate curriculum understanding."
        ctk.CTkLabel(
            left,
            text=desc,
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
            wraplength=560,
        ).pack(fill="x", pady=(4, 8))

        # Metadata badges row
        meta_row = ctk.CTkFrame(left, fg_color="transparent")
        meta_row.pack(fill="x")

        badges = [
            f"⏱ {q.get('duration_minutes', 30)} Minutes",
            f"📝 {q.get('question_count', 0)} Questions",
            f"🎯 {q.get('total_marks', 0)} Total Marks",
            f"🏆 Passing Score: {q.get('passing_percentage', 50)}%",
        ]
        for b in badges:
            ctk.CTkLabel(
                meta_row,
                text=b,
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MAIN,
                fg_color=Theme.BG_INPUT,
                corner_radius=4,
                padx=8,
                pady=2,
            ).pack(side="left", padx=(0, 8))

        # Right Action Button
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", fill="y", padx=(16, 0))

        ctk.CTkButton(
            right,
            text="Start Assessment →",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.COLOR_QUIZZES,
            hover_color="#059669",
            text_color="#FFFFFF",
            width=150,
            height=38,
            corner_radius=8,
            command=lambda q_id=q["id"]: self.on_start_quiz(q_id),
        ).pack(expand=True)

    def _open_join_code_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Join Private Quiz")
        dialog.geometry("400x280")
        dialog.configure(fg_color=Theme.BG_CARD)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Enter Quiz Join Code", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(20, 6))
        ctk.CTkLabel(dialog, text="Provided by your teacher (e.g. QF-A1B2)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(0, 12))

        code_entry = ctk.CTkEntry(dialog, placeholder_text="QF-XXXX", width=240, height=40, font=("Segoe UI", 16, "bold"), justify="center")
        code_entry.pack(pady=(0, 8))
        code_entry.focus()

        err_lbl = ctk.CTkLabel(dialog, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER, wraplength=340)
        err_lbl.pack(pady=(0, 8))

        def handle_join():
            code = code_entry.get().strip().upper()
            if not code:
                err_lbl.configure(text="Please enter a join code.")
                return
            join_btn.configure(state="disabled", text="Verifying...")
            ok, res = api_client.join_quiz_by_code(code)
            join_btn.configure(state="normal", text="Join & Start Quiz")
            if ok:
                dialog.destroy()
                self.on_start_quiz(res["id"])
            else:
                err_lbl.configure(text=str(res))

        code_entry.bind("<Return>", lambda _: handle_join())

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(6, 16))
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
            height=36,
            command=dialog.destroy,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        join_btn = ctk.CTkButton(
            btn_row,
            text="Join Quiz →",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=36,
            command=handle_join,
        )
        join_btn.grid(row=0, column=1, padx=(6, 0), sticky="ew")

