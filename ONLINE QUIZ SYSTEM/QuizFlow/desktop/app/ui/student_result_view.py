"""
Student Results and Review Screen: Score Breakdown and Question-by-Question Review.
"""
import customtkinter as ctk
from app.utils.theme import Theme


class StudentResultView(ctk.CTkFrame):
    def __init__(self, master, result_data, on_back_to_dashboard):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.result = result_data
        self.on_back_to_dashboard = on_back_to_dashboard

        self.pack(fill="both", expand=True, padx=28, pady=24)
        self._build_ui()

    def _build_ui(self):
        # Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=f"Assessment Results: {self.result['quiz_title']}",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Detailed score report, performance breakdown, and question solutions",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="← Return to Dashboard",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=36,
            corner_radius=8,
            command=self.on_back_to_dashboard,
        ).pack(side="right")

        # Top Score Summary Card
        is_pass = self.result["is_passed"]
        banner_bg = Theme.SUCCESS_BG if is_pass else Theme.DANGER_BG
        banner_border = Theme.SUCCESS if is_pass else Theme.DANGER
        verdict_text = "CONGRATULATIONS, YOU PASSED!" if is_pass else "ASSESSMENT NOT PASSED"

        score_card = ctk.CTkFrame(
            self,
            fg_color=banner_bg,
            corner_radius=10,
            border_width=1,
            border_color=banner_border,
        )
        score_card.pack(fill="x", pady=(0, 20))

        inner_score = ctk.CTkFrame(score_card, fg_color="transparent")
        inner_score.pack(fill="both", expand=True, padx=24, pady=18)

        ctk.CTkLabel(
            inner_score,
            text=verdict_text,
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        # Metrics stats row
        stats_row = ctk.CTkFrame(inner_score, fg_color="transparent")
        stats_row.pack(fill="x", pady=(10, 0))

        metrics = [
            f"🎯 Score: {self.result['score_obtained']} / {self.result['total_marks']}",
            f"📊 Percentage: {self.result['percentage']}%",
            f"🏆 Required: {self.result['passing_percentage']}%",
            f"✓ Correct: {self.result['correct_count']}",
            f"✗ Incorrect: {self.result['incorrect_count']}",
            f"⚪ Skipped: {self.result['unattempted_count']}",
        ]

        for m in metrics:
            ctk.CTkLabel(
                stats_row,
                text=m,
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.TEXT_MAIN,
                fg_color=Theme.BG_INPUT,
                corner_radius=6,
                padx=10,
                pady=4,
            ).pack(side="left", padx=(0, 10))

        # Question Review Section or Held Banner
        is_released = self.result.get("results_released", True)
        reviews = self.result.get("review", [])

        if not is_released:
            held_card = ctk.CTkFrame(
                self,
                fg_color="#FEF3C7",
                corner_radius=10,
                border_width=1,
                border_color=Theme.WARNING,
            )
            held_card.pack(fill="x", pady=(0, 16))
            ctk.CTkLabel(
                held_card,
                text="🔒 Detailed Answer Review Pending\nThe quiz organizer has configured answer reviews to be released after submission evaluation. Check back soon for full question solutions.",
                font=Theme.FONT_BODY_BOLD,
                text_color="#92400E",
                padx=20,
                pady=16,
                justify="left",
            ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                self,
                text="Question Solutions & Explanation Breakdown",
                font=Theme.FONT_HEADING,
                text_color=Theme.TEXT_MAIN,
            ).pack(anchor="w", pady=(8, 10))

            review_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
            review_scroll.pack(fill="both", expand=True)

            for idx, item in enumerate(reviews, start=1):
                self._render_review_item(review_scroll, idx, item)

    def _render_review_item(self, parent, idx: int, item: dict):
        is_correct = item["is_correct"]
        skipped = item["selected_option"] is None

        card = ctk.CTkFrame(
            parent,
            fg_color=Theme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        card.pack(fill="x", pady=8, padx=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=14)

        # Header
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            top_row,
            text=f"Q{idx}.  {item['question_text']}",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN,
            anchor="w",
            wraplength=620,
        ).pack(side="left", fill="x", expand=True)

        # Result badge
        if skipped:
            badge_text = "SKIPPED (0 Marks)"
            badge_color = Theme.TEXT_DIM
        elif is_correct:
            badge_text = f"CORRECT (+{item['marks_awarded']} Marks)"
            badge_color = Theme.SUCCESS
        else:
            badge_text = "INCORRECT (0 Marks)"
            badge_color = Theme.DANGER

        ctk.CTkLabel(
            top_row,
            text=f" {badge_text} ",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MAIN,
            fg_color=badge_color,
            corner_radius=4,
        ).pack(side="right")

        # Options List
        options = [
            ("A", item.get("option_a", "")),
            ("B", item.get("option_b", "")),
            ("C", item.get("option_c", "")),
            ("D", item.get("option_d", "")),
        ]

        correct_opt = item.get("correct_option", "")
        user_opt = item.get("selected_option")

        opt_grid = ctk.CTkFrame(inner, fg_color="transparent")
        opt_grid.pack(fill="x", pady=(4, 8))
        opt_grid.grid_columnconfigure(0, weight=1)
        opt_grid.grid_columnconfigure(1, weight=1)

        for i, (letter, text) in enumerate(options):
            r = i // 2
            c = i % 2

            is_this_correct = letter == correct_opt
            is_this_selected = letter == user_opt

            prefix = ""
            if is_this_correct:
                prefix = "✓ (Correct) "
                bg = Theme.SUCCESS_BG
                fg = Theme.SUCCESS
            elif is_this_selected and not is_correct:
                prefix = "✗ (Your Answer) "
                bg = Theme.DANGER_BG
                fg = Theme.DANGER
            else:
                bg = Theme.BG_INPUT
                fg = Theme.TEXT_MUTED

            lbl = ctk.CTkLabel(
                opt_grid,
                text=f"{prefix}({letter}) {text}",
                font=Theme.FONT_BODY,
                text_color=fg,
                fg_color=bg,
                corner_radius=6,
                anchor="w",
                padx=10,
                pady=6,
            )
            lbl.grid(row=r, column=c, padx=4, pady=3, sticky="ew")

        # Explanation
        if item.get("explanation"):
            ctk.CTkLabel(
                inner,
                text=f"💡 Solution Explanation: {item['explanation']}",
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_DIM,
                anchor="w",
                wraplength=650,
            ).pack(fill="x", pady=(4, 0))

