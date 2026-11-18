"""
Organizer Quizzes View - Dedicated Teacher Curriculum & Quiz Management Workspace.
Provides audience filtering, private join code controls, question editor triggers, and CSV exports.
"""
from datetime import datetime
import urllib.parse
import webbrowser
import csv
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client
from app.ui.organizer_dashboard_view import CreateOrEditQuizDialog, QuizReportDialog


class OrganizerQuizzesView(ctk.CTkFrame):
    def __init__(self, master, on_manage_questions, on_view_results=None):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.on_manage_questions = on_manage_questions
        self.on_view_results = on_view_results
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

        # Quiz status tabs
        self.filter_buttons = ctk.CTkSegmentedButton(
            fc_inner,
            values=["All", "Published", "Drafts"],
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

    def on_search(self, query: str):
        self.search_query = query.strip().lower()
        if hasattr(self, "search_entry") and self.search_entry.winfo_exists():
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, query)
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

            if self.filter_mode == "Published" and not is_pub:
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

        # Title with click-to-view-submissions
        title_btn = ctk.CTkButton(
            top_row,
            text=q["title"],
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
            fg_color="transparent",
            hover_color=Theme.BG_INPUT,
            anchor="w",
            command=lambda q_obj=q: QuizSubmissionsDialog(self, q_obj),
        )
        title_btn.pack(side="left")

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
        ).pack(side="left", padx=10)

        # Description
        desc_text = q.get("description") or "No description provided."
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

        # View Submissions Quick Link Button
        ctk.CTkButton(
            meta_row,
            text="👥 View Submissions",
            font=Theme.FONT_SMALL,
            text_color="#FFFFFF",
            fg_color="#6366F1",
            hover_color="#4F46E5",
            corner_radius=4,
            height=22,
            width=130,
            command=lambda q_obj=q: QuizSubmissionsDialog(self, q_obj),
        ).pack(side="left", padx=(4, 6))

        # Right Column: Action Buttons
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right", fill="y", padx=(14, 0))

        # 1. View Submissions (Prominent)
        ctk.CTkButton(
            actions,
            text="👥 Submissions",
            font=Theme.FONT_SMALL,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            text_color="#FFFFFF",
            width=135,
            height=28,
            command=lambda q_obj=q: QuizSubmissionsDialog(self, q_obj),
        ).pack(pady=(0, 4))

        # 2. Manage Questions
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

        # 3. View Report & Export CSV
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
            command=lambda q_obj=q, pub=is_pub: self._toggle_publish(q_obj, pub),
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

    def _toggle_publish(self, quiz_obj: dict, is_currently_published: bool):
        quiz_id = quiz_obj["id"]
        if is_currently_published:
            ok, res = api_client.unpublish_quiz(quiz_id)
        else:
            ok, res = api_client.publish_quiz(quiz_id)

        if ok:
            self.load_data()
            if not is_currently_published:
                # Automatically pop up the Share Quiz Dialog with WhatsApp, Copy, Email options!
                q_updated = dict(quiz_obj)
                q_updated["is_published"] = True
                ShareQuizDialog(self, q_updated, on_refresh=self.load_data)
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

        # Quick Share Channels Row
        share_channels = ctk.CTkFrame(card, fg_color="transparent")
        share_channels.pack(fill="x", padx=20, pady=(6, 4))

        ctk.CTkButton(
            share_channels,
            text="💬 WhatsApp",
            font=Theme.FONT_SMALL,
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            height=32,
            corner_radius=8,
            command=self._share_whatsapp,
        ).pack(side="left", padx=(0, 6), expand=True, fill="x")

        ctk.CTkButton(
            share_channels,
            text="✉️ Email",
            font=Theme.FONT_SMALL,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="#FFFFFF",
            height=32,
            corner_radius=8,
            command=self._share_email,
        ).pack(side="left", padx=(0, 6), expand=True, fill="x")

        ctk.CTkButton(
            share_channels,
            text="🌐 Open Link",
            font=Theme.FONT_SMALL,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            text_color="#FFFFFF",
            height=32,
            corner_radius=8,
            command=self._open_in_browser,
        ).pack(side="left", expand=True, fill="x")

        # WhatsApp share hint
        ctk.CTkFrame(card, fg_color=Theme.BORDER_COLOR, height=1).pack(fill="x", padx=20, pady=(10, 6))
        ctk.CTkLabel(card,
            text="💡 Accessible on Any System: Share this link with students on phones, tablets, or computers.\n"
                 "Students open the link in any web browser — no login or account required.",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, justify="left", anchor="w",
            wraplength=460).pack(fill="x", padx=20, pady=(0, 12))

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

    def _share_whatsapp(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        title = self.quiz_data.get("title", "Assessment")
        msg = f"Join and complete the quiz '{title}' directly via this link:\n{url}\n(No account or login required)"
        encoded = urllib.parse.quote(msg)
        webbrowser.open(f"https://api.whatsapp.com/send?text={encoded}")

    def _share_email(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        title = self.quiz_data.get("title", "Assessment")
        subject = urllib.parse.quote(f"Invitation to take quiz: {title}")
        body = urllib.parse.quote(f"Hello,\n\nPlease click the link below to take the quiz '{title}':\n{url}\n\nNo student account or login is needed. Best of luck!")
        webbrowser.open(f"mailto:?subject={subject}&body={body}")

    def _open_in_browser(self):
        url = self.url_entry.get().strip()
        if url:
            webbrowser.open(url)


class QuizSubmissionsDialog(ctk.CTkToplevel):
    """
    Dedicated Submissions Workspace for a Specific Quiz.
    Shows real-time attempt records, pass/fail status, participant details, and 1-click CSV export.
    """
    def __init__(self, master, quiz_dict: dict):
        super().__init__(master)
        self.master = master
        self.quiz = dict(quiz_dict or {})
        self.quiz_id = self.quiz.get("id")
        self.submissions = []
        self.status_filter = "All"
        self.search_query = ""

        self.title(f"Student Submissions — {self.quiz.get('title', 'Quiz')}")
        self.geometry("960x680")
        self.configure(fg_color=Theme.BG_MAIN)
        self.grab_set()

        # Center on master
        x = master.winfo_x() + (master.winfo_width() - 960) // 2
        y = master.winfo_y() + (master.winfo_height() - 680) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # 1. Header Banner
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 12))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        q_title = self.quiz.get("title", "Assessment")
        ctk.CTkLabel(left, text=f"Submissions for: {q_title}", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(anchor="w")

        info_txt = f"⏱ {self.quiz.get('duration_minutes', 0)} mins  •  🎯 {self.quiz.get('total_marks', 0)} marks  •  🏆 {self.quiz.get('passing_percentage', 50)}% pass criteria"
        ctk.CTkLabel(left, text=info_txt, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Right Action Buttons
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right,
            text="🔄 Refresh",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MAIN,
            width=85,
            height=30,
            corner_radius=6,
            command=self.load_data,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            right,
            text="📥 Export CSV",
            font=Theme.FONT_SMALL,
            fg_color="#059669",
            hover_color="#047857",
            text_color="#FFFFFF",
            width=95,
            height=30,
            corner_radius=6,
            command=self._export_csv,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            right,
            text="✕ Close",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_INPUT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MUTED,
            width=70,
            height=30,
            corner_radius=6,
            command=self.destroy,
        ).pack(side="left")

        # 2. Metric Cards Row
        self.metric_row = ctk.CTkFrame(container, fg_color="transparent")
        self.metric_row.pack(fill="x", padx=16, pady=(0, 12))
        self.metric_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="q_sub_m")

        self.c_tot = self._create_card(self.metric_row, 0, "Total Attempts", "0", "Student submissions", Theme.COLOR_ATTEMPTS)
        self.c_pass = self._create_card(self.metric_row, 1, "Passed", "0", "Met pass criteria", Theme.COLOR_QUIZZES)
        self.c_fail = self._create_card(self.metric_row, 2, "Needs Review", "0", "Below pass threshold", Theme.DANGER)
        self.c_avg = self._create_card(self.metric_row, 3, "Average Score", "0%", "Class average accuracy", Theme.COLOR_STUDENTS)

        # 3. Filter Bar
        f_card = ctk.CTkFrame(container, fg_color=Theme.BG_INPUT, corner_radius=8)
        f_card.pack(fill="x", padx=16, pady=(0, 10))

        fc_inner = ctk.CTkFrame(f_card, fg_color="transparent")
        fc_inner.pack(fill="x", padx=10, pady=8)

        search_box = ctk.CTkFrame(fc_inner, fg_color=Theme.BG_CARD, corner_radius=6, border_width=1, border_color=Theme.BORDER_COLOR)
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Search student name, class, section, or phone...",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            border_width=0,
            height=32,
        )
        self.search_entry.pack(fill="x", padx=6)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.status_seg = ctk.CTkSegmentedButton(
            fc_inner,
            values=["All", "Passed", "Needs Review", "In Progress"],
            command=self._on_status_change,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=30,
        )
        self.status_seg.set("All")
        self.status_seg.pack(side="right")

        # 4. Table Header
        th = ctk.CTkFrame(container, fg_color="#F8FAFC", corner_radius=6, height=32)
        th.pack(fill="x", padx=16, pady=(0, 6))
        th.grid_columnconfigure(0, weight=3)
        th.grid_columnconfigure(1, weight=2)
        th.grid_columnconfigure(2, weight=2)
        th.grid_columnconfigure(3, weight=2)
        th.grid_columnconfigure(4, weight=2)
        th.grid_columnconfigure(5, weight=2)
        th.grid_columnconfigure(6, weight=2)

        ctk.CTkLabel(th, text="STUDENT PARTICIPANT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        ctk.CTkLabel(th, text="CLASS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(th, text="SEM / SECTION", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(th, text="PHONE / EMAIL", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(th, text="SCORE / %", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(th, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=5, padx=8, pady=6, sticky="w")
        ctk.CTkLabel(th, text="SUBMITTED AT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=6, padx=8, pady=6, sticky="w")

        # 5. Table Body Scrollable
        self.table_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    def _create_card(self, parent, col, title, default_val, subtitle, color):
        card = ctk.CTkFrame(parent, fg_color=Theme.BG_INPUT, corner_radius=8)
        card.grid(row=0, column=col, padx=4 if 0 < col < 3 else (0 if col == 0 else (4, 0)), sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)

        ctk.CTkLabel(inner, text=title, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=default_val, font=("Segoe UI", 16, "bold"), text_color=Theme.TEXT_MAIN, anchor="w")
        val_lbl.pack(anchor="w", pady=(1, 1))
        ctk.CTkLabel(inner, text=subtitle, font=("Segoe UI", 8), text_color=color, anchor="w").pack(anchor="w")
        return val_lbl

    def load_data(self):
        ok, res = api_client.get_organizer_results(quiz_id=self.quiz_id)
        if not ok:
            for w in self.table_scroll.winfo_children():
                w.destroy()
            err_box = ctk.CTkFrame(self.table_scroll, fg_color=Theme.DANGER_LIGHT, corner_radius=8)
            err_box.pack(fill="x", padx=10, pady=20)
            ctk.CTkLabel(
                err_box,
                text=f"⚠️ Could not load submissions for this quiz: {res}",
                font=Theme.FONT_BODY,
                text_color=Theme.DANGER,
            ).pack(padx=14, pady=12)
            return

        self.submissions = res if isinstance(res, list) else []

        tot = len(self.submissions)
        passed = sum(1 for s in self.submissions if s.get("is_passed", False))
        failed = sum(1 for s in self.submissions if s.get("status") == "completed" and not s.get("is_passed", False))
        avg_score = int(sum(s.get("percentage", 0) for s in self.submissions) / tot) if tot > 0 else 0

        self.c_tot.configure(text=str(tot))
        self.c_pass.configure(text=str(passed))
        self.c_fail.configure(text=str(failed))
        self.c_avg.configure(text=f"{avg_score}%")

        self._filter_and_render()

    def _on_search(self, event=None):
        self.search_query = self.search_entry.get().strip().lower()
        self._filter_and_render()

    def _on_status_change(self, value):
        self.status_filter = value
        self._filter_and_render()

    def _filter_and_render(self):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        filtered = []
        for s in self.submissions:
            st = s.get("status", "")
            is_pass = s.get("is_passed", False)

            if self.status_filter == "Passed" and not is_pass:
                continue
            if self.status_filter == "Needs Review" and (is_pass or st != "completed"):
                continue
            if self.status_filter == "In Progress" and st != "in_progress":
                continue

            if self.search_query:
                combined = f"{s.get('student_name', '')} {s.get('student_class', '')} {s.get('student_section', '')} {s.get('student_phone', '')} {s.get('student_email', '')}".lower()
                if self.search_query not in combined:
                    continue

            filtered.append(s)

        if not filtered:
            empty_box = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            empty_box.pack(pady=36)
            ctk.CTkLabel(
                empty_box,
                text="No student submissions recorded for this quiz yet.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=(0, 10))

            ctk.CTkButton(
                empty_box,
                text="🔗 Share Quiz Link",
                font=Theme.FONT_SMALL,
                fg_color="#0EA5E9",
                hover_color="#0284C7",
                text_color="#FFFFFF",
                height=30,
                corner_radius=6,
                command=lambda: ShareQuizDialog(self, self.quiz),
            ).pack()
            return

        for idx, s in enumerate(filtered):
            row = ctk.CTkFrame(
                self.table_scroll,
                fg_color=Theme.BG_CARD if idx % 2 == 0 else "#F8FAFC",
                corner_radius=6,
                border_width=1,
                border_color=Theme.BORDER_COLOR,
            )
            row.pack(fill="x", pady=2)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)
            row.grid_columnconfigure(5, weight=2)
            row.grid_columnconfigure(6, weight=2)

            # Student Name + Avatar
            name_box = ctk.CTkFrame(row, fg_color="transparent")
            name_box.grid(row=0, column=0, padx=10, pady=8, sticky="w")
            s_name = s.get("student_name", "Student")
            initial = s_name[0].upper() if s_name else "S"
            ctk.CTkLabel(
                name_box,
                text=f" {initial} ",
                font=("Segoe UI", 8, "bold"),
                fg_color=Theme.PRIMARY_LIGHT,
                text_color=Theme.PRIMARY,
                corner_radius=10,
                width=22,
                height=22,
            ).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(name_box, text=s_name, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left")

            # Class
            ctk.CTkLabel(row, text=s.get("student_class") or "—", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, padx=8, pady=8, sticky="w")

            # Sem / Section
            ctk.CTkLabel(row, text=s.get("student_section") or "—", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, padx=8, pady=8, sticky="w")

            # Phone / Email
            contact = s.get("student_phone") or s.get("student_email") or "—"
            ctk.CTkLabel(row, text=contact, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, padx=8, pady=8, sticky="w")

            # Score & %
            pct = s.get("percentage", 0)
            score_txt = f"{pct}% ({s.get('score_obtained', 0)} / {s.get('total_marks', 0)})"
            ctk.CTkLabel(row, text=score_txt, font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=4, padx=8, pady=8, sticky="w")

            # Status Badge
            st = s.get("status", "")
            is_pass = s.get("is_passed", False)
            if st == "in_progress":
                badge_bg, badge_fg, badge_text = Theme.WARNING_LIGHT, Theme.WARNING, "IN PROGRESS"
            elif is_pass:
                badge_bg, badge_fg, badge_text = Theme.SUCCESS_LIGHT, Theme.SUCCESS, "PASSED"
            else:
                badge_bg, badge_fg, badge_text = Theme.DANGER_LIGHT, Theme.DANGER, "NEEDS REVIEW"

            ctk.CTkLabel(
                row,
                text=f" {badge_text} ",
                font=Theme.FONT_SMALL,
                text_color=badge_fg,
                fg_color=badge_bg,
                corner_radius=4,
            ).grid(row=0, column=5, padx=8, pady=8, sticky="w")

            # Submitted At
            raw_d = s.get("submitted_at") or s.get("end_time") or s.get("start_time") or ""
            d_str = "Recent"
            if raw_d:
                try:
                    clean_d = str(raw_d).replace("T", " ")
                    if "." in clean_d:
                        clean_d = clean_d.split(".")[0]
                    d_str = clean_d
                except Exception:
                    d_str = str(raw_d)[:16]
            ctk.CTkLabel(row, text=d_str, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=6, padx=8, pady=8, sticky="w")

    def _export_csv(self):
        if not self.submissions:
            messagebox.showinfo("Export", "No submissions to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"Submissions_Quiz_{self.quiz_id}_{datetime.now().strftime('%Y%m%d')}.csv",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Student Name", "Class", "Sem / Section", "Contact", "Score", "Total Marks", "Percentage", "Status", "Date Submitted"])
                for s in self.submissions:
                    writer.writerow([
                        s.get("student_name", "Student"),
                        s.get("student_class", ""),
                        s.get("student_section", ""),
                        s.get("student_phone") or s.get("student_email") or "",
                        s.get("score_obtained", 0),
                        s.get("total_marks", 0),
                        f"{s.get('percentage', 0)}%",
                        s.get("status", ""),
                        s.get("submitted_at") or s.get("end_time") or s.get("start_time") or "",
                    ])
            messagebox.showinfo("Export Successful", f"Submissions CSV exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export CSV: {str(e)}")
