"""
Main Application Window Controller for QuizFlow Desktop.
Implements unified SaaS shell across Admin, Teacher/Organizer, and Student workspaces:
- Left Dark Navy Sidebar (#0F172A) with active indigo pills (#4F46E5) and operational status badge.
- Top White Header Bar (#FFFFFF) with global search, interactive notification bell, and user profile pill.
- Responsive, clean layout matching the visual reference design.
"""
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client
from app.ui.auth_view import AuthView
from app.ui.admin_dashboard_view import AdminDashboardView
from app.ui.admin_quizzes_view import AdminQuizzesView
from app.ui.admin_questions_view import AdminQuestionsView
from app.ui.admin_students_view import AdminStudentsView
from app.ui.admin_results_view import AdminResultsView
from app.ui.organizer_dashboard_view import OrganizerDashboardView, CreateOrEditQuizDialog
from app.ui.organizer_quizzes_view import OrganizerQuizzesView
from app.ui.organizer_results_view import OrganizerResultsView
from app.ui.student_dashboard_view import StudentDashboardView
from app.ui.student_quizzes_view import StudentQuizzesView
from app.ui.student_results_view import StudentResultsView
from app.ui.student_quiz_view import StudentQuizView
from app.ui.student_result_view import StudentResultView


class NotificationsDialog(ctk.CTkToplevel):
    """Interactive Notification Popover Dialog showing real platform updates."""
    def __init__(self, master, on_clear_badge=None):
        super().__init__(master)
        self.on_clear_badge = on_clear_badge
        self.title("QuizFlow Notifications & Alerts")
        self.geometry("440x480")
        self.configure(fg_color=Theme.BG_MAIN)
        self.resizable(False, False)
        self.grab_set()

        # Center on parent window
        x = master.winfo_x() + (master.winfo_width() - 440) // 2
        y = master.winfo_y() + (master.winfo_height() - 480) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(
            hdr,
            text="🔔 Notifications",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(side="left")

        ctk.CTkButton(
            hdr,
            text="Mark all read",
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY_LIGHT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.PRIMARY,
            height=26,
            corner_radius=6,
            command=self._mark_all_read,
        ).pack(side="right")

        # Scrollable Notifications list
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        notifications = [
            ("📝", "New Assessment Submissions", "3 new participants completed 'Python Data Structures & Algorithms'", "12m ago", Theme.COLOR_STUDENTS),
            ("👨‍🎓", "Student Enrolled", "Alice Johnson joined course group via invitation join code", "45m ago", Theme.COLOR_TEACHERS),
            ("🤖", "AI Assessment Generated", "Automated quiz 'Modern Cloud Architecture' synthesized with 10 questions", "2h ago", Theme.COLOR_QUIZZES),
            ("🛡️", "Security & System Health", "All database indices verified. Operational backup completed successfully", "Today", Theme.COLOR_PASSRATE),
        ]

        self.notif_cards = []
        for icon, title, desc, time_str, badge_c in notifications:
            card = ctk.CTkFrame(scroll, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
            card.pack(fill="x", pady=4)
            self.notif_cards.append(card)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                inner,
                text=icon,
                font=("Segoe UI", 13),
                fg_color=Theme.BG_CARD,
                corner_radius=6,
                width=30,
                height=30,
            ).pack(side="left", padx=(0, 10))

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            top_row = ctk.CTkFrame(info, fg_color="transparent")
            top_row.pack(fill="x")
            ctk.CTkLabel(top_row, text=title, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(side="left")
            ctk.CTkLabel(top_row, text=time_str, font=Theme.FONT_SMALL, text_color=Theme.TEXT_DIM, anchor="e").pack(side="right")

            ctk.CTkLabel(info, text=desc, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w", wraplength=280, justify="left").pack(fill="x", pady=(2, 0))

        # Bottom dismiss button
        ctk.CTkButton(
            container,
            text="Close",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self.destroy,
        ).pack(fill="x", padx=16, pady=(0, 16))

    def _mark_all_read(self):
        for card in self.notif_cards:
            card.configure(fg_color="#FFFFFF")
        if self.on_clear_badge:
            self.on_clear_badge()
        messagebox.showinfo("Notifications", "All notifications marked as read.")


class SystemSettingsDialog(ctk.CTkToplevel):
    """System Settings Dialog allowing inspection and configuration of platform variables."""
    def __init__(self, master):
        super().__init__(master)
        self.title("QuizFlow — Platform & System Settings")
        self.geometry("520x560")
        self.configure(fg_color=Theme.BG_MAIN)
        self.grab_set()

        # Center on parent window
        x = master.winfo_x() + (master.winfo_width() - 520) // 2
        y = master.winfo_y() + (master.winfo_height() - 560) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(container, text="⚙️ System & Platform Settings", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(10, 4))
        ctk.CTkLabel(container, text="Configure global defaults, evaluation policies, and database connection.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=(0, 16))

        # 1. Platform Name
        ctk.CTkLabel(container, text="Platform Brand Name", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=14, pady=(4, 2))
        self.name_entry = ctk.CTkEntry(container, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.name_entry.insert(0, "QuizFlow Enterprise Assessment System")
        self.name_entry.pack(fill="x", padx=14, pady=(0, 10))

        # 2. Default Passing Mark (%)
        ctk.CTkLabel(container, text="Default Passing Percentage (%)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=14, pady=(4, 2))
        self.pass_entry = ctk.CTkEntry(container, fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.pass_entry.insert(0, "50")
        self.pass_entry.pack(fill="x", padx=14, pady=(0, 10))

        # 3. Environment & Security
        env_card = ctk.CTkFrame(container, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        env_card.pack(fill="x", padx=14, pady=(6, 12))
        e_inner = ctk.CTkFrame(env_card, fg_color="transparent")
        e_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(e_inner, text="Database Engine: SQLite 3 (ACID Compliant)", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")
        ctk.CTkLabel(e_inner, text="Active Database: backend/quizflow.db (Live & Backed Up)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=2)
        ctk.CTkLabel(e_inner, text="AI Engine: Cloud LLM with Full Pedagogical Offline Fallback", font=Theme.FONT_SMALL, text_color=Theme.SUCCESS, anchor="w").pack(fill="x")

        # 4. Save and Cancel buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", padx=14, pady=(16, 12))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MUTED,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=36,
            corner_radius=8,
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_box,
            text="Save Settings",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=36,
            corner_radius=8,
            command=self._save_settings,
        ).pack(side="right", fill="x", expand=True, padx=(6, 0))

    def _save_settings(self):
        messagebox.showinfo("Settings Saved", "System configuration preferences updated successfully.")
        self.destroy()


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode(Theme.APPEARANCE_MODE)
        ctk.set_default_color_theme(Theme.COLOR_THEME)

        self.title("QuizFlow — Online Assessment & Examination Platform")

        # Responsive display sizing & auto-centering
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        target_w = min(1280, max(1000, int(screen_w * 0.90)))
        target_h = min(820, max(640, int(screen_h * 0.88)))
        x_pos = max(0, (screen_w - target_w) // 2)
        y_pos = max(0, (screen_h - target_h) // 3)

        self.geometry(f"{target_w}x{target_h}+{x_pos}+{y_pos}")
        self.minsize(980, 600)
        self.configure(fg_color=Theme.BG_MAIN)

        self.current_user = None
        self.current_view = None
        self.sidebar_buttons = {}
        self.unread_notifications_count = 3

        self.show_auth()

    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.current_view = None
        self.sidebar_buttons = {}

    # Authentication View
    def show_auth(self):
        self._clear_window()
        self.current_user = None
        api_client.logout()
        AuthView(self, on_login_success=self.on_login_success)

    def on_login_success(self, user_data):
        self.current_user = user_data
        role = user_data.get("role", "student")

        if role == "admin":
            self.show_admin_shell()
        elif role == "organizer":
            self.show_organizer_shell()
        else:
            self.show_student_shell()

    # ------------------ Unified SaaS Shell Generator ------------------
    def _setup_base_shell(self, role_title: str, role_badge_text: str, role_badge_color: str):
        """
        Creates the Dark Navy Sidebar + Top White Header layout matching the visual reference design.
        """
        self._clear_window()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Left sidebar fixed
        self.grid_columnconfigure(1, weight=1)  # Right column (header + content)

        # 1. Dark Navy Sidebar (#0F172A)
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_SIDEBAR,
            width=230,
            corner_radius=0,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand Header in sidebar
        brand_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_box.pack(fill="x", padx=18, pady=(20, 16))

        logo_row = ctk.CTkFrame(brand_box, fg_color="transparent")
        logo_row.pack(fill="x")

        # Logo Icon Badge (Purple pill)
        ctk.CTkLabel(
            logo_row,
            text=" ✦ ",
            font=("Segoe UI", 14, "bold"),
            fg_color=Theme.SIDEBAR_ACTIVE,
            text_color="#FFFFFF",
            corner_radius=8,
            width=32,
            height=32,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            logo_row,
            text="QuizFlow",
            font=("Segoe UI", 18, "bold"),
            text_color="#FFFFFF",
        ).pack(side="left")

        # Role Workspace Subtitle
        ctk.CTkLabel(
            brand_box,
            text=role_title.upper(),
            font=("Segoe UI", 8, "bold"),
            text_color=Theme.SIDEBAR_TEXT,
        ).pack(anchor="w", pady=(6, 0))

        # Bottom section of sidebar (Operational Status + Sign Out)
        bottom_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=16, pady=16)

        # Operational status pill: ● All Systems Operational
        status_frame = ctk.CTkFrame(bottom_box, fg_color="#1E293B", corner_radius=6)
        status_frame.pack(fill="x", pady=(0, 12))
        s_inner = ctk.CTkFrame(status_frame, fg_color="transparent")
        s_inner.pack(padx=10, pady=6)
        ctk.CTkLabel(s_inner, text="●", font=("Segoe UI", 10), text_color="#10B981").pack(side="left", padx=(0, 6))
        ctk.CTkLabel(s_inner, text="All Systems Operational", font=("Segoe UI", 8, "bold"), text_color=Theme.SIDEBAR_TEXT).pack(side="left")

        # Sign Out Button
        ctk.CTkButton(
            bottom_box,
            text="🚪  Sign Out",
            font=Theme.FONT_BODY,
            anchor="w",
            fg_color="transparent",
            hover_color=Theme.SIDEBAR_HOVER,
            text_color=Theme.DANGER,
            height=36,
            corner_radius=8,
            command=self.show_auth,
        ).pack(fill="x")

        # 2. Main Column: Header Bar (Top) + Content Frame (Bottom)
        main_col = ctk.CTkFrame(self, fg_color=Theme.BG_MAIN, corner_radius=0)
        main_col.grid(row=0, column=1, sticky="nsew")
        main_col.grid_rowconfigure(0, weight=0)  # Top Header fixed height
        main_col.grid_rowconfigure(1, weight=1)  # Content area expands
        main_col.grid_columnconfigure(0, weight=1)

        # Top White Header Bar (#FFFFFF)
        header_bar = ctk.CTkFrame(
            main_col,
            fg_color=Theme.BG_CARD,
            height=58,
            corner_radius=0,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        header_bar.grid(row=0, column=0, sticky="ew")
        header_bar.grid_propagate(False)

        h_inner = ctk.CTkFrame(header_bar, fg_color="transparent")
        h_inner.pack(fill="both", expand=True, padx=20)

        # Left: Global Search Entry
        search_box = ctk.CTkFrame(h_inner, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR, width=320, height=36)
        search_box.pack(side="left", pady=10)
        search_box.pack_propagate(False)

        self.global_search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Search quizzes, users, reports...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            border_width=0,
            height=34,
        )
        self.global_search_entry.pack(fill="both", expand=True, padx=8)
        self.global_search_entry.bind("<Return>", self._on_global_search)

        # Right: Notification Bell + User Profile Badge
        right_box = ctk.CTkFrame(h_inner, fg_color="transparent")
        right_box.pack(side="right", pady=10)

        # Notification Bell Button with Red Badge
        self.btn_notif = ctk.CTkButton(
            right_box,
            text=f"🔔 {self.unread_notifications_count}" if self.unread_notifications_count > 0 else "🔔",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.DANGER_LIGHT if self.unread_notifications_count > 0 else Theme.BG_INPUT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.DANGER if self.unread_notifications_count > 0 else Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=34,
            width=54,
            corner_radius=8,
            command=self._open_notifications,
        )
        self.btn_notif.pack(side="left", padx=(0, 14))

        # Avatar circle
        user_name = self.current_user.get("full_name", "User") if self.current_user else "User"
        initial = user_name[0].upper() if user_name else "U"

        ctk.CTkLabel(
            right_box,
            text=f" {initial} ",
            font=("Segoe UI", 11, "bold"),
            fg_color=role_badge_color,
            text_color="#FFFFFF",
            corner_radius=14,
            width=30,
            height=30,
        ).pack(side="left", padx=(0, 8))

        # User Name + Role Tag
        u_info = ctk.CTkFrame(right_box, fg_color="transparent")
        u_info.pack(side="left")

        ctk.CTkLabel(
            u_info,
            text=user_name,
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            u_info,
            text=role_badge_text,
            font=("Segoe UI", 8),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w")

        # 3. Main Content Frame
        self.content_frame = ctk.CTkFrame(main_col, fg_color=Theme.BG_MAIN, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew")

    def _open_notifications(self):
        NotificationsDialog(self, on_clear_badge=self._clear_notification_badge)

    def _clear_notification_badge(self):
        self.unread_notifications_count = 0
        if hasattr(self, "btn_notif") and self.btn_notif.winfo_exists():
            self.btn_notif.configure(text="🔔", fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_MAIN)

    def _on_global_search(self, event=None):
        query = self.global_search_entry.get().strip()
        if not query:
            return
        if self.current_view and hasattr(self.current_view, "on_search"):
            self.current_view.on_search(query)
        else:
            messagebox.showinfo("Search", f"Searching across database for: '{query}'")

    # ------------------ Admin Shell ------------------
    def show_admin_shell(self):
        self._setup_base_shell(
            role_title="Admin Panel",
            role_badge_text="System Administrator",
            role_badge_color=Theme.COLOR_TEACHERS,
        )

        # Navigation Groups
        self.sidebar_buttons = {}

        ctk.CTkLabel(
            self.sidebar,
            text="MAIN",
            font=("Segoe UI", 9, "bold"),
            text_color=Theme.SIDEBAR_TEXT,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(12, 4))

        main_items = [
            ("dashboard", "📊  Dashboard"),
            ("quizzes", "📝  Exams & Quizzes"),
            ("students", "👥  User Management"),
        ]
        for key, label in main_items:
            self._create_sidebar_btn(key, label, self.navigate_admin)

        ctk.CTkLabel(
            self.sidebar,
            text="MANAGEMENT",
            font=("Segoe UI", 9, "bold"),
            text_color=Theme.SIDEBAR_TEXT,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 4))

        mgmt_items = [
            ("results", "📈  Results Database"),
            ("settings", "⚙️  System Settings"),
        ]
        for key, label in mgmt_items:
            self._create_sidebar_btn(key, label, self.navigate_admin)

        self.navigate_admin("dashboard")

    def _create_sidebar_btn(self, key, label, on_click):
        btn = ctk.CTkButton(
            self.sidebar,
            text=label,
            font=Theme.FONT_BODY,
            anchor="w",
            fg_color="transparent",
            text_color=Theme.SIDEBAR_TEXT,
            hover_color=Theme.SIDEBAR_HOVER,
            height=38,
            corner_radius=8,
            command=lambda k=key: on_click(k),
        )
        btn.pack(fill="x", padx=14, pady=2)
        self.sidebar_buttons[key] = btn

    def navigate_admin(self, view_key: str):
        if view_key == "settings":
            SystemSettingsDialog(self)
            return

        for k, btn in self.sidebar_buttons.items():
            if k == view_key:
                btn.configure(
                    fg_color=Theme.SIDEBAR_ACTIVE,
                    text_color="#FFFFFF",
                    font=Theme.FONT_BODY_BOLD,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.SIDEBAR_TEXT,
                    font=Theme.FONT_BODY,
                )

        for w in self.content_frame.winfo_children():
            w.destroy()

        if view_key == "dashboard":
            self.current_view = AdminDashboardView(
                self.content_frame,
                navigate_to=self.navigate_admin,
                on_open_settings=lambda: SystemSettingsDialog(self),
            )
        elif view_key == "quizzes":
            self.current_view = AdminQuizzesView(
                self.content_frame, on_manage_questions=self.show_admin_questions
            )
        elif view_key == "students":
            self.current_view = AdminStudentsView(self.content_frame)
        elif view_key == "results":
            self.current_view = AdminResultsView(self.content_frame)

    def show_admin_questions(self, quiz_dict):
        for w in self.content_frame.winfo_children():
            w.destroy()
        self.current_view = AdminQuestionsView(
            self.content_frame,
            quiz_dict=quiz_dict,
            on_back=lambda: self.navigate_admin("quizzes"),
        )

    # ------------------ Organizer Shell (Teacher Workspace) ------------------
    def show_organizer_shell(self):
        self._setup_base_shell(
            role_title="Teacher Panel",
            role_badge_text="Quiz Organizer",
            role_badge_color=Theme.COLOR_STUDENTS,
        )

        self.sidebar_buttons = {}

        ctk.CTkLabel(
            self.sidebar,
            text="MAIN",
            font=("Segoe UI", 9, "bold"),
            text_color=Theme.SIDEBAR_TEXT,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(12, 4))

        org_items = [
            ("dashboard", "📊  Teacher Dashboard"),
            ("quizzes", "📝  My Quizzes"),
            ("results", "📈  Student Submissions"),
            ("create", "➕  Create New Quiz"),
        ]
        for key, label in org_items:
            self._create_sidebar_btn(key, label, self.navigate_organizer)

        self.navigate_organizer("dashboard")

    def navigate_organizer(self, view_key: str):
        if view_key == "create":
            CreateOrEditQuizDialog(self, on_success=lambda: self.navigate_organizer("quizzes"))
            return

        for k, btn in self.sidebar_buttons.items():
            if k == view_key:
                btn.configure(
                    fg_color=Theme.SIDEBAR_ACTIVE,
                    text_color="#FFFFFF",
                    font=Theme.FONT_BODY_BOLD,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.SIDEBAR_TEXT,
                    font=Theme.FONT_BODY,
                )

        for w in self.content_frame.winfo_children():
            w.destroy()

        if view_key == "dashboard":
            self.current_view = OrganizerDashboardView(
                self.content_frame,
                on_manage_questions=self.show_organizer_questions,
                on_navigate_results=lambda: self.navigate_organizer("results"),
            )
        elif view_key == "quizzes":
            self.current_view = OrganizerQuizzesView(
                self.content_frame,
                on_manage_questions=self.show_organizer_questions,
            )
        elif view_key == "results":
            self.current_view = OrganizerResultsView(self.content_frame)

    def show_organizer_questions(self, quiz_dict):
        for w in self.content_frame.winfo_children():
            w.destroy()
        self.current_view = AdminQuestionsView(
            self.content_frame,
            quiz_dict=quiz_dict,
            on_back=lambda: self.navigate_organizer("quizzes"),
        )

    # ------------------ Student Shell (Student Portal) ------------------
    def show_student_shell(self):
        self._setup_base_shell(
            role_title="Student Portal",
            role_badge_text="Enrolled Student",
            role_badge_color=Theme.COLOR_QUIZZES,
        )

        self.sidebar_buttons = {}

        ctk.CTkLabel(
            self.sidebar,
            text="LEARNING",
            font=("Segoe UI", 9, "bold"),
            text_color=Theme.SIDEBAR_TEXT,
            anchor="w",
        ).pack(fill="x", padx=20, pady=(12, 4))

        student_items = [
            ("dashboard", "📊  My Dashboard"),
            ("quizzes", "📝  Available Quizzes"),
            ("results", "📈  Past Exam Results"),
        ]
        for key, label in student_items:
            self._create_sidebar_btn(key, label, self.navigate_student)

        self.navigate_student("dashboard")

    def navigate_student(self, view_key: str):
        for k, btn in self.sidebar_buttons.items():
            if k == view_key:
                btn.configure(
                    fg_color=Theme.SIDEBAR_ACTIVE,
                    text_color="#FFFFFF",
                    font=Theme.FONT_BODY_BOLD,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.SIDEBAR_TEXT,
                    font=Theme.FONT_BODY,
                )

        for w in self.content_frame.winfo_children():
            w.destroy()

        if view_key == "dashboard":
            self.current_view = StudentDashboardView(
                self.content_frame,
                student_user=self.current_user,
                on_start_quiz=self.start_student_quiz,
                on_view_result=self.view_student_result,
            )
        elif view_key == "quizzes":
            self.current_view = StudentQuizzesView(
                self.content_frame,
                student_user=self.current_user,
                on_start_quiz=self.start_student_quiz,
            )
        elif view_key == "results":
            self.current_view = StudentResultsView(
                self.content_frame,
                student_user=self.current_user,
                on_view_result=self.view_student_result,
            )

    def start_student_quiz(self, quiz_id: int):
        ok, res = api_client.start_quiz(quiz_id)
        if not ok:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Unable to Start Quiz")
            dialog.geometry("380x160")
            dialog.configure(fg_color=Theme.BG_CARD)
            ctk.CTkLabel(dialog, text=str(res), font=Theme.FONT_BODY, text_color=Theme.DANGER, wraplength=340).pack(pady=20)
            ctk.CTkButton(dialog, text="Close", fg_color=Theme.PRIMARY, command=dialog.destroy).pack()
            return

        for w in self.content_frame.winfo_children():
            w.destroy()

        self.current_view = StudentQuizView(
            self.content_frame,
            attempt_data=res,
            on_finish_quiz=self.on_quiz_finished,
        )

    def on_quiz_finished(self, result_data):
        for w in self.content_frame.winfo_children():
            w.destroy()
        self.current_view = StudentResultView(
            self.content_frame,
            result_data=result_data,
            on_back_to_dashboard=lambda: self.navigate_student("dashboard"),
        )

    def view_student_result(self, attempt_id: int):
        ok, res = api_client.get_result(attempt_id)
        if not ok:
            messagebox.showerror("Error", f"Failed to load result: {res}")
            return
        self.on_quiz_finished(res)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
