"""
Organizer Quizzes View - Dedicated Teacher Curriculum & Quiz Management Workspace.
Provides audience filtering, private join code controls, question editor triggers, and CSV exports.
"""
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client
from app.ui.organizer_dashboard_view import CreateOrEditQuizDialog, QuizReportDialog


class OrganizerQuizzesView(ctk.CTkFrame):
    def __init__(self, master, on_manage_questions):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.on_manage_questions = on_manage_questions
        self.quizzes = []
        self.filter_mode = "All"
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
            text="Curriculum Exams & Quiz Management",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Create, publish, edit question banks, and configure private join codes for your classes.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Actions
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

        # 2. Search & Audience Filter Card
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

        # Search box
        search_box = ctk.CTkFrame(fc_inner, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Search your quizzes by title or join code...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            border_width=0,
            height=36,
        )
        self.search_entry.pack(fill="x", padx=8)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Audience segmented tabs
        self.filter_buttons = ctk.CTkSegmentedButton(
            fc_inner,
            values=["All", "🔒 Private (Code Required)", "🌐 Public", "Drafts"],
            command=self._on_filter_changed,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_INPUT,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=34,
        )
        self.filter_buttons.set("All")
        self.filter_buttons.pack(side="right")

        # 3. Quizzes Container
        self.quizzes_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.quizzes_container.pack(fill="both", expand=True, pady=(0, 16))

    def _open_create_quiz(self):
        CreateOrEditQuizDialog(self, on_success=self.load_data)

    def _on_search_key(self, event=None):
        self.search_query = self.search_entry.get().strip().lower()
        self._filter_and_render()

    def _on_filter_changed(self, value):
        self.filter_mode = value
        self._filter_and_render()

    def load_data(self):
        ok_q, quizzes = api_client.get_organizer_quizzes()
        self.quizzes = quizzes if (ok_q and quizzes) else []
        self._filter_and_render()

    def _filter_and_render(self):
        for w in self.quizzes_container.winfo_children():
            w.destroy()

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

            if self.search_query:
                t = q.get("title", "").lower()
                c = q.get("join_code", "").lower()
                if self.search_query not in t and self.search_query not in c:
                    continue

            filtered.append(q)

        if not filtered:
            box = ctk.CTkFrame(self.quizzes_container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
            box.pack(fill="x", pady=20)
            ctk.CTkLabel(
                box,
                text="No assessments found matching the selected filter or search.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=40)
            return

        for q in filtered:
            self._render_quiz_card(q)

    def _copy_join_code(self, code: str):
        self.clipboard_clear()
        self.clipboard_append(code)
        messagebox.showinfo("Join Code Copied", f"Code '{code}' copied to clipboard!\nShare this code with your students to grant private access.")

    def _render_quiz_card(self, q):
        card = ctk.CTkFrame(self.quizzes_container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        card.pack(fill="x", pady=6)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        # Left Column: Info & Badges
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

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

        # Description
        desc_text = q.get("description") or "No description provided."
        if not is_pub_disc:
            desc_text += " • (Restricted test: only participants with join code can take it)"
        ctk.CTkLabel(left, text=desc_text, font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, anchor="w", wraplength=520).pack(fill="x", pady=(4, 6))

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

        # 4. Share Quiz Link
        ctk.CTkButton(
            actions,
            text="🔗 Share Link",
            font=Theme.FONT_SMALL,
            fg_color="#0EA5E9",
            hover_color="#0284C7",
            text_color="#FFFFFF",
            width=135,
            height=28,
            command=lambda q_obj=q: ShareQuizDialog(self, q_obj, on_refresh=self.load_data),
        ).pack(pady=(0, 4))

        # 5. Delete
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



class ShareQuizDialog(ctk.CTkToplevel):
    """
    Professional Share Quiz Dialog — shows the shareable public quiz link,
    allows copying, regenerating, and toggling the link's active state.
    Students receive this link to access the quiz without logging in.
    """

    def __init__(self, master, quiz_data: dict, on_refresh=None):
        super().__init__(master)
        self.quiz_data = quiz_data
        self.on_refresh = on_refresh
        self.quiz_id = quiz_data["id"]

        self.title("Share Quiz Link")
        self.geometry("520x480")
        self.configure(fg_color=Theme.BG_MAIN)
        self.resizable(False, False)
        self.grab_set()

        # Center on parent
        x = master.winfo_rootx() + (master.winfo_width() - 520) // 2
        y = master.winfo_rooty() + (master.winfo_height() - 480) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._link_data = None
        self._build_ui()
        self._load_link()

    def _build_ui(self):
        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12,
                            border_width=1, border_color=Theme.BORDER_COLOR)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(hdr, text="🔗  Share Quiz Link", font=Theme.FONT_HEADING,
                     text_color=Theme.TEXT_MAIN).pack(side="left")

        # Quiz title & status
        info = ctk.CTkFrame(card, fg_color=Theme.BG_INPUT, corner_radius=8)
        info.pack(fill="x", padx=20, pady=(8, 4))
        is_pub = self.quiz_data.get("is_published", False)
        status_color = Theme.SUCCESS if is_pub else Theme.WARNING
        status_text = "✅ PUBLISHED" if is_pub else "⚠️  DRAFT (Not publicly accessible)"
        ctk.CTkLabel(info, text=self.quiz_data.get("title", "Quiz"),
                     font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN,
                     anchor="w").pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(info, text=status_text, font=Theme.FONT_SMALL,
                     text_color=status_color, anchor="w").pack(fill="x", padx=12, pady=(0, 10))

        # URL display
        url_lbl = ctk.CTkFrame(card, fg_color="transparent")
        url_lbl.pack(fill="x", padx=20, pady=(10, 2))
        ctk.CTkLabel(url_lbl, text="Shareable Quiz URL:", font=Theme.FONT_SMALL,
                     text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")

        url_row = ctk.CTkFrame(card, fg_color="transparent")
        url_row.pack(fill="x", padx=20, pady=(0, 4))
        self.url_entry = ctk.CTkEntry(url_row, placeholder_text="Loading…",
                                      fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR,
                                      font=Theme.FONT_SMALL, height=36, corner_radius=8)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(url_row, text="📋 Copy", font=Theme.FONT_SMALL,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                      text_color="#FFFFFF", width=70, height=36, corner_radius=8,
                      command=self._copy_link).pack(side="right")

        # LOCAL DEV notice
        self.dev_notice = ctk.CTkLabel(card,
            text="⚠️  Local URL — only accessible on this machine.\nSet PUBLIC_BASE_URL in .env for internet sharing.",
            font=Theme.FONT_SMALL, text_color="#D97706", justify="left", anchor="w")
        self.dev_notice.pack(fill="x", padx=20, pady=(0, 8))

        # Status badge
        self.link_status_lbl = ctk.CTkLabel(card, text="Link status: loading…",
                                            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED)
        self.link_status_lbl.pack(anchor="w", padx=20, pady=(4, 0))

        # Action buttons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(12, 4))

        ctk.CTkButton(btn_row, text="🔄 Regenerate Link", font=Theme.FONT_SMALL,
                      fg_color=Theme.WARNING, hover_color="#B45309",
                      text_color="#FFFFFF", height=34, corner_radius=8,
                      command=self._regenerate).pack(side="left", padx=(0, 8))

        self.toggle_btn = ctk.CTkButton(btn_row, text="Deactivate Link", font=Theme.FONT_SMALL,
                                        fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER,
                                        text_color="#FFFFFF", height=34, corner_radius=8,
                                        command=self._toggle_active)
        self.toggle_btn.pack(side="left")

        # WhatsApp share hint
        ctk.CTkFrame(card, fg_color=Theme.BORDER_COLOR, height=1).pack(fill="x", padx=20, pady=(12, 8))
        ctk.CTkLabel(card,
            text="💡 Tip: Copy the link and share via WhatsApp, Email, or any messaging app.\n"
                 "Students open it in a browser — no account or app download needed.",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, justify="left", anchor="w",
            wraplength=460).pack(fill="x", padx=20, pady=(0, 14))

        # Close button
        ctk.CTkButton(card, text="Close", font=Theme.FONT_BODY,
                      fg_color=Theme.SECONDARY, hover_color=Theme.SECONDARY_HOVER,
                      text_color="#FFFFFF", height=36, corner_radius=8,
                      command=self.destroy).pack(padx=20, pady=(0, 14), fill="x")

    def _load_link(self):
        """Fetch or create the share link from the backend."""
        ok, data = api_client.get_share_link(self.quiz_id)
        if ok:
            self._link_data = data
            self._refresh_ui()
        else:
            self.url_entry.configure(placeholder_text=f"Error: {data}")
            self.link_status_lbl.configure(text="⚠️  Could not load link.")

    def _refresh_ui(self):
        if not self._link_data:
            return
        url = self._link_data.get("share_url", "")
        is_active = self._link_data.get("is_share_link_active", True)

        # Update URL entry
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)

        # Show/hide local dev notice
        is_local = "localhost" in url or "127.0.0.1" in url
        if is_local:
            self.dev_notice.pack(fill="x", padx=20, pady=(0, 8))
        else:
            self.dev_notice.pack_forget()

        # Link active status
        if is_active:
            self.link_status_lbl.configure(text="✅  Link is ACTIVE — students can access this quiz.",
                                           text_color=Theme.SUCCESS)
            self.toggle_btn.configure(text="🚫 Deactivate Link", fg_color=Theme.DANGER,
                                      hover_color=Theme.DANGER_HOVER)
        else:
            self.link_status_lbl.configure(text="🚫  Link is INACTIVE — students cannot access.",
                                           text_color=Theme.DANGER)
            self.toggle_btn.configure(text="✅ Activate Link", fg_color=Theme.SUCCESS,
                                      hover_color="#059669")

    def _copy_link(self):
        url = self.url_entry.get().strip()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            messagebox.showinfo("Copied!", "Quiz link copied to clipboard!\nPaste it in WhatsApp, Email, etc.")

    def _regenerate(self):
        if not messagebox.askyesno("Regenerate Link",
            "Regenerating creates a new token. The old link will stop working.\n"
            "Existing student submissions are preserved.\n\nContinue?"):
            return
        ok, data = api_client.regenerate_share_link(self.quiz_id)
        if ok:
            self._link_data = data
            self._refresh_ui()
            if self.on_refresh:
                self.on_refresh()
        else:
            messagebox.showerror("Error", f"Could not regenerate link: {data}")

    def _toggle_active(self):
        ok, data = api_client.toggle_share_link(self.quiz_id)
        if ok:
            self._link_data = data
            self._refresh_ui()
        else:
            messagebox.showerror("Error", f"Could not toggle link status: {data}")
