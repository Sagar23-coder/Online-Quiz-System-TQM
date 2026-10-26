"""
Organizer Results View - Dedicated Teacher Submissions & Gradebook Workspace.
Provides gradebook audit table, pass/fail status filters, search, and CSV export.
"""
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client


class OrganizerResultsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.submissions = []
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
            text="Student Submissions & Exam Gradebook",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Review participant scores, evaluate pass/fail criteria, and export grade logs to CSV.",
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
            text="📥  Export CSV",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.COLOR_QUIZZES,
            hover_color="#059669",
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self._export_csv,
        ).pack(side="left")

        # 2. Metric Summary Cards
        self.summary_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.summary_row.pack(fill="x", pady=(0, 18))
        self.summary_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="sub_metrics")

        self.c_tot = self._create_card(self.summary_row, 0, "Total Submissions", "0", "Student exam attempts", Theme.COLOR_ATTEMPTS)
        self.c_pass = self._create_card(self.summary_row, 1, "Passed Submissions", "0", "Met pass criteria", Theme.COLOR_QUIZZES)
        self.c_fail = self._create_card(self.summary_row, 2, "Failed Submissions", "0", "Below threshold", Theme.DANGER)
        self.c_avg = self._create_card(self.summary_row, 3, "Average Score", "0%", "Class average accuracy", Theme.COLOR_STUDENTS)

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
            placeholder_text="🔍 Search submissions by student name or quiz title...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            border_width=0,
            height=36,
        )
        self.search_entry.pack(fill="x", padx=8)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Status Tabs
        self.status_seg = ctk.CTkSegmentedButton(
            fc_inner,
            values=["All Submissions", "Passed Only", "Failed Only"],
            command=self._on_status_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_INPUT,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=34,
        )
        self.status_seg.set("All Submissions")
        self.status_seg.pack(side="right")

        # 4. Submissions Table Card
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
        th.grid_columnconfigure(0, weight=3)
        th.grid_columnconfigure(1, weight=4)
        th.grid_columnconfigure(2, weight=2)
        th.grid_columnconfigure(3, weight=2)
        th.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(th, text="STUDENT PARTICIPANT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="ASSESSMENT QUIZ", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="SCORE / PERCENTAGE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=12, pady=8, sticky="w")
        ctk.CTkLabel(th, text="SUBMITTED AT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=12, pady=8, sticky="w")

        self.table_body = ctk.CTkFrame(table_card, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _create_card(self, parent, col, title, default_val, subtitle, color):
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
        ok, res = api_client.get_all_results()
        self.submissions = res if (ok and res) else []

        tot = len(self.submissions)
        passed = sum(1 for s in self.submissions if s.get("is_passed", False))
        failed = tot - passed
        avg_score = int(sum(s.get("percentage", 0) for s in self.submissions) / tot) if tot > 0 else 0

        self.c_tot.configure(text=str(tot))
        self.c_pass.configure(text=str(passed))
        self.c_fail.configure(text=str(failed))
        self.c_avg.configure(text=f"{avg_score}%")

        self._filter_and_render()

    def _filter_and_render(self):
        for w in self.table_body.winfo_children():
            w.destroy()

        filtered = []
        for s in self.submissions:
            is_pass = s.get("is_passed", False)
            if self.status_filter == "Passed Only" and not is_pass:
                continue
            if self.status_filter == "Failed Only" and is_pass:
                continue
            if self.search_query:
                st = s.get("student_name", "").lower()
                qt = s.get("quiz_title", "").lower()
                if self.search_query not in st and self.search_query not in qt:
                    continue
            filtered.append(s)

        if not filtered:
            ctk.CTkLabel(
                self.table_body,
                text="No submissions found matching criteria.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=36)
            return

        for idx, s in enumerate(filtered):
            row = ctk.CTkFrame(
                self.table_body,
                fg_color=Theme.BG_CARD if idx % 2 == 0 else "#FAFAFA",
                corner_radius=6,
            )
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=4)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)

            # Student Name
            name_box = ctk.CTkFrame(row, fg_color="transparent")
            name_box.grid(row=0, column=0, padx=12, pady=10, sticky="w")
            initial = (s.get("student_name", "S")[0]).upper()
            ctk.CTkLabel(
                name_box,
                text=f" {initial} ",
                font=("Segoe UI", 9, "bold"),
                fg_color=Theme.PRIMARY_LIGHT,
                text_color=Theme.PRIMARY,
                corner_radius=10,
                width=24,
                height=24,
            ).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(name_box, text=s.get("student_name", "Student"), font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left")

            # Quiz Title
            ctk.CTkLabel(row, text=s.get("quiz_title", "Assessment"), font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=12, pady=10, sticky="w")

            # Score & Percentage
            pct = s.get("percentage", 0)
            score_txt = f"{pct}% ({s.get('score_obtained', 0)} / {s.get('total_marks', 0)})"
            ctk.CTkLabel(row, text=score_txt, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=2, padx=12, pady=10, sticky="w")

            # Status Badge Pill
            is_pass = s.get("is_passed", False)
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

            # Submitted At
            d_str = str(s.get("submitted_at", "Recent"))
            if "T" in d_str:
                d_str = d_str.split("T")[0]
            ctk.CTkLabel(row, text=d_str, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=12, pady=10, sticky="w")

    def _export_csv(self):
        if not self.submissions:
            messagebox.showinfo("Export", "No submission records available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"QuizFlow_Gradebook_{datetime.now().strftime('%Y%m%d')}.csv",
        )
        if not file_path:
            return

        import csv
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Student Name", "Quiz Title", "Score Obtained", "Total Marks", "Percentage", "Status", "Date Submitted"])
                for s in self.submissions:
                    writer.writerow([
                        s.get("student_name", "Student"),
                        s.get("quiz_title", "Quiz"),
                        s.get("score_obtained", 0),
                        s.get("total_marks", 0),
                        f"{s.get('percentage', 0)}%",
                        "PASSED" if s.get("is_passed") else "FAILED",
                        s.get("submitted_at", ""),
                    ])
            messagebox.showinfo("Export Success", f"Gradebook exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not write CSV file: {str(e)}")

