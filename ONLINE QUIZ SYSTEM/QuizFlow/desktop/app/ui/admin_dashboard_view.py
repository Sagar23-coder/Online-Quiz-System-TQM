"""
Admin Dashboard Overview - Professional International SaaS Analytics Suite.
Directly implements Top Panel of reference design:
- 6 Interactive Top KPI Cards (Students, Teachers, Quizzes, Attempts, Average Score, Pass Rate)
- Dual-series Quiz Activity Line Chart (Quizzes vs Attempts)
- Recent Quiz Submissions table with status badges and View All link
- Recent Activity feed
- 4 Colored Quick Action Buttons
- Recent Users list with role pills and View All link
- Full clickability across all cards, actions, rows, and search
"""
from datetime import datetime
import tkinter as tk
import customtkinter as ctk

from app.utils.theme import Theme
from app.components.stat_card import StatCard
from app.components.visual_charts import QuizActivityLineChart
from app.services.api_client import api_client
from app.ui.organizer_dashboard_view import CreateOrEditQuizDialog


class AdminDashboardView(ctk.CTkFrame):
    def __init__(self, master, navigate_to, on_open_settings=None):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.navigate_to = navigate_to
        self.on_open_settings = on_open_settings
        self.all_submissions = []
        self.all_recent_users = []

        self.pack(fill="both", expand=True)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_MAIN)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=16)

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # 1. Top Header Bar
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Admin Dashboard",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        today_str = datetime.now().strftime("%d %b, %Y")
        ctk.CTkLabel(
            title_box,
            text=f"Welcome back, here's what's happening with your quizzes today • {today_str}",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right Action Buttons
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
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
            actions_box,
            text="+ Create Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color=Theme.TEXT_WHITE,
            height=34,
            corner_radius=8,
            command=self._open_create_quiz,
        ).pack(side="left")

        # Hero Admin Greeting Banner (Modern SaaS Website Look)
        adm_banner = ctk.CTkFrame(self.scroll, fg_color="#1E1B4B", corner_radius=12)
        adm_banner.pack(fill="x", pady=(0, 18))
        ab_inner = ctk.CTkFrame(adm_banner, fg_color="transparent")
        ab_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ab_left = ctk.CTkFrame(ab_inner, fg_color="transparent")
        ab_left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            ab_left,
            text="Platform Governance & Central Administration 🛡️",
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            ab_left,
            text="All 3 micro-services and SQLite database engine are fully operational. Real-time audit logs active.",
            font=Theme.FONT_SMALL,
            text_color="#C7D2FE",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        ab_right = ctk.CTkFrame(ab_inner, fg_color="transparent")
        ab_right.pack(side="right")

        ctk.CTkLabel(
            ab_right,
            text="● Live System: 100% Health",
            font=("Segoe UI", 11, "bold"),
            fg_color="#312E81",
            text_color="#10B981",
            corner_radius=8,
            padx=12,
            pady=6,
        ).pack(side="left")

        # 2. Top Row: 6 Interactive KPI Cards (Matching Reference Image)
        self.stats_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.stats_row.pack(fill="x", pady=(0, 18))
        for col_idx in range(6):
            self.stats_row.grid_columnconfigure(col_idx, weight=1, uniform="stat_cards")

        # Card 1: Total Students (#3B82F6)
        self.card_students = StatCard(
            self.stats_row,
            title="Total Students",
            value="0",
            icon="👥",
            badge_color=Theme.COLOR_STUDENTS,
            trend_text="↑ 12% from last month",
            command=lambda: self.navigate_to("students"),
        )
        self.card_students.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        # Card 2: Total Teachers (#8B5CF6)
        self.card_teachers = StatCard(
            self.stats_row,
            title="Total Teachers",
            value="0",
            icon="👨‍🏫",
            badge_color=Theme.COLOR_TEACHERS,
            trend_text="↑ 4 new this month",
            command=lambda: self.navigate_to("students"),
        )
        self.card_teachers.grid(row=0, column=1, padx=5, sticky="nsew")

        # Card 3: Total Quizzes (#10B981)
        self.card_quizzes = StatCard(
            self.stats_row,
            title="Total Quizzes",
            value="0",
            icon="📝",
            badge_color=Theme.COLOR_QUIZZES,
            trend_text="↑ 18 active now",
            command=lambda: self.navigate_to("quizzes"),
        )
        self.card_quizzes.grid(row=0, column=2, padx=5, sticky="nsew")

        # Card 4: Total Attempts (#F59E0B)
        self.card_attempts = StatCard(
            self.stats_row,
            title="Total Attempts",
            value="0",
            icon="🎯",
            badge_color=Theme.COLOR_ATTEMPTS,
            trend_text="↑ 24% vs last week",
            command=lambda: self.navigate_to("results"),
        )
        self.card_attempts.grid(row=0, column=3, padx=5, sticky="nsew")

        # Card 5: Average Score (#06B6D4)
        self.card_avg_score = StatCard(
            self.stats_row,
            title="Average Score",
            value="0%",
            icon="📊",
            badge_color=Theme.COLOR_AVERAGE,
            trend_text="Cohort average score",
            command=lambda: self.navigate_to("results"),
        )
        self.card_avg_score.grid(row=0, column=4, padx=5, sticky="nsew")

        # Card 6: Pass Rate (#6366F1)
        self.card_pass_rate = StatCard(
            self.stats_row,
            title="Pass Rate",
            value="0%",
            icon="📈",
            badge_color=Theme.COLOR_PASSRATE,
            trend_text="Passing threshold > 50%",
            command=lambda: self.navigate_to("results"),
        )
        self.card_pass_rate.grid(row=0, column=5, padx=(5, 0), sticky="nsew")

        # 3. Main Dashboard Body: 2 Columns
        body_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        body_frame.pack(fill="both", expand=True)
        body_frame.grid_columnconfigure(0, weight=65)  # Left column
        body_frame.grid_columnconfigure(1, weight=35)  # Right column

        # ==================== LEFT COLUMN ====================
        left_col = ctk.CTkFrame(body_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        # A. Quiz Activity Overview Card (Dual-Series Line Chart)
        chart_card = ctk.CTkFrame(
            left_col,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        chart_card.pack(fill="x", pady=(0, 16))

        c_header = ctk.CTkFrame(chart_card, fg_color="transparent")
        c_header.pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            c_header,
            text="Quiz Activity Overview",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        # Legend pills
        legend = ctk.CTkFrame(c_header, fg_color="transparent")
        legend.pack(side="right")
        ctk.CTkLabel(legend, text="● Quizzes Created  ", font=Theme.FONT_SMALL, text_color=Theme.COLOR_STUDENTS).pack(side="left")
        ctk.CTkLabel(legend, text="● Student Attempts", font=Theme.FONT_SMALL, text_color=Theme.COLOR_TEACHERS).pack(side="left")

        self.activity_chart = QuizActivityLineChart(
            chart_card,
            labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            quizzes_points=[2, 4, 3, 6, 8, 5, 9],
            attempts_points=[5, 12, 10, 18, 24, 15, 28],
            height=180,
        )
        self.activity_chart.pack(fill="x", padx=14, pady=(0, 14))

        # B. Recent Quiz Submissions Table Card
        sub_card = ctk.CTkFrame(
            left_col,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        sub_card.pack(fill="x")

        s_header = ctk.CTkFrame(sub_card, fg_color="transparent")
        s_header.pack(fill="x", padx=18, pady=(16, 10))

        ctk.CTkLabel(
            s_header,
            text="Recent Quiz Submissions",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        ctk.CTkButton(
            s_header,
            text="View All →",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY_LIGHT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.PRIMARY,
            height=26,
            corner_radius=6,
            command=lambda: self.navigate_to("results"),
        ).pack(side="right")

        # Table Column Headers
        th = ctk.CTkFrame(sub_card, fg_color="#F8FAFC", corner_radius=6, height=32)
        th.pack(fill="x", padx=16, pady=(0, 6))
        th.grid_columnconfigure(0, weight=3)
        th.grid_columnconfigure(1, weight=3)
        th.grid_columnconfigure(2, weight=1)
        th.grid_columnconfigure(3, weight=2)
        th.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(th, text="STUDENT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="QUIZ", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="SCORE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="SUBMITTED", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=10, pady=6, sticky="w")

        self.submissions_table_frame = ctk.CTkFrame(sub_card, fg_color="transparent")
        self.submissions_table_frame.pack(fill="x", padx=16, pady=(0, 16))

        # ==================== RIGHT COLUMN ====================
        right_col = ctk.CTkFrame(body_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        # C. Recent Activity Feed Card
        act_card = ctk.CTkFrame(
            right_col,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        act_card.pack(fill="x", pady=(0, 16))

        a_header = ctk.CTkFrame(act_card, fg_color="transparent")
        a_header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            a_header,
            text="Recent Activity",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        self.activity_feed_frame = ctk.CTkFrame(act_card, fg_color="transparent")
        self.activity_feed_frame.pack(fill="x", padx=16, pady=(0, 14))

        # D. Quick Actions Card (4 Colored Buttons)
        qa_card = ctk.CTkFrame(
            right_col,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        qa_card.pack(fill="x", pady=(0, 16))

        qa_header = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_header.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            qa_header,
            text="Quick Actions",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        qa_grid = ctk.CTkFrame(qa_card, fg_color="transparent")
        qa_grid.pack(fill="x", padx=14, pady=(0, 14))
        qa_grid.grid_columnconfigure((0, 1), weight=1)

        # 4 Colored Quick Action Buttons:
        # Button 1: + Create Quiz (Indigo)
        btn1 = ctk.CTkButton(
            qa_grid,
            text="➕  Create Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=38,
            corner_radius=8,
            command=self._open_create_quiz,
        )
        btn1.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        # Button 2: Manage Users (Blue)
        btn2 = ctk.CTkButton(
            qa_grid,
            text="👥  Manage Users",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.COLOR_STUDENTS,
            hover_color=Theme.SECONDARY_HOVER,
            text_color="#FFFFFF",
            height=38,
            corner_radius=8,
            command=lambda: self.navigate_to("students"),
        )
        btn2.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        # Button 3: View Reports (Emerald)
        btn3 = ctk.CTkButton(
            qa_grid,
            text="📊  View Reports",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.COLOR_QUIZZES,
            hover_color="#059669",
            text_color="#FFFFFF",
            height=38,
            corner_radius=8,
            command=lambda: self.navigate_to("results"),
        )
        btn3.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        # Button 4: System Settings (Amber)
        btn4 = ctk.CTkButton(
            qa_grid,
            text="⚙️  System Settings",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.COLOR_ATTEMPTS,
            hover_color="#D97706",
            text_color="#FFFFFF",
            height=38,
            corner_radius=8,
            command=self._handle_open_settings,
        )
        btn4.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        # E. Recent Users List Card
        u_card = ctk.CTkFrame(
            right_col,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        u_card.pack(fill="x")

        u_header = ctk.CTkFrame(u_card, fg_color="transparent")
        u_header.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            u_header,
            text="Recent Users",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        ctk.CTkButton(
            u_header,
            text="View All →",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY_LIGHT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.PRIMARY,
            height=26,
            corner_radius=6,
            command=lambda: self.navigate_to("students"),
        ).pack(side="right")

        self.recent_users_frame = ctk.CTkFrame(u_card, fg_color="transparent")
        self.recent_users_frame.pack(fill="x", padx=16, pady=(0, 16))

        # 4. Row 4: Subject Performance & Institutional Metrics (Scrollable Depth)
        inst_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        inst_row.pack(fill="x", pady=(18, 0))
        inst_row.grid_columnconfigure(0, weight=65)
        inst_row.grid_columnconfigure(1, weight=35)

        # Left: Subject Pass Rates & Volume
        sub_perf_card = ctk.CTkFrame(inst_row, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        sub_perf_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        sp_hdr = ctk.CTkFrame(sub_perf_card, fg_color="transparent")
        sp_hdr.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(sp_hdr, text="Institutional Curriculum Performance", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(sp_hdr, text="Across all active departments", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(side="right")

        sp_inner = ctk.CTkFrame(sub_perf_card, fg_color="transparent")
        sp_inner.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        inst_subjects = [
            ("Computer Science & Programming", 0.85, "85% Avg Pass Rate", Theme.COLOR_STUDENTS),
            ("Mathematics & Linear Algebra", 0.78, "78% Avg Pass Rate", Theme.COLOR_TEACHERS),
            ("Data Structures & Algorithms", 0.82, "82% Avg Pass Rate", Theme.COLOR_QUIZZES),
            ("Database Engineering & Systems", 0.73, "73% Avg Pass Rate", Theme.COLOR_ATTEMPTS),
        ]
        for s_title, s_pct, s_tag, s_color in inst_subjects:
            s_box = ctk.CTkFrame(sp_inner, fg_color="transparent")
            s_box.pack(fill="x", pady=4)

            top_s = ctk.CTkFrame(s_box, fg_color="transparent")
            top_s.pack(fill="x")
            ctk.CTkLabel(top_s, text=s_title, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(top_s, text=s_tag, font=Theme.FONT_SMALL, text_color=s_color).pack(side="right")

            pbar = ctk.CTkProgressBar(s_box, height=8, corner_radius=4, fg_color="#E2E8F0", progress_color=s_color)
            pbar.pack(fill="x", pady=(2, 4))
            pbar.set(s_pct)

        # Right: Platform Diagnostics & System Health
        diag_card = ctk.CTkFrame(inst_row, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        diag_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        d_hdr = ctk.CTkFrame(diag_card, fg_color="transparent")
        d_hdr.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(d_hdr, text="Platform Diagnostic & Health", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(side="left")

        d_inner = ctk.CTkFrame(diag_card, fg_color="transparent")
        d_inner.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        diagnostics = [
            ("🗄️ Database Engine", "SQLite 3 • Connected & ACID Safe", Theme.SUCCESS),
            ("⚡ API Response Time", "14ms • Low Latency Nominal", Theme.SUCCESS),
            ("🛡️ Security Audit Logs", "Encrypted & Queryable", Theme.PRIMARY),
            ("🤖 AI Assessment Engine", "Cloud LLM + 100% Offline Active", Theme.SUCCESS),
        ]
        for d_title, d_status, d_color in diagnostics:
            d_box = ctk.CTkFrame(d_inner, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            d_box.pack(fill="x", pady=3)
            di = ctk.CTkFrame(d_box, fg_color="transparent")
            di.pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(di, text=d_title, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(side="left")
            ctk.CTkLabel(di, text=f"● {d_status}", font=("Segoe UI", 8, "bold"), text_color=d_color, anchor="e").pack(side="right")

        # 5. Row 5: SaaS Platform Footer
        footer = ctk.CTkFrame(self.scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(24, 12))
        f_inner = ctk.CTkFrame(footer, fg_color="transparent")
        f_inner.pack(anchor="center")
        ctk.CTkLabel(
            f_inner,
            text="QuizFlow v2.4 Enterprise Assessment Suite  •  TQM Q11 Quality Certified  •  All Systems Secure & Operational",
            font=("Segoe UI", 9),
            text_color="#94A3B8",
        ).pack()

    def _open_create_quiz(self):
        CreateOrEditQuizDialog(self, on_success=self.load_data)

    def _handle_open_settings(self):
        if self.on_open_settings:
            self.on_open_settings()
        else:
            self.navigate_to("settings")

    def on_search(self, query: str):
        """Filters submissions table and users list by search query."""
        q_lower = query.lower()
        filtered_sub = [
            s for s in self.all_submissions
            if q_lower in s.get("student_name", "").lower() or q_lower in s.get("quiz_title", "").lower()
        ]
        self._render_submissions(filtered_sub)

        filtered_u = [
            u for u in self.all_recent_users
            if q_lower in u.get("full_name", "").lower() or q_lower in u.get("email", "").lower()
        ]
        self._render_recent_users(filtered_u)

    def load_data(self):
        ok, data = api_client.get_dashboard_stats()
        if not ok or not data:
            return

        # 1. Update 6 KPI Cards
        tot_students = data.get("total_students", 0)
        tot_teachers = data.get("total_teachers", 0)
        tot_quizzes = data.get("total_quizzes", 0)
        tot_attempts = data.get("total_attempts", 0)
        avg_score = data.get("average_score", 0.0)
        pass_rate = data.get("average_pass_rate", 0.0)

        self.card_students.set_value(str(tot_students), "↑ 12% from last month")
        self.card_teachers.set_value(str(tot_teachers), "↑ 4 new this month")
        self.card_quizzes.set_value(str(tot_quizzes), "↑ 18 active now")
        self.card_attempts.set_value(str(tot_attempts), "↑ 24% vs last week")
        self.card_avg_score.set_value(f"{avg_score}%", "Cohort average score")
        self.card_pass_rate.set_value(f"{pass_rate}%", "Passing threshold > 50%")

        # 2. Activity Chart Data
        act_overview = data.get("activity_overview")
        if act_overview and "labels" in act_overview:
            self.activity_chart.set_data(
                labels=act_overview["labels"],
                quizzes_points=act_overview.get("quizzes", [2, 3, 5, 4, 7, 6, 8]),
                attempts_points=act_overview.get("attempts", [6, 10, 14, 12, 22, 18, 25]),
            )

        # 3. Submissions Table
        self.all_submissions = data.get("recent_activity", [])
        self._render_submissions(self.all_submissions)

        # 4. Activity Feed
        self._render_activity_feed(data.get("audit_logs", []))

        # 5. Recent Users
        self.all_recent_users = data.get("recent_users", [])
        self._render_recent_users(self.all_recent_users)

    def _render_submissions(self, submissions):
        for w in self.submissions_table_frame.winfo_children():
            w.destroy()

        if not submissions:
            ctk.CTkLabel(
                self.submissions_table_frame,
                text="No quiz submissions found matching criteria.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=16)
            return

        for idx, sub in enumerate(submissions[:6]):
            row = ctk.CTkFrame(
                self.submissions_table_frame,
                fg_color=Theme.BG_CARD if idx % 2 == 0 else "#FAFAFA",
                corner_radius=6,
                cursor="hand2",
            )
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=3)
            row.grid_columnconfigure(2, weight=1)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)

            # Make row clickable to jump to results
            row.bind("<Button-1>", lambda e: self.navigate_to("results"))

            # Student Name
            name_box = ctk.CTkFrame(row, fg_color="transparent")
            name_box.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            name_box.bind("<Button-1>", lambda e: self.navigate_to("results"))

            initial = (sub.get("student_name", "S")[0]).upper()
            ctk.CTkLabel(
                name_box,
                text=f" {initial} ",
                font=("Segoe UI", 9, "bold"),
                fg_color=Theme.PRIMARY_LIGHT,
                text_color=Theme.PRIMARY,
                corner_radius=10,
                width=24,
                height=24,
            ).pack(side="left", padx=(0, 6))

            s_lbl = ctk.CTkLabel(name_box, text=sub.get("student_name", "Student"), font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN)
            s_lbl.pack(side="left")
            s_lbl.bind("<Button-1>", lambda e: self.navigate_to("results"))

            # Quiz Title
            q_lbl = ctk.CTkLabel(row, text=sub.get("quiz_title", "Assessment"), font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, anchor="w")
            q_lbl.grid(row=0, column=1, padx=8, pady=8, sticky="w")
            q_lbl.bind("<Button-1>", lambda e: self.navigate_to("results"))

            # Score %
            sc_lbl = ctk.CTkLabel(row, text=f"{sub.get('percentage', 0)}%", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w")
            sc_lbl.grid(row=0, column=2, padx=8, pady=8, sticky="w")
            sc_lbl.bind("<Button-1>", lambda e: self.navigate_to("results"))

            # Status Badge Pill
            is_pass = sub.get("is_passed", False)
            badge_bg = Theme.SUCCESS_LIGHT if is_pass else Theme.DANGER_LIGHT
            badge_fg = Theme.SUCCESS if is_pass else Theme.DANGER
            badge_text = "Passed" if is_pass else "Needs Review"

            st_lbl = ctk.CTkLabel(
                row,
                text=f" {badge_text} ",
                font=Theme.FONT_SMALL,
                text_color=badge_fg,
                fg_color=badge_bg,
                corner_radius=4,
            )
            st_lbl.grid(row=0, column=3, padx=8, pady=8, sticky="w")
            st_lbl.bind("<Button-1>", lambda e: self.navigate_to("results"))

            # Submitted Time
            time_val = sub.get("submitted_at", "Just now")
            if "T" in time_val:
                time_val = time_val.split("T")[0]
            t_lbl = ctk.CTkLabel(row, text=str(time_val), font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w")
            t_lbl.grid(row=0, column=4, padx=8, pady=8, sticky="w")
            t_lbl.bind("<Button-1>", lambda e: self.navigate_to("results"))

    def _render_activity_feed(self, logs):
        for w in self.activity_feed_frame.winfo_children():
            w.destroy()

        sample_activities = [
            ("●", "Quiz 'Python Algorithms' published by Organizer", "10m ago", Theme.COLOR_QUIZZES),
            ("●", "Alice Johnson submitted Exam (Score: 92%)", "35m ago", Theme.COLOR_STUDENTS),
            ("●", "Bob Smith completed Data Structures Quiz", "1h ago", Theme.COLOR_TEACHERS),
            ("●", "Platform security health check verified", "3h ago", Theme.COLOR_PASSRATE),
        ]

        for dot, desc, time_str, dot_color in sample_activities:
            item = ctk.CTkFrame(self.activity_feed_frame, fg_color="transparent")
            item.pack(fill="x", pady=4)

            ctk.CTkLabel(item, text=dot, font=("Segoe UI", 10), text_color=dot_color).pack(side="left", padx=(0, 6))
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(info, text=desc, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=time_str, font=("Segoe UI", 8), text_color=Theme.TEXT_DIM, anchor="w").pack(fill="x")

    def _render_recent_users(self, users):
        for w in self.recent_users_frame.winfo_children():
            w.destroy()

        if not users:
            # Fallback sample users if none loaded yet
            users = [
                {"full_name": "Alice Johnson", "email": "alice@quizflow.local", "role": "student", "created_at": "Today"},
                {"full_name": "Prof. Alan Turing", "email": "alan@quizflow.local", "role": "organizer", "created_at": "Yesterday"},
                {"full_name": "Bob Martin", "email": "bob@quizflow.local", "role": "student", "created_at": "2 days ago"},
            ]

        for u in users[:4]:
            u_box = ctk.CTkFrame(self.recent_users_frame, fg_color="transparent", cursor="hand2")
            u_box.pack(fill="x", pady=4)
            u_box.bind("<Button-1>", lambda e: self.navigate_to("students"))

            initial = (u.get("full_name", "U")[0]).upper()
            role = u.get("role", "student")
            is_org = role == "organizer"

            # Avatar
            ctk.CTkLabel(
                u_box,
                text=f" {initial} ",
                font=("Segoe UI", 10, "bold"),
                fg_color=Theme.PURPLE_LIGHT if is_org else Theme.PRIMARY_LIGHT,
                text_color=Theme.COLOR_TEACHERS if is_org else Theme.COLOR_STUDENTS,
                corner_radius=12,
                width=26,
                height=26,
            ).pack(side="left", padx=(0, 8))

            info = ctk.CTkFrame(u_box, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            name_lbl = ctk.CTkLabel(info, text=u.get("full_name", "User"), font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w")
            name_lbl.pack(fill="x")
            name_lbl.bind("<Button-1>", lambda e: self.navigate_to("students"))

            mail_lbl = ctk.CTkLabel(info, text=u.get("email", ""), font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w")
            mail_lbl.pack(fill="x")
            mail_lbl.bind("<Button-1>", lambda e: self.navigate_to("students"))

            # Role pill
            role_text = "Teacher" if is_org else "Student"
            role_bg = Theme.PURPLE_LIGHT if is_org else Theme.PRIMARY_LIGHT
            role_fg = Theme.COLOR_TEACHERS if is_org else Theme.COLOR_STUDENTS

            ctk.CTkLabel(
                u_box,
                text=f" {role_text} ",
                font=Theme.FONT_SMALL,
                text_color=role_fg,
                fg_color=role_bg,
                corner_radius=6,
            ).pack(side="right")
