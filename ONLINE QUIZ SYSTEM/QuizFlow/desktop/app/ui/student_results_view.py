"""
Student Results View - Dedicated Exam Results & History Database.
Provides score breakdown, pass/fail filters, search, and answer review actions.
"""
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client


class StudentResultsView(ctk.CTkFrame):
    def __init__(self, master, student_user, on_view_result):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.user = student_user
        self.on_view_result = on_view_result
        self.all_history = []
        self.status_filter = "All"
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
            text="My Exam Results & Performance History",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Comprehensive record of all your completed quizzes, question reviews, and score reports.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right Action Button
        ctk.CTkButton(
            header,
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
        ).pack(side="right")

        # 2. Performance Summary Cards Row
        self.summary_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.summary_row.pack(fill="x", pady=(0, 18))
        self.summary_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="summary_cards")

        # Card 1: Completed
        self.c1 = self._create_mini_card(self.summary_row, 0, "Exams Attempted", "0", "Total tests taken", Theme.COLOR_STUDENTS)
        # Card 2: Passed
        self.c2 = self._create_mini_card(self.summary_row, 1, "Passed Assessments", "0", "Scored above threshold", Theme.COLOR_QUIZZES)
        # Card 3: Needs Review
        self.c3 = self._create_mini_card(self.summary_row, 2, "Needs Practice", "0", "Below pass threshold", Theme.COLOR_ATTEMPTS)
        # Card 4: Average Score
        self.c4 = self._create_mini_card(self.summary_row, 3, "Average Accuracy", "0%", "Cohort average score", Theme.COLOR_TEACHERS)

        # 3. Filter & Search Bar
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
            placeholder_text="🔍 Search results by quiz title...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            border_width=0,
            height=36,
        )
        self.search_entry.pack(fill="x", padx=8)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Status Filter Tabs
        self.status_seg = ctk.CTkSegmentedButton(
            fc_inner,
            values=["All Results", "✅ Passed Only", "⚠️ Needs Practice"],
            command=self._on_status_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_INPUT,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=34,
        )
        self.status_seg.set("All Results")
        self.status_seg.pack(side="right")

        # 4. Results Table Card
        table_card = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        table_card.pack(fill="both", expand=True, pady=(0, 20))

        # Table Column Headers
        th = ctk.CTkFrame(table_card, fg_color="#F8FAFC", corner_radius=6, height=36)
        th.pack(fill="x", padx=16, pady=(16, 8))
        th.grid_columnconfigure(0, weight=4)
        th.grid_columnconfigure(1, weight=2)
        th.grid_columnconfigure(2, weight=2)
        th.grid_columnconfigure(3, weight=2)
        th.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(th, text="ASSESSMENT QUIZ", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="DATE COMPLETED", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="SCORE / MARKS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="ACTIONS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=12, pady=8, sticky="w")

        self.table_body = ctk.CTkFrame(table_card, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _create_mini_card(self, parent, col, title, default_val, subtitle, color):
        card = ctk.CTkFrame(parent, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        card.grid(row=0, column=col, padx=4 if 0 < col < 3 else (0 if col == 0 else (4, 0)), sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(inner, text=title, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=default_val, font=("Segoe UI", 20, "bold"), text_color=Theme.TEXT_MAIN, anchor="w")
        val_lbl.pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(inner, text=subtitle, font=("Segoe UI", 8), text_color=color, anchor="w").pack(anchor="w")
        return val_lbl

    def _on_search_key(self, event=None):
        self.search_query = self.search_entry.get().strip().lower()
        self._filter_and_render()

    def _on_status_change(self, value):
        self.status_filter = value
        self._filter_and_render()

    def load_data(self):
        ok, history = api_client.get_my_history()
        self.all_history = history if (ok and history) else []

        # Update Summary Cards
        tot = len(self.all_history)
        passed = sum(1 for h in self.all_history if h.get("is_passed", False))
        failed = tot - passed
        avg_score = int(sum(h.get("percentage", 0) for h in self.all_history) / tot) if tot > 0 else 0

        self.c1.configure(text=str(tot))
        self.c2.configure(text=str(passed))
        self.c3.configure(text=str(failed))
        self.c4.configure(text=f"{avg_score}%")

        self._filter_and_render()

    def _filter_and_render(self):
        for w in self.table_body.winfo_children():
            w.destroy()

        filtered = []
        for h in self.all_history:
            is_pass = h.get("is_passed", False)
            if self.status_filter == "✅ Passed Only" and not is_pass:
                continue
            if self.status_filter == "⚠️ Needs Practice" and is_pass:
                continue
            if self.search_query:
                t = h.get("quiz_title", "").lower()
                if self.search_query not in t:
                    continue
            filtered.append(h)

        if not filtered:
            ctk.CTkLabel(
                self.table_body,
                text="No examination results found matching the selected filter.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=36)
            return

        for idx, h in enumerate(filtered):
            row = ctk.CTkFrame(
                self.table_body,
                fg_color=Theme.BG_CARD if idx % 2 == 0 else "#FAFAFA",
                corner_radius=6,
            )
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(0, weight=4)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)

            # Quiz Title + Icon
            t_box = ctk.CTkFrame(row, fg_color="transparent")
            t_box.grid(row=0, column=0, padx=12, pady=10, sticky="w")
            ctk.CTkLabel(t_box, text="📝", font=("Segoe UI", 12)).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(t_box, text=h.get("quiz_title", "Assessment"), font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left")

            # Date
            d_str = str(h.get("completed_at", "Recent"))
            if "T" in d_str:
                d_str = d_str.split("T")[0]
            ctk.CTkLabel(row, text=d_str, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=12, pady=10, sticky="w")

            # Score & Percentage
            pct = h.get("percentage", 0)
            score_txt = f"{pct}%  ({h.get('score_obtained', 0)} / {h.get('total_marks', 0)})"
            ctk.CTkLabel(row, text=score_txt, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=2, padx=12, pady=10, sticky="w")

            # Status Badge Pill
            is_pass = h.get("is_passed", False)
            badge_bg = Theme.SUCCESS_LIGHT if is_pass else Theme.DANGER_LIGHT
            badge_fg = Theme.SUCCESS if is_pass else Theme.DANGER
            badge_text = "PASSED" if is_pass else "NEEDS REVIEW"

            ctk.CTkLabel(
                row,
                text=f" {badge_text} ",
                font=Theme.FONT_SMALL,
                text_color=badge_fg,
                fg_color=badge_bg,
                corner_radius=4,
            ).grid(row=0, column=3, padx=12, pady=10, sticky="w")

            # Action: Review Answers
            ctk.CTkButton(
                row,
                text="Review Solutions →",
                font=Theme.FONT_SMALL,
                fg_color=Theme.PRIMARY_LIGHT,
                hover_color=Theme.BORDER_COLOR,
                text_color=Theme.PRIMARY,
                height=28,
                corner_radius=6,
                command=lambda a_id=h["attempt_id"]: self.on_view_result(a_id),
            ).grid(row=0, column=4, padx=12, pady=10, sticky="w")

