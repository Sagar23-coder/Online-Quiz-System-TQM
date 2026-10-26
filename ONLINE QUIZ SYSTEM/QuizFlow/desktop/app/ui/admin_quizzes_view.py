"""
Admin Quiz Management View: Listing, Creating, Publishing, and Deleting Quizzes.
"""
import customtkinter as ctk
from app.utils.theme import Theme
from app.services.api_client import api_client
from app.ui.organizer_dashboard_view import CreateOrEditQuizDialog


class CreateQuizDialog(ctk.CTkToplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title("Create New Quiz")
        self.geometry("480x460")
        self.configure(fg_color=Theme.BG_DARK)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Create New Quiz", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(16, 12))

        # Title
        ctk.CTkLabel(container, text="Quiz Title *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=20, pady=(4, 2))
        self.title_entry = ctk.CTkEntry(container, placeholder_text="e.g. Operating Systems Architecture", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.title_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Description
        ctk.CTkLabel(container, text="Description", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=20, pady=(0, 2))
        self.desc_entry = ctk.CTkEntry(container, placeholder_text="Brief summary of quiz scope", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.desc_entry.pack(fill="x", padx=20, pady=(0, 10))

        # Duration & Passing Percentage in 2 columns
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 10))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        col1 = ctk.CTkFrame(row, fg_color="transparent")
        col1.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkLabel(col1, text="Duration (Minutes) *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.dur_entry = ctk.CTkEntry(col1, placeholder_text="30", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.dur_entry.insert(0, "30")
        self.dur_entry.pack(fill="x", pady=(2, 0))

        col2 = ctk.CTkFrame(row, fg_color="transparent")
        col2.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        ctk.CTkLabel(col2, text="Passing Marks (%) *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.pass_entry = ctk.CTkEntry(col2, placeholder_text="50", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR)
        self.pass_entry.insert(0, "50")
        self.pass_entry.pack(fill="x", pady=(2, 0))

        self.error_label = ctk.CTkLabel(container, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER, wraplength=400)
        self.error_label.pack(pady=4)

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(12, 16))
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
            text="Create Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=38,
            command=self._handle_create,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _handle_create(self):
        title = self.title_entry.get().strip()
        desc = self.desc_entry.get().strip()
        dur_str = self.dur_entry.get().strip()
        pass_str = self.pass_entry.get().strip()

        if not title:
            self.error_label.configure(text="Quiz title is required.")
            return

        try:
            dur = int(dur_str)
            pass_pct = int(pass_str)
        except ValueError:
            self.error_label.configure(text="Duration and passing percentage must be integers.")
            return

        ok, res = api_client.create_quiz({
            "title": title,
            "description": desc or None,
            "duration_minutes": dur,
            "passing_percentage": pass_pct,
        })

        if ok:
            self.destroy()
            self.on_success()
        else:
            self.error_label.configure(text=str(res))


class AdminQuizzesView(ctk.CTkFrame):
    def __init__(self, master, on_manage_questions):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.on_manage_questions = on_manage_questions
        self.quizzes = []

        self.pack(fill="both", expand=True, padx=24, pady=20)
        self._build_ui()
        self.load_quizzes()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Quiz Management",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Create, edit, publish, and configure assessment tests",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(
            btn_box,
            text="Refresh",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            width=90,
            height=34,
            command=self.load_quizzes,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="+ Create Quiz",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            height=34,
            command=self._open_create_dialog,
        ).pack(side="left")

        # Scrollable Quizzes List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def _open_create_dialog(self):
        CreateOrEditQuizDialog(self, on_success=self.load_quizzes)

    def load_quizzes(self):
        ok, res = api_client.get_admin_quizzes()
        if not ok:
            return

        self.quizzes = res
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.quizzes:
            ctk.CTkLabel(
                self.scroll,
                text="No quizzes created yet. Click '+ Create Quiz' above to add your first quiz.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=40)
            return

        for q in self.quizzes:
            self._render_quiz_card(q)

    def _render_quiz_card(self, q):
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        card.pack(fill="x", pady=6, padx=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Left Column: Information
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        # Title & Badges
        top_row = ctk.CTkFrame(left, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=q["title"],
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
        ).pack(side="left")

        # Status badge
        is_pub = q["is_published"]
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
        ).pack(side="left", padx=12)

        # Description
        desc_text = q.get("description") or "No description provided."
        ctk.CTkLabel(
            left,
            text=desc_text,
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
            wraplength=520,
        ).pack(fill="x", pady=(4, 8))

        # Metadata badges row
        meta_row = ctk.CTkFrame(left, fg_color="transparent")
        meta_row.pack(fill="x")

        badges = [
            f"⏱ {q['duration_minutes']} min",
            f"📝 {q['question_count']} questions",
            f"🎯 {q['total_marks']} marks",
            f"🏆 {q['passing_percentage']}% pass",
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

        # Right Column: Action Buttons
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right", fill="y", padx=(16, 0))

        # Manage Questions Button
        ctk.CTkButton(
            actions,
            text="Manage Questions",
            font=Theme.FONT_SMALL,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            width=130,
            height=30,
            command=lambda q_obj=q: self.on_manage_questions(q_obj),
        ).pack(pady=(0, 6))

        # Toggle Publish Button
        pub_btn_text = "Unpublish" if is_pub else "Publish Quiz"
        pub_btn_color = Theme.WARNING if is_pub else Theme.SUCCESS
        ctk.CTkButton(
            actions,
            text=pub_btn_text,
            font=Theme.FONT_SMALL,
            fg_color=pub_btn_color,
            width=130,
            height=30,
            command=lambda q_id=q["id"], pub=is_pub: self._toggle_publish(q_id, pub),
        ).pack(pady=(0, 6))

        # Delete Button
        ctk.CTkButton(
            actions,
            text="Delete",
            font=Theme.FONT_SMALL,
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            width=130,
            height=28,
            command=lambda q_id=q["id"]: self._delete_quiz(q_id),
        ).pack()

    def _toggle_publish(self, quiz_id: int, currently_published: bool):
        if currently_published:
            api_client.unpublish_quiz(quiz_id)
        else:
            api_client.publish_quiz(quiz_id)
        self.load_quizzes()

    def _delete_quiz(self, quiz_id: int):
        ok, res = api_client.delete_quiz(quiz_id)
        self.load_quizzes()

