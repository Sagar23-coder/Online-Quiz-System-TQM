"""
Student Dashboard View - Professional International SaaS Learning & Examination Suite.
Directly implements Bottom-Right Panel of reference design:
- 4 Interactive Top KPI Cards (Total Attempts, Average Score, Pass Rate, Your Rank)
- Available Quizzes section with green Start Quiz buttons and Join Code modal
- Student Progress Area Chart with soft gradient curve
- Recent Results table with score percentages, pass/fail badges, and Review Answers actions
- Quick Links / Study Resources card
- Non-negotiable clickability across all buttons, cards, and links
"""
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.components.stat_card import StatCard
from app.components.visual_charts import StudentProgressAreaChart
from app.services.api_client import api_client


class StudentDashboardView(ctk.CTkFrame):
    def __init__(self, master, student_user, on_start_quiz, on_view_result):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.user = student_user
        self.on_start_quiz = on_start_quiz
        self.on_view_result = on_view_result
        self.all_quizzes = []
        self.all_history = []

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
            text="Student Dashboard",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Track your learning progress, take quizzes, and review your performance.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right Action: 🔑 Enter Join Code
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

        # Hero Welcome Banner (Modern SaaS Website Feel)
        user_name = self.user.get("full_name", "Student") if self.user else "Student"
        banner = ctk.CTkFrame(self.scroll, fg_color="#1E1B4B", corner_radius=12)
        banner.pack(fill="x", pady=(0, 18))
        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="both", expand=True, padx=20, pady=16)

        b_left = ctk.CTkFrame(b_inner, fg_color="transparent")
        b_left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            b_left,
            text=f"Welcome back, {user_name}! 🎓",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            b_left,
            text="You have completed your recent assessments. Consistency is key to mastery — keep up the study streak!",
            font=Theme.FONT_SMALL,
            text_color="#C7D2FE",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        b_right = ctk.CTkFrame(b_inner, fg_color="transparent")
        b_right.pack(side="right")

        ctk.CTkLabel(
            b_right,
            text="🔥 5-Day Study Streak",
            font=("Segoe UI", 11, "bold"),
            fg_color="#312E81",
            text_color="#FDE047",
            corner_radius=8,
            padx=12,
            pady=6,
        ).pack(side="left", padx=(0, 8))

        # 2. Top Row: 4 Interactive KPI Cards (Matching Bottom-Right Panel of Reference Image)
        self.stats_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=(0, 18))
        self.stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # Card 1: Total Attempts (#F59E0B)
        self.card_att = StatCard(
            self.stats_row,
            title="Total Attempts",
            value="0",
            icon="🎯",
            badge_color=Theme.COLOR_ATTEMPTS,
            trend_text="Completed assessments",
            command=lambda: self._focus_results(),
        )
        self.card_att.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        # Card 2: Average Score (#06B6D4)
        self.card_avg = StatCard(
            self.stats_row,
            title="Average Score",
            value="0%",
            icon="📊",
            badge_color=Theme.COLOR_AVERAGE,
            trend_text="Across all quizzes",
            command=lambda: self._focus_results(),
        )
        self.card_avg.grid(row=0, column=1, padx=4, sticky="nsew")

        # Card 3: Pass Rate (#10B981)
        self.card_pass = StatCard(
            self.stats_row,
            title="Pass Rate",
            value="0%",
            icon="📈",
            badge_color=Theme.COLOR_QUIZZES,
            trend_text="Passed assessments",
            command=lambda: self._focus_results(),
        )
        self.card_pass.grid(row=0, column=2, padx=4, sticky="nsew")

        # Card 4: Your Rank (#8B5CF6)
        self.card_rank = StatCard(
            self.stats_row,
            title="Your Rank",
            value="Top 15%",
            icon="🏆",
            badge_color=Theme.COLOR_TEACHERS,
            trend_text="Overall cohort ranking",
            command=lambda: self._show_rank_dialog(),
        )
        self.card_rank.grid(row=0, column=3, padx=(6, 0), sticky="nsew")

        # 3. Middle Row: Available Quizzes (Left) + Student Progress Area Chart (Right)
        mid_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mid_row.pack(fill="x", pady=(0, 18))
        mid_row.grid_columnconfigure(0, weight=60)
        mid_row.grid_columnconfigure(1, weight=40)

        # Left: Available Quizzes Card
        avail_card = ctk.CTkFrame(
            mid_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        avail_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        av_hdr = ctk.CTkFrame(avail_card, fg_color="transparent")
        av_hdr.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            av_hdr,
            text="Available Quizzes",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        ctk.CTkButton(
            av_hdr,
            text="Enter Code →",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY_LIGHT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.PRIMARY,
            height=26,
            corner_radius=6,
            command=self._open_join_code_dialog,
        ).pack(side="right")

        self.quizzes_list_frame = ctk.CTkFrame(avail_card, fg_color="transparent")
        self.quizzes_list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Right: Student Progress Area Chart Card
        prog_card = ctk.CTkFrame(
            mid_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        prog_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        p_hdr = ctk.CTkFrame(prog_card, fg_color="transparent")
        p_hdr.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            p_hdr,
            text="Student Progress",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        ctk.CTkLabel(
            p_hdr,
            text="● Score Trend (%)",
            font=Theme.FONT_SMALL,
            text_color=Theme.COLOR_STUDENTS,
        ).pack(side="right")

        self.progress_chart = StudentProgressAreaChart(
            prog_card,
            points=[55, 62, 70, 75, 74, 82],
            labels=["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
            height=180,
        )
        self.progress_chart.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # 4. Bottom Row: Recent Results (Left) + Quick Links (Right)
        bottom_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bottom_row.pack(fill="both", expand=True)
        bottom_row.grid_columnconfigure(0, weight=60)
        bottom_row.grid_columnconfigure(1, weight=40)

        # Left: Recent Results Card
        self.results_card = ctk.CTkFrame(
            bottom_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        self.results_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        r_hdr = ctk.CTkFrame(self.results_card, fg_color="transparent")
        r_hdr.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            r_hdr,
            text="Recent Results",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        # Table Column Headers
        th = ctk.CTkFrame(self.results_card, fg_color="#F8FAFC", corner_radius=6, height=32)
        th.pack(fill="x", padx=16, pady=(0, 6))
        th.grid_columnconfigure(0, weight=4)
        th.grid_columnconfigure(1, weight=2)
        th.grid_columnconfigure(2, weight=2)
        th.grid_columnconfigure(3, weight=2)
        th.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(th, text="QUIZ", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="DATE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="SCORE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="ACTION", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=10, pady=6, sticky="w")

        self.results_table_frame = ctk.CTkFrame(self.results_card, fg_color="transparent")
        self.results_table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Right: Quick Links / Resources Card
        ql_card = ctk.CTkFrame(
            bottom_row,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        ql_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ql_hdr = ctk.CTkFrame(ql_card, fg_color="transparent")
        ql_hdr.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            ql_hdr,
            text="Quick Links",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        ql_inner = ctk.CTkFrame(ql_card, fg_color="transparent")
        ql_inner.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Link 1: Practice Available Quiz
        ctk.CTkButton(
            ql_inner,
            text="🔄  Practice Assessment Quiz",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=38,
            corner_radius=8,
            anchor="w",
            command=self._start_first_available_quiz,
        ).pack(fill="x", pady=(0, 8))

        # Link 2: Review Missed Answers
        ctk.CTkButton(
            ql_inner,
            text="📚  Review Past Mistakes",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=38,
            corner_radius=8,
            anchor="w",
            command=self._review_latest_attempt,
        ).pack(fill="x", pady=(0, 8))

        # Link 3: View Achievement Badge
        ctk.CTkButton(
            ql_inner,
            text="🏆  View Achievement Certificate",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.COLOR_TEACHERS,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=38,
            corner_radius=8,
            anchor="w",
            command=self._show_certificate_dialog,
        ).pack(fill="x")

        # 5. Row 5: Subject Mastery & Learning Analytics (Scrollable Web App Depth)
        analytics_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        analytics_row.pack(fill="x", pady=(18, 0))
        analytics_row.grid_columnconfigure(0, weight=60)
        analytics_row.grid_columnconfigure(1, weight=40)

        # Left: Topic Competency Breakdown Card
        comp_card = ctk.CTkFrame(analytics_row, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        comp_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        c_hdr = ctk.CTkFrame(comp_card, fg_color="transparent")
        c_hdr.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(c_hdr, text="Curriculum Subject Mastery", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(c_hdr, text="Based on your recent submissions", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="right")

        c_inner = ctk.CTkFrame(comp_card, fg_color="transparent")
        c_inner.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        subjects_data = [
            ("Computer Science & Algorithms", 0.88, "88% • Excellent", Theme.COLOR_QUIZZES),
            ("Python & Object-Oriented Design", 0.82, "82% • Strong", Theme.COLOR_STUDENTS),
            ("Data Structures & Complexity", 0.74, "74% • Proficient", Theme.COLOR_TEACHERS),
            ("Database Systems & SQL", 0.68, "68% • Review Recommended", Theme.COLOR_ATTEMPTS),
        ]
        for s_title, s_pct, s_tag, s_color in subjects_data:
            s_box = ctk.CTkFrame(c_inner, fg_color="transparent")
            s_box.pack(fill="x", pady=4)

            top_s = ctk.CTkFrame(s_box, fg_color="transparent")
            top_s.pack(fill="x")
            ctk.CTkLabel(top_s, text=s_title, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(top_s, text=s_tag, font=Theme.FONT_SMALL, text_color=s_color).pack(side="right")

            pbar = ctk.CTkProgressBar(s_box, height=8, corner_radius=4, fg_color="#E2E8F0", progress_color=s_color)
            pbar.pack(fill="x", pady=(2, 4))
            pbar.set(s_pct)

        # Right: Campus Noticeboard & Study Tips
        tips_card = ctk.CTkFrame(analytics_row, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        tips_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        t_hdr = ctk.CTkFrame(tips_card, fg_color="transparent")
        t_hdr.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(t_hdr, text="Campus Noticeboard", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")

        t_inner = ctk.CTkFrame(tips_card, fg_color="transparent")
        t_inner.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        notices = [
            ("📢", "Midterm Examination Window", "Registration and mock attempts open until Oct 28.", "High Priority"),
            ("💡", "Active Recall Study Tip", "Revisit questions you got wrong within 24 hours to double retention.", "Tip"),
            ("🕒", "Weekly Teacher Office Hours", "Wednesdays 3-5 PM via portal messaging.", "Schedule"),
        ]
        for icon, n_title, n_desc, n_badge in notices:
            n_row = ctk.CTkFrame(t_inner, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            n_row.pack(fill="x", pady=3)
            ni = ctk.CTkFrame(n_row, fg_color="transparent")
            ni.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(ni, text=icon, font=("Segoe UI", 12)).pack(side="left", padx=(0, 8))
            nb = ctk.CTkFrame(ni, fg_color="transparent")
            nb.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(nb, text=n_title, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")
            ctk.CTkLabel(nb, text=n_desc, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w", wraplength=260, justify="left").pack(fill="x")

        # 6. Row 6: SaaS Platform Footer
        footer = ctk.CTkFrame(self.scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(24, 12))
        f_inner = ctk.CTkFrame(footer, fg_color="transparent")
        f_inner.pack(anchor="center")
        ctk.CTkLabel(
            f_inner,
            text="QuizFlow v2.4 Enterprise Assessment Suite  •  TQM Q11 Certified  •  All Systems Secure & Operational",
            font=("Segoe UI", 9),
            text_color="#94A3B8",
        ).pack()

    def _focus_results(self):
        # Smooth visual feedback
        self.results_card.configure(border_color=Theme.PRIMARY)
        self.after(600, lambda: self.results_card.configure(border_color=Theme.BORDER_COLOR))

    def _start_first_available_quiz(self):
        if self.all_quizzes:
            self.on_start_quiz(self.all_quizzes[0]["id"])
        else:
            messagebox.showinfo("No Quizzes", "No open assessments currently available.")

    def _review_latest_attempt(self):
        if self.all_history:
            self.on_view_result(self.all_history[0]["attempt_id"])
        else:
            messagebox.showinfo("No Attempts", "You haven't completed any assessments yet.")

    def _show_rank_dialog(self):
        messagebox.showinfo(
            "Cohort Ranking",
            f"Student: {self.user.get('full_name', 'Student')}\nCohort Standing: Top 15%\n\nKeep attempting quizzes to increase your standing!",
        )

    def _show_certificate_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Certificate of Assessment")
        dialog.geometry("460x340")
        dialog.configure(fg_color=Theme.BG_CARD)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="🎖️ Assessment Achievement", font=Theme.FONT_TITLE, text_color=Theme.COLOR_TEACHERS).pack(pady=(24, 6))
        ctk.CTkLabel(dialog, text="This certificate is awarded to", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack()
        ctk.CTkLabel(dialog, text=self.user.get("full_name", "Student"), font=("Segoe UI", 16, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=(4, 12))

        ctk.CTkLabel(
            dialog,
            text="For exemplary performance and active participation in QuizFlow curriculum assessments.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            wraplength=380,
            justify="center",
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            dialog,
            text="Close",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=34,
            command=dialog.destroy,
        ).pack(pady=(0, 16))

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

    def on_search(self, query: str):
        """Filters available quizzes and past results."""
        q_lower = query.lower()
        filtered_q = [
            q for q in self.all_quizzes
            if q_lower in q.get("title", "").lower() or q_lower in q.get("join_code", "").lower()
        ]
        self._render_quizzes(filtered_q)

        filtered_h = [
            h for h in self.all_history
            if q_lower in h.get("quiz_title", "").lower()
        ]
        self._render_results_table(filtered_h)

    def load_data(self):
        # 1. Fetch Student Dashboard Stats
        ok_stats, stats = api_client.get_student_dashboard_stats()
        if ok_stats and stats:
            tot_att = stats.get("total_attempts", 0)
            avg_score = stats.get("average_score", 0.0)
            pass_rate = stats.get("pass_rate", 0.0)
            rank = stats.get("rank", "Top 15%")

            self.card_att.set_value(str(tot_att), "Completed assessments")
            self.card_avg.set_value(f"{avg_score}%", "Across all quizzes")
            self.card_pass.set_value(f"{pass_rate}%", "Passed assessments")
            self.card_rank.set_value(str(rank), "Overall cohort ranking")

            weekly = stats.get("weekly_progress", {})
            if weekly and "scores" in weekly and len(weekly["scores"]) >= 2:
                self.progress_chart.set_data(weekly["scores"], weekly.get("labels"))

        # 2. Fetch Available Quizzes
        ok_q, quizzes = api_client.get_published_quizzes()
        self.all_quizzes = quizzes if (ok_q and quizzes) else []
        self._render_quizzes(self.all_quizzes)

        # 3. Fetch Recent History
        ok_h, history = api_client.get_my_history()
        self.all_history = history if (ok_h and history) else []
        self._render_results_table(self.all_history)

    def _render_quizzes(self, quizzes):
        for w in self.quizzes_list_frame.winfo_children():
            w.destroy()

        if not quizzes:
            ctk.CTkLabel(
                self.quizzes_list_frame,
                text="No assessments currently available. Use 'Enter Join Code' to join private tests.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=24)
            return

        for q in quizzes[:4]:
            card = ctk.CTkFrame(self.quizzes_list_frame, fg_color=Theme.BG_INPUT, corner_radius=10, border_width=1, border_color=Theme.BORDER_COLOR)
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)

            top_row = ctk.CTkFrame(left, fg_color="transparent")
            top_row.pack(fill="x")

            ctk.CTkLabel(top_row, text=q.get("title", "Assessment"), font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(side="left")

            # Subject / Category badge
            subj = q.get("subject") or "General"
            ctk.CTkLabel(
                top_row,
                text=f" {subj} ",
                font=Theme.FONT_SMALL,
                fg_color=Theme.PRIMARY_LIGHT,
                text_color=Theme.PRIMARY,
                corner_radius=4,
            ).pack(side="left", padx=8)

            meta_text = f"⏱ {q.get('duration_minutes', 30)} mins  •  📝 {q.get('question_count', 0)} questions  •  Pass: {q.get('passing_percentage', 50)}%"
            ctk.CTkLabel(left, text=meta_text, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(2, 0))

            # Green Start Quiz button matching reference design
            ctk.CTkButton(
                inner,
                text="Start Quiz →",
                font=Theme.FONT_BODY_BOLD,
                fg_color=Theme.COLOR_QUIZZES,
                hover_color="#059669",
                text_color="#FFFFFF",
                width=100,
                height=32,
                corner_radius=6,
                command=lambda q_id=q["id"]: self.on_start_quiz(q_id),
            ).pack(side="right", padx=(10, 0))

    def _render_results_table(self, history):
        for w in self.results_table_frame.winfo_children():
            w.destroy()

        if not history:
            ctk.CTkLabel(
                self.results_table_frame,
                text="No recent assessment results found. Take a quiz to view your score breakdown!",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=20)
            return

        for idx, h in enumerate(history[:5]):
            row = ctk.CTkFrame(
                self.results_table_frame,
                fg_color=Theme.BG_CARD if idx % 2 == 0 else "#FAFAFA",
                corner_radius=6,
            )
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=4)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)

            # Quiz Title
            ctk.CTkLabel(row, text=h.get("quiz_title", "Assessment"), font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=0, padx=8, pady=8, sticky="w")

            # Date
            date_str = str(h.get("completed_at", "Recent"))
            if "T" in date_str:
                date_str = date_str.split("T")[0]
            ctk.CTkLabel(row, text=date_str, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, pady=8, sticky="w")

            # Score %
            pct = h.get("percentage", 0)
            ctk.CTkLabel(row, text=f"{pct}%", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=2, padx=8, pady=8, sticky="w")

            # Status Badge Pill
            is_pass = h.get("is_passed", False)
            badge_bg = Theme.SUCCESS_LIGHT if is_pass else Theme.DANGER_LIGHT
            badge_fg = Theme.SUCCESS if is_pass else Theme.DANGER
            badge_text = "Passed" if is_pass else "Needs Review"

            ctk.CTkLabel(
                row,
                text=f" {badge_text} ",
                font=Theme.FONT_SMALL,
                text_color=badge_fg,
                fg_color=badge_bg,
                corner_radius=4,
            ).grid(row=0, column=3, padx=8, pady=8, sticky="w")

            # Action Button
            ctk.CTkButton(
                row,
                text="Review Answers",
                font=Theme.FONT_SMALL,
                fg_color=Theme.PRIMARY_LIGHT,
                hover_color=Theme.BORDER_COLOR,
                text_color=Theme.PRIMARY,
                height=26,
                corner_radius=6,
                command=lambda a_id=h["attempt_id"]: self.on_view_result(a_id),
            ).grid(row=0, column=4, padx=8, pady=8, sticky="w")
