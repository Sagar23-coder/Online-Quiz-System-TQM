"""
Admin Results View: Platform-Wide Quiz Attempt Audit Log.
"""
import customtkinter as ctk
from app.utils.theme import Theme
from app.services.api_client import api_client


class AdminResultsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.results = []

        self.pack(fill="both", expand=True, padx=24, pady=20)
        self._build_ui()
        self.load_results()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Assessment Results & Audit Log",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Comprehensive record of student submissions and performance evaluations",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="Refresh Results",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            width=120,
            height=34,
            command=self.load_results,
        ).pack(side="right")

        # Table container
        self.table_card = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        self.table_card.pack(fill="both", expand=True)

        # Header Row
        self.th = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.th.pack(fill="x", padx=16, pady=(12, 8))
        self.th.grid_columnconfigure(0, weight=3)
        self.th.grid_columnconfigure(1, weight=4)
        self.th.grid_columnconfigure(2, weight=2)
        self.th.grid_columnconfigure(3, weight=2)
        self.th.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(self.th, text="STUDENT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self.th, text="ASSESSMENT QUIZ", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(self.th, text="SCORE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(self.th, text="PERCENTAGE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(self.th, text="RESULT", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, sticky="w")

        ctk.CTkFrame(self.table_card, fg_color=Theme.BORDER_COLOR, height=1).pack(fill="x", padx=12, pady=(0, 4))

        self.scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=4, pady=4)

    def load_results(self):
        ok, res = api_client.get_all_results()
        if not ok:
            return

        self.results = res
        for w in self.scroll.winfo_children():
            w.destroy()

        if not self.results:
            ctk.CTkLabel(
                self.scroll,
                text="No quiz attempt results submitted yet.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=40)
            return

        for r in self.results:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=4)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)

            ctk.CTkLabel(row, text=r["student_name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=r["quiz_title"], font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(row, text=f"{r['score_obtained']}/{r['total_marks']}", font=Theme.FONT_BODY, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=2, sticky="w")
            ctk.CTkLabel(row, text=f"{r['percentage']}%", font=Theme.FONT_BODY_BOLD, text_color=Theme.PRIMARY, anchor="w").grid(row=0, column=3, sticky="w")

            is_pass = r["is_passed"]
            badge_color = Theme.SUCCESS if is_pass else Theme.DANGER
            badge_text = "PASSED" if is_pass else "FAILED"
            badge = ctk.CTkLabel(
                row,
                text=f" {badge_text} ",
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MAIN,
                fg_color=badge_color,
                corner_radius=4,
            )
            badge.grid(row=0, column=4, sticky="w")

