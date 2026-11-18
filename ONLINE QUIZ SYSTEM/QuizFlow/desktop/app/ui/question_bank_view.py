"""
Question Bank View - Dedicated Teacher Question Repository & Taxonomy Workspace.
Provides question bank creation, categorization by topic & difficulty, and transfer/import into quizzes.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client


class CreateBankDialog(ctk.CTkToplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title("Create Question Bank — QuizFlow")
        self.geometry("480x520")
        self.configure(fg_color=Theme.BG_MAIN)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(container, text="📚 Create Question Bank", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(12, 16))

        # Title
        ctk.CTkLabel(container, text="Repository Title *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.title_entry = ctk.CTkEntry(container, placeholder_text="e.g. Data Structures & Algorithms Question Pool", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.title_entry.pack(fill="x", padx=16, pady=(0, 10))

        # Subject & Topic
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 10))
        row1.grid_columnconfigure((0, 1), weight=1)

        c1 = ctk.CTkFrame(row1, fg_color="transparent")
        c1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(c1, text="Subject *", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.subj_entry = ctk.CTkEntry(c1, placeholder_text="e.g. Computer Science", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.subj_entry.pack(fill="x", pady=(2, 0))

        c2 = ctk.CTkFrame(row1, fg_color="transparent")
        c2.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(c2, text="Topic / Chapter", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.topic_entry = ctk.CTkEntry(c2, placeholder_text="e.g. Binary Search Trees", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.topic_entry.pack(fill="x", pady=(2, 0))

        # Difficulty & Grade
        row2 = ctk.CTkFrame(container, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 10))
        row2.grid_columnconfigure((0, 1), weight=1)

        c3 = ctk.CTkFrame(row2, fg_color="transparent")
        c3.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkLabel(c3, text="Difficulty Level", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.diff_seg = ctk.CTkSegmentedButton(c3, values=["easy", "medium", "hard"], height=34)
        self.diff_seg.set("medium")
        self.diff_seg.pack(fill="x", pady=(2, 0))

        c4 = ctk.CTkFrame(row2, fg_color="transparent")
        c4.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        ctk.CTkLabel(c4, text="Target Grade / Semester", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x")
        self.grade_entry = ctk.CTkEntry(c4, placeholder_text="e.g. 5th Semester", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=34)
        self.grade_entry.pack(fill="x", pady=(2, 0))

        # Description
        ctk.CTkLabel(container, text="Description (Optional)", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(4, 2))
        self.desc_entry = ctk.CTkEntry(container, placeholder_text="Notes or syllabus references", fg_color=Theme.BG_INPUT, border_color=Theme.BORDER_COLOR, height=36)
        self.desc_entry.pack(fill="x", padx=16, pady=(0, 16))

        # Error Banner
        self.err_lbl = ctk.CTkLabel(container, text="", font=Theme.FONT_SMALL, text_color=Theme.DANGER)
        self.err_lbl.pack(pady=4)

        # Buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(8, 14))
        btn_box.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_box, text="✕ Cancel", font=Theme.FONT_BODY, fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_MAIN, hover_color=Theme.BORDER_COLOR, height=38, command=self.destroy).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(btn_box, text="✓ Create Repository", font=Theme.FONT_BODY_BOLD, fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, text_color="#FFFFFF", height=38, command=self._handle_create).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _handle_create(self):
        title = self.title_entry.get().strip()
        subj = self.subj_entry.get().strip() or "General"
        topic = self.topic_entry.get().strip()
        diff = self.diff_seg.get()
        grade = self.grade_entry.get().strip()
        desc = self.desc_entry.get().strip()

        if not title or len(title) < 3:
            self.err_lbl.configure(text="Title must be at least 3 characters.")
            return

        ok, res = api_client.create_question_bank({
            "title": title,
            "subject": subj,
            "topic": topic or None,
            "difficulty": diff,
            "grade_level": grade or None,
            "description": desc or None,
        })

        if ok:
            messagebox.showinfo("Success", "Question Bank created successfully!")
            self.destroy()
            self.on_success()
        else:
            self.err_lbl.configure(text=str(res))


class QuestionBankView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.banks = []

        self.pack(fill="both", expand=True)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_MAIN)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=16)

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # Header Row
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(title_box, text="Curriculum Question Banks", font=Theme.FONT_TITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Organize, curate, and reuse questions across multiple exams and academic terms.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")

        ctk.CTkButton(btn_box, text="🔄 Refresh", font=Theme.FONT_BODY_BOLD, fg_color=Theme.BG_CARD, hover_color=Theme.BORDER_COLOR, text_color=Theme.TEXT_MAIN, border_width=1, border_color=Theme.BORDER_COLOR, width=90, height=34, corner_radius=8, command=self.load_data).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_box, text="+ Create Question Bank", font=Theme.FONT_BODY_BOLD, fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, text_color="#FFFFFF", height=34, corner_radius=8, command=self._open_create_bank).pack(side="left")

        # Banks Container
        self.banks_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.banks_container.pack(fill="both", expand=True, pady=(0, 16))

    def _open_create_bank(self):
        CreateBankDialog(self, on_success=self.load_data)

    def load_data(self):
        ok, res = api_client.get_question_banks()
        self.banks = res if (ok and res) else []
        self._render_banks()

    def _render_banks(self):
        for w in self.banks_container.winfo_children():
            w.destroy()

        if not self.banks:
            empty_card = ctk.CTkFrame(self.banks_container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
            empty_card.pack(fill="x", pady=24, padx=12)
            ctk.CTkLabel(empty_card, text="📚 No Question Banks Found", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(28, 6))
            ctk.CTkLabel(empty_card, text="Create your first question repository to store reusable exam questions by subject and topic.", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(pady=(0, 20))
            ctk.CTkButton(empty_card, text="+ Create Question Bank", font=Theme.FONT_BODY_BOLD, fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, text_color="#FFFFFF", height=36, width=200, corner_radius=8, command=self._open_create_bank).pack(pady=(0, 28))
            return

        for bank in self.banks:
            card = ctk.CTkFrame(self.banks_container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
            card.pack(fill="x", pady=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=18, pady=14)

            # Left Info
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            tag_row = ctk.CTkFrame(left, fg_color="transparent")
            tag_row.pack(anchor="w", pady=(0, 4))

            ctk.CTkLabel(tag_row, text=f" {bank.get('subject', 'General').upper()} ", font=("Segoe UI", 9, "bold"), fg_color=Theme.PRIMARY_LIGHT, text_color=Theme.PRIMARY, corner_radius=4).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(tag_row, text=f" {bank.get('difficulty', 'medium').upper()} ", font=("Segoe UI", 9, "bold"), fg_color=Theme.BG_INPUT, text_color=Theme.TEXT_MUTED, corner_radius=4).pack(side="left", padx=(0, 6))

            ctk.CTkLabel(left, text=bank.get("title", "Untitled Bank"), font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")

            meta_text = f"Topic: {bank.get('topic') or 'All Topics'} • {bank.get('item_count', 0)} Questions Available"
            if bank.get("grade_level"):
                meta_text += f" • Grade: {bank['grade_level']}"
            ctk.CTkLabel(left, text=meta_text, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(2, 0))

            # Right Actions
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right", padx=(12, 0))

            ctk.CTkButton(
                right,
                text="🗑️ Delete",
                font=Theme.FONT_SMALL,
                fg_color=Theme.DANGER_LIGHT,
                hover_color=Theme.BORDER_COLOR,
                text_color=Theme.DANGER,
                width=80,
                height=32,
                corner_radius=6,
                command=lambda b=bank: self._delete_bank(b["id"]),
            ).pack(side="right")

    def _delete_bank(self, bank_id: int):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this Question Bank?"):
            ok, res = api_client.delete_question_bank(bank_id)
            if ok:
                self.load_data()
            else:
                messagebox.showerror("Error", str(res))
