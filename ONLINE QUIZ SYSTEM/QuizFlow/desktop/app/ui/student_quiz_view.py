"""
Student Quiz-Taking Screen - Exact implementation of the Exam Assessment UI.
Features:
- Top Summary Bar with Exam Type, Subject, Completed Progress (X/Y) %, and Green 'Submit Answer' button
- Question Area with Question Badge, Bookmark icon, Large Question Text
- Clean Option Cards (A, B, C, D) with Royal Purple/Indigo active selected state
- Bottom Navigation: First, Back, Current (e.g. '1 / 4' purple pill), Next, Last
- Right Sidebar: Circular Countdown Timer Gauge ('Timer Remaining:'), View Bookmarked/Unanswered filters, and Pagination Numbers.
"""
from datetime import datetime, timezone, timedelta
from tkinter import messagebox
import customtkinter as ctk
from app.utils.theme import Theme
from app.components.visual_charts import CircularProgress
from app.services.api_client import api_client


class StudentQuizView(ctk.CTkFrame):
    def __init__(self, master, attempt_data, on_finish_quiz):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.attempt = attempt_data
        self.attempt_id = attempt_data.get("attempt_id") or attempt_data.get("id")
        self.on_finish_quiz = on_finish_quiz

        self.questions = attempt_data.get("questions", [])
        self.saved_answers = {int(k): v for k, v in attempt_data.get("saved_answers", {}).items()}
        self.bookmarked = set()
        self.current_idx = 0
        self.timer_id = None
        self.is_submitting = False

        # Parse deadline safely
        deadline_raw = attempt_data.get("deadline_time") or attempt_data.get("deadline_at")
        if isinstance(deadline_raw, str):
            try:
                self.deadline = datetime.fromisoformat(deadline_raw.replace("Z", "+00:00"))
            except Exception:
                self.deadline = datetime.now(timezone.utc) + timedelta(minutes=attempt_data.get("duration_minutes", 15))
        elif isinstance(deadline_raw, datetime):
            self.deadline = deadline_raw
        else:
            self.deadline = datetime.now(timezone.utc) + timedelta(minutes=attempt_data.get("duration_minutes", 15))

        if self.deadline.tzinfo is None:
            self.deadline = self.deadline.replace(tzinfo=timezone.utc)

        self.total_seconds = attempt_data.get("duration_minutes", 15) * 60

        self.pack(fill="both", expand=True)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=Theme.BG_MAIN)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=16)

        self._build_ui()
        self._start_timer()
        self._show_question(0)

    def _build_ui(self):
        # 1. Top Exam Summary Card (White card spanning top)
        self.top_summary_card = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        self.top_summary_card.pack(fill="x", pady=(0, 20))

        inner_summary = ctk.CTkFrame(self.top_summary_card, fg_color="transparent")
        inner_summary.pack(fill="x", padx=20, pady=14)

        # Left Info Columns
        left_cols = ctk.CTkFrame(inner_summary, fg_color="transparent")
        left_cols.pack(side="left", fill="x", expand=True)

        # Exam Type
        col_type = ctk.CTkFrame(left_cols, fg_color="transparent")
        col_type.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(col_type, text="Exam Type", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        t_box = ctk.CTkFrame(col_type, fg_color="transparent")
        t_box.pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(t_box, text="⏱  Online Assessment", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(side="left")

        # Divider 1
        ctk.CTkFrame(left_cols, fg_color=Theme.BORDER_COLOR, width=1, height=36).pack(side="left", padx=16)

        # Subject
        col_subj = ctk.CTkFrame(left_cols, fg_color="transparent")
        col_subj.pack(side="left", padx=16)
        ctk.CTkLabel(col_subj, text="Subject / Quiz", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        s_box = ctk.CTkFrame(col_subj, fg_color="transparent")
        s_box.pack(anchor="w", pady=(2, 0))
        quiz_title = self.attempt.get("quiz_title", "General Quiz")
        if len(quiz_title) > 24:
            quiz_title = quiz_title[:22] + "..."
        ctk.CTkLabel(s_box, text=f"⏱  {quiz_title}", font=Theme.FONT_SUBTITLE, text_color=Theme.TEXT_MAIN).pack(side="left")

        # Divider 2
        ctk.CTkFrame(left_cols, fg_color=Theme.BORDER_COLOR, width=1, height=36).pack(side="left", padx=16)

        # Completed Progress
        col_prog = ctk.CTkFrame(left_cols, fg_color="transparent")
        col_prog.pack(side="left", fill="x", expand=True, padx=16)

        prog_top = ctk.CTkFrame(col_prog, fg_color="transparent")
        prog_top.pack(fill="x")
        self.lbl_completed_text = ctk.CTkLabel(
            prog_top,
            text=f"Completed (0/{len(self.questions)})",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.lbl_completed_text.pack(side="left")

        self.lbl_completed_pct = ctk.CTkLabel(
            prog_top,
            text="0%",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.TEXT_MAIN,
        )
        self.lbl_completed_pct.pack(side="right")

        self.summary_pbar = ctk.CTkProgressBar(
            col_prog,
            height=6,
            corner_radius=3,
            fg_color="#E2E8F0",
            progress_color=Theme.SUCCESS,
        )
        self.summary_pbar.pack(fill="x", pady=(4, 0))
        self.summary_pbar.set(0.0)

        # Right: Green 'Submit Answer' button (matching design)
        self.btn_submit_top = ctk.CTkButton(
            inner_summary,
            text="Submit Answer",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#1E7A66",  # Emerald teal
            hover_color="#166534",
            text_color="#FFFFFF",
            width=140,
            height=42,
            corner_radius=22,
            command=self._handle_submit_click,
        )
        self.btn_submit_top.pack(side="right", padx=(20, 0))

        # 2. Main Two-Column Layout
        main_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        main_grid.pack(fill="both", expand=True)
        main_grid.grid_columnconfigure(0, weight=7)  # Question Card (70%)
        main_grid.grid_columnconfigure(1, weight=3)  # Sidebar (30%)

        # Left Column: Question Container
        left_container = ctk.CTkFrame(main_grid, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        # Question Header (Pill badge + Bookmark)
        q_meta_row = ctk.CTkFrame(left_container, fg_color="transparent")
        q_meta_row.pack(fill="x", pady=(4, 12))

        self.pill_question_num = ctk.CTkLabel(
            q_meta_row,
            text="Question: 1",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            fg_color="#F1F5F9",
            corner_radius=12,
            padx=12,
            pady=4,
        )
        self.pill_question_num.pack(side="left")

        # Bookmark button
        self.btn_bookmark = ctk.CTkButton(
            q_meta_row,
            text="🔖",
            font=("Segoe UI", 13),
            width=36,
            height=36,
            corner_radius=18,
            fg_color=Theme.PRIMARY_LIGHT,
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.PRIMARY,
            command=self._toggle_bookmark,
        )
        self.btn_bookmark.pack(side="right")

        # Question Statement Text
        self.lbl_question_text = ctk.CTkLabel(
            left_container,
            text="",
            font=("Segoe UI", 18, "bold"),
            text_color=Theme.TEXT_MAIN,
            wraplength=640,
            justify="left",
            anchor="w",
        )
        self.lbl_question_text.pack(fill="x", pady=(0, 20))

        # Option Cards Container (A, B, C, D)
        self.option_cards = {}
        for letter in ["A", "B", "C", "D"]:
            card = ctk.CTkFrame(
                left_container,
                fg_color=Theme.BG_CARD,
                corner_radius=10,
                border_width=1,
                border_color=Theme.BORDER_COLOR,
                cursor="hand2",
            )
            card.pack(fill="x", pady=6)

            inner_opt = ctk.CTkFrame(card, fg_color="transparent")
            inner_opt.pack(fill="x", padx=16, pady=14)

            # Left square letter badge
            badge = ctk.CTkLabel(
                inner_opt,
                text=letter,
                font=Theme.FONT_BODY_BOLD,
                fg_color="#F1F5F9",
                text_color=Theme.TEXT_MAIN,
                corner_radius=6,
                width=32,
                height=32,
            )
            badge.pack(side="left", padx=(0, 14))

            # Option Text
            opt_text = ctk.CTkLabel(
                inner_opt,
                text="",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MAIN,
                anchor="w",
                justify="left",
                wraplength=520,
            )
            opt_text.pack(side="left", fill="x", expand=True)

            # Bind clicks
            for w in (card, inner_opt, badge, opt_text):
                w.bind("<Button-1>", lambda e, l=letter: self._select_option(l))

            self.option_cards[letter] = {
                "card": card,
                "badge": badge,
                "text": opt_text,
            }

        # Bottom Pagination Bar: [First] [Back] [ 1 / N ] [Next] [Last]
        bot_nav = ctk.CTkFrame(left_container, fg_color="transparent")
        bot_nav.pack(anchor="w", pady=(24, 16))

        self.btn_first = ctk.CTkButton(
            bot_nav,
            text="First",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F8FAFC",
            hover_color="#E2E8F0",
            text_color="#1E293B",
            border_width=1,
            border_color="#CBD5E1",
            width=65,
            height=32,
            corner_radius=6,
            command=lambda: self._show_question(0),
        )
        self.btn_first.pack(side="left", padx=(0, 6))

        self.btn_back = ctk.CTkButton(
            bot_nav,
            text="Back",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F8FAFC",
            hover_color="#E2E8F0",
            text_color="#1E293B",
            border_width=1,
            border_color="#CBD5E1",
            width=65,
            height=32,
            corner_radius=6,
            command=self._prev_question,
        )
        self.btn_back.pack(side="left", padx=(0, 6))

        # Active Question Purple Pill [ 1 / N ]
        self.pill_active_nav = ctk.CTkLabel(
            bot_nav,
            text=f"1 / {len(self.questions)}",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            text_color="#FFFFFF",
            corner_radius=6,
            padx=14,
            pady=6,
        )
        self.pill_active_nav.pack(side="left", padx=(0, 6))

        self.btn_next = ctk.CTkButton(
            bot_nav,
            text="Next",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F8FAFC",
            hover_color="#E2E8F0",
            text_color="#1E293B",
            border_width=1,
            border_color="#CBD5E1",
            width=65,
            height=32,
            corner_radius=6,
            command=self._next_question,
        )
        self.btn_next.pack(side="left", padx=(0, 6))

        self.btn_last = ctk.CTkButton(
            bot_nav,
            text="Last",
            font=Theme.FONT_BODY_BOLD,
            fg_color="#F8FAFC",
            hover_color="#E2E8F0",
            text_color="#1E293B",
            border_width=1,
            border_color="#CBD5E1",
            width=65,
            height=32,
            corner_radius=6,
            command=lambda: self._show_question(len(self.questions) - 1),
        )
        self.btn_last.pack(side="left")

        # Right Column: Sidebar (Timer Card & Action Buttons)
        right_sidebar = ctk.CTkFrame(main_grid, fg_color="transparent")
        right_sidebar.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Timer Card
        timer_card = ctk.CTkFrame(
            right_sidebar,
            fg_color=Theme.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        timer_card.pack(fill="x", pady=(0, 16))

        inner_timer = ctk.CTkFrame(timer_card, fg_color="transparent")
        inner_timer.pack(fill="both", expand=True, padx=20, pady=20)

        # Circular Timer Gauge
        self.timer_gauge = CircularProgress(
            inner_timer,
            percentage=100.0,
            size=110,
            ring_width=10,
            ring_color="#10B981",  # Emerald green
            track_color="#E2E8F0",
            label="0:00",
        )
        self.timer_gauge.pack(pady=(0, 8))

        ctk.CTkLabel(
            inner_timer,
            text="Timer Remaining:",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack()

        # Action Buttons Card
        action_card = ctk.CTkFrame(
            right_sidebar,
            fg_color=Theme.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
        )
        action_card.pack(fill="x")

        inner_act = ctk.CTkFrame(action_card, fg_color="transparent")
        inner_act.pack(fill="both", expand=True, padx=18, pady=18)

        # View Bookmarked (Purple)
        ctk.CTkButton(
            inner_act,
            text="View Bookmarked",
            font=Theme.FONT_BODY_BOLD,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            height=36,
            corner_radius=18,
            command=self._view_bookmarked,
        ).pack(fill="x", pady=(0, 10))

        # View Un Answered (Outline)
        ctk.CTkButton(
            inner_act,
            text="View Un Answered",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=36,
            corner_radius=18,
            command=self._view_unanswered,
        ).pack(fill="x", pady=(0, 10))

        # Save for Revision (Outline)
        ctk.CTkButton(
            inner_act,
            text="Save for Revision",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            text_color=Theme.TEXT_MAIN,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            height=36,
            corner_radius=18,
            command=self._toggle_bookmark,
        ).pack(fill="x", pady=(0, 16))

        # Question Mini Palette Navigation (< 1 2 3 4 >)
        self.palette_bar = ctk.CTkFrame(inner_act, fg_color="transparent")
        self.palette_bar.pack(anchor="center")

        ctk.CTkButton(
            self.palette_bar,
            text="<",
            font=Theme.FONT_SMALL,
            fg_color="#F1F5F9",
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MUTED,
            width=28,
            height=28,
            corner_radius=4,
            command=self._prev_question,
        ).pack(side="left", padx=2)

        self.palette_pills = []
        for i in range(len(self.questions)):
            btn = ctk.CTkButton(
                self.palette_bar,
                text=str(i + 1),
                font=Theme.FONT_SMALL,
                fg_color=Theme.BG_CARD,
                hover_color=Theme.PRIMARY_LIGHT,
                text_color=Theme.TEXT_MAIN,
                border_width=1,
                border_color=Theme.BORDER_COLOR,
                width=28,
                height=28,
                corner_radius=4,
                command=lambda idx=i: self._show_question(idx),
            )
            btn.pack(side="left", padx=2)
            self.palette_pills.append(btn)

        ctk.CTkButton(
            self.palette_bar,
            text=">",
            font=Theme.FONT_SMALL,
            fg_color="#F1F5F9",
            hover_color=Theme.BORDER_COLOR,
            text_color=Theme.TEXT_MUTED,
            width=28,
            height=28,
            corner_radius=4,
            command=self._next_question,
        ).pack(side="left", padx=2)

    def _show_question(self, index: int):
        self.current_idx = index
        q = self.questions[index]

        self.pill_question_num.configure(text=f"Question: {index + 1}")
        self.lbl_question_text.configure(text=q["question_text"])
        self.pill_active_nav.configure(text=f"{index + 1} / {len(self.questions)}")

        # Update options text
        opts = [
            ("A", q["option_a"]),
            ("B", q["option_b"]),
            ("C", q["option_c"]),
            ("D", q["option_d"]),
        ]

        selected_opt = self.saved_answers.get(q["id"])

        for letter, text in opts:
            item = self.option_cards[letter]
            item["text"].configure(text=text)

            is_selected = selected_opt == letter
            if is_selected:
                # Purple Selected State matching design
                item["card"].configure(fg_color=Theme.PRIMARY, border_color=Theme.PRIMARY)
                item["badge"].configure(fg_color="#FFFFFF", text_color=Theme.PRIMARY)
                item["text"].configure(text_color="#FFFFFF", font=Theme.FONT_BODY_BOLD)
            else:
                # Clean White unselected state
                item["card"].configure(fg_color=Theme.BG_CARD, border_color=Theme.BORDER_COLOR)
                item["badge"].configure(fg_color="#F1F5F9", text_color=Theme.TEXT_MAIN)
                item["text"].configure(text_color=Theme.TEXT_MAIN, font=Theme.FONT_BODY)

        # Update bookmark icon
        is_bookmarked = q["id"] in self.bookmarked
        self.btn_bookmark.configure(
            fg_color=Theme.PRIMARY if is_bookmarked else Theme.PRIMARY_LIGHT,
            text_color="#FFFFFF" if is_bookmarked else Theme.PRIMARY,
        )

        # Update completion progress in top summary bar
        answered_count = len([v for v in self.saved_answers.values() if v])
        pct = (answered_count / len(self.questions)) * 100.0 if self.questions else 0.0
        self.lbl_completed_text.configure(text=f"Completed ({answered_count}/{len(self.questions)})")
        self.lbl_completed_pct.configure(text=f"{int(pct)}%")
        self.summary_pbar.set(pct / 100.0)

        # Update palette pill borders
        for i, btn in enumerate(self.palette_pills):
            qid = self.questions[i]["id"]
            if i == self.current_idx:
                btn.configure(border_color=Theme.PRIMARY, border_width=2, text_color=Theme.PRIMARY)
            elif qid in self.saved_answers and self.saved_answers[qid]:
                btn.configure(border_color=Theme.SUCCESS, border_width=1, text_color=Theme.SUCCESS)
            else:
                btn.configure(border_color=Theme.BORDER_COLOR, border_width=1, text_color=Theme.TEXT_MAIN)

    def _select_option(self, letter: str):
        q = self.questions[self.current_idx]
        self.saved_answers[q["id"]] = letter
        self._show_question(self.current_idx)

        # Autosave immediately to server
        api_client.save_answer(
            attempt_id=self.attempt_id,
            question_id=q["id"],
            selected_option=letter,
        )

    def _toggle_bookmark(self):
        q = self.questions[self.current_idx]
        if q["id"] in self.bookmarked:
            self.bookmarked.remove(q["id"])
        else:
            self.bookmarked.add(q["id"])
        self._show_question(self.current_idx)

    def _view_bookmarked(self):
        for i, q in enumerate(self.questions):
            if q["id"] in self.bookmarked:
                self._show_question(i)
                return

    def _view_unanswered(self):
        for i, q in enumerate(self.questions):
            if q["id"] not in self.saved_answers or not self.saved_answers[q["id"]]:
                self._show_question(i)
                return

    def _prev_question(self):
        if self.current_idx > 0:
            self._show_question(self.current_idx - 1)

    def _next_question(self):
        if self.current_idx < len(self.questions) - 1:
            self._show_question(self.current_idx + 1)

    def _start_timer(self):
        self._tick_timer()

    def _tick_timer(self):
        now = datetime.now(timezone.utc)
        diff = (self.deadline - now).total_seconds()

        if diff <= 0:
            self.timer_gauge.set_percentage(0, center_text="00:00")
            self._auto_submit_expired()
            return

        minutes = int(diff // 60)
        seconds = int(diff % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        pct = max(0.0, min(100.0, (diff / self.total_seconds) * 100.0))
        self.timer_gauge.set_percentage(pct, center_text=time_str)

        self.timer_id = self.after(1000, self._tick_timer)

    def _handle_submit_click(self):
        answered = len([v for v in self.saved_answers.values() if v])
        unanswered = len(self.questions) - answered
        msg = "Are you sure you want to finish and submit your quiz?"
        if unanswered > 0:
            msg = f"You have {unanswered} unanswered question(s).\nAre you sure you want to finalize and submit?"

        if messagebox.askyesno("Submit Assessment", msg):
            self._submit_attempt()

    def _auto_submit_expired(self):
        if not self.is_submitting:
            self._submit_attempt()

    def _submit_attempt(self):
        if self.is_submitting:
            return
        self.is_submitting = True

        if self.timer_id:
            self.after_cancel(self.timer_id)

        self.btn_submit_top.configure(state="disabled", text="Grading...")
        ok, res = api_client.finish_quiz(self.attempt_id)

        if ok:
            self.on_finish_quiz(res)
        else:
            ok_res, res_data = api_client.get_result(self.attempt_id)
            if ok_res:
                self.on_finish_quiz(res_data)
            else:
                self.btn_submit_top.configure(state="normal", text="Submit Answer")
                self.is_submitting = False

    def destroy(self):
        if self.timer_id:
            try:
                self.after_cancel(self.timer_id)
            except Exception:
                pass
        super().destroy()
