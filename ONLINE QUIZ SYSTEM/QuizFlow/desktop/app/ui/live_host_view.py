"""
Live Assessment Host View - Synchronized Classroom Gamified Assessment Workspace.
Enables teachers to host live sessions with PIN codes, advance questions, and view live podiums.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from app.utils.theme import Theme
from app.services.api_client import api_client


class LiveSessionControllerDialog(ctk.CTkToplevel):
    def __init__(self, master, session_info):
        super().__init__(master)
        self.session_info = session_info
        self.pin = session_info["session_pin"]
        self.title(f"Live Quiz Host — {self.pin}")
        self.geometry("640x700")
        self.configure(fg_color=Theme.BG_MAIN)
        self.grab_set()

        self._build_ui()
        self.poll_state()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header with PIN
        pin_banner = ctk.CTkFrame(container, fg_color="#0F172A", corner_radius=10)
        pin_banner.pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkLabel(pin_banner, text="CLASSROOM JOIN PIN", font=("Segoe UI", 10, "bold"), text_color="#94A3B8").pack(pady=(12, 2))
        self.lbl_pin = ctk.CTkLabel(pin_banner, text=self.pin, font=("Segoe UI", 36, "bold"), text_color="#FBBF24")
        self.lbl_pin.pack(pady=(0, 4))
        ctk.CTkLabel(pin_banner, text="Students open: /live or enter PIN to join", font=Theme.FONT_SMALL, text_color="#E2E8F0").pack(pady=(0, 12))

        # Status & Participant count
        stat_row = ctk.CTkFrame(container, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=(0, 12))
        stat_row.grid_columnconfigure((0, 1), weight=1)

        self.lbl_status = ctk.CTkLabel(stat_row, text="Status: LOBBY (Waiting for students)", font=Theme.FONT_BODY_BOLD, text_color=Theme.COLOR_QUIZZES, anchor="w")
        self.lbl_status.grid(row=0, column=0, sticky="w")

        self.lbl_count = ctk.CTkLabel(stat_row, text="👥 0 Participants Joined", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="e")
        self.lbl_count.grid(row=0, column=1, sticky="e")

        # Question Display Box
        self.q_box = ctk.CTkFrame(container, fg_color=Theme.BG_INPUT, corner_radius=8, border_width=1, border_color=Theme.BORDER_COLOR)
        self.q_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.lbl_q_title = ctk.CTkLabel(self.q_box, text="Quiz in Lobby — Click 'Start Assessment' when all students have joined.", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, wraplength=560)
        self.lbl_q_title.pack(expand=True, padx=16, pady=16)

        # Leaderboard Box
        ctk.CTkLabel(container, text="🏆 Live Leaderboard (Top Players)", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x", padx=16, pady=(4, 4))
        self.leaderboard_frame = ctk.CTkFrame(container, fg_color=Theme.BG_MAIN, corner_radius=8, height=120)
        self.leaderboard_frame.pack(fill="x", padx=16, pady=(0, 12))
        self.leaderboard_frame.pack_propagate(False)

        # Action Buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(8, 14))
        btn_box.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_start = ctk.CTkButton(btn_box, text="🚀 Start Assessment", font=Theme.FONT_BODY_BOLD, fg_color=Theme.SUCCESS, hover_color="#059669", height=40, command=self._start_quiz)
        self.btn_start.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_next = ctk.CTkButton(btn_box, text="⏭ Next Question", font=Theme.FONT_BODY_BOLD, fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, height=40, command=self._next_question)
        self.btn_next.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_end = ctk.CTkButton(btn_box, text="🏁 End & Podium", font=Theme.FONT_BODY_BOLD, fg_color=Theme.DANGER, hover_color="#DC2626", height=40, command=self._end_session)
        self.btn_end.grid(row=0, column=2, padx=(4, 0), sticky="ew")

    def poll_state(self):
        ok, res = api_client.get_live_session_state(self.pin)
        if ok and res:
            st = res.get("status", "lobby").upper()
            self.lbl_status.configure(text=f"Status: {st}")
            self.lbl_count.configure(text=f"👥 {res.get('total_participants', 0)} Participants Joined")

            cq = res.get("current_question")
            if cq:
                self.lbl_q_title.configure(
                    text=f"Q{cq['question_index']} of {cq['total_questions']}: {cq['question_text']}\n\n"
                         f"A: {cq['option_a']}   |   B: {cq['option_b']}\n"
                         f"C: {cq['option_c']}   |   D: {cq['option_d']}",
                    font=Theme.FONT_BODY_BOLD,
                    text_color=Theme.TEXT_MAIN,
                )
            elif st == "ENDED":
                self.lbl_q_title.configure(text="Assessment Concluded! Reviewing top winners.", text_color=Theme.COLOR_QUIZZES)

            # Update leaderboard
            for w in self.leaderboard_frame.winfo_children():
                w.destroy()

            lb = res.get("leaderboard", [])
            if not lb:
                ctk.CTkLabel(self.leaderboard_frame, text="Waiting for submissions...", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(expand=True)
            else:
                for p in lb:
                    row = ctk.CTkFrame(self.leaderboard_frame, fg_color="transparent")
                    row.pack(fill="x", padx=10, pady=2)
                    ctk.CTkLabel(row, text=f"#{p['rank']} {p['nickname']}", font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN).pack(side="left")
                    ctk.CTkLabel(row, text=f"{p['score']} pts (🔥 {p.get('streak', 0)})", font=Theme.FONT_SMALL, text_color=Theme.PRIMARY).pack(side="right")

        # Poll every 2 seconds if window is alive
        if self.winfo_exists():
            self.after(2000, self.poll_state)

    def _start_quiz(self):
        ok, _ = api_client.start_live_session(self.pin)
        if ok:
            self.btn_start.configure(state="disabled")

    def _next_question(self):
        ok, res = api_client.next_live_question(self.pin)
        if ok and res.get("status") == "ended":
            messagebox.showinfo("Session Finished", "All assessment questions have been presented!")

    def _end_session(self):
        ok, res = api_client.end_live_session(self.pin)
        if ok:
            podium = res.get("podium", [])
            podium_text = "\n".join([f"{p['rank']}. {p['nickname']} — {p['score']} pts" for p in podium]) or "No participants."
            messagebox.showinfo("Final Podium Winners", f"🏆 Session Concluded!\n\n{podium_text}")
            self.destroy()


class LiveQuizHostView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG_MAIN)
        self.quizzes = []

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

        ctk.CTkLabel(title_box, text="⚡ Live Classroom Assessment Host", font=Theme.FONT_TITLE, text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Host synchronous classroom quizzes with real-time student participation, timers, and speed-scored leaderboards.", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(anchor="w", pady=(2, 0))

        # Quizzes Container
        self.container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.container.pack(fill="both", expand=True, pady=(0, 16))

    def load_data(self):
        ok, res = api_client.get_organizer_quizzes()
        self.quizzes = res if (ok and res) else []
        self._render()

    def _render(self):
        for w in self.container.winfo_children():
            w.destroy()

        if not self.quizzes:
            empty = ctk.CTkFrame(self.container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
            empty.pack(fill="x", pady=24, padx=12)
            ctk.CTkLabel(empty, text="⚡ No Quizzes Available to Host", font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN).pack(pady=(28, 6))
            ctk.CTkLabel(empty, text="Create and add questions to a quiz before launching a live session.", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(pady=(0, 24))
            return

        for q in self.quizzes:
            card = ctk.CTkFrame(self.container, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR)
            card.pack(fill="x", pady=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=18, pady=14)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(left, text=q.get("title", "Untitled Quiz"), font=Theme.FONT_HEADING, text_color=Theme.TEXT_MAIN, anchor="w").pack(fill="x")
            ctk.CTkLabel(left, text=f"{q.get('question_count', 0)} Questions • Subject: {q.get('subject', 'General')} • {q.get('duration_minutes', 15)} Mins", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").pack(fill="x", pady=(2, 0))

            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right", padx=(12, 0))

            ctk.CTkButton(
                right,
                text="⚡ Launch Live Session",
                font=Theme.FONT_BODY_BOLD,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                text_color="#FFFFFF",
                height=36,
                corner_radius=8,
                command=lambda q_id=q["id"]: self._launch_live(q_id),
            ).pack(side="right")

    def _launch_live(self, quiz_id: int):
        ok, res = api_client.create_live_session(quiz_id)
        if ok and res:
            LiveSessionControllerDialog(self, session_info=res)
        else:
            messagebox.showerror("Error", str(res))
