"""
Admin User Management View: Users Directory, Role Filtering, and Account Suspension.
"""
from tkinter import messagebox
import customtkinter as ctk
from app.utils.theme import Theme
from app.services.api_client import api_client


class AdminStudentsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Theme.BG_DARK)
        self.users = []
        self.role_filter = "All"

        self.pack(fill="both", expand=True, padx=24, pady=20)
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="User Management & Moderation",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MAIN,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Platform users directory: Monitor accounts, review roles, suspend or reactivate access",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side="right")

        # Role filter segmented button
        self.filter_btn = ctk.CTkSegmentedButton(
            right_box,
            values=["All", "Participants", "Organizers", "Admins"],
            command=self._on_filter_changed,
            selected_color=Theme.PRIMARY,
            unselected_color=Theme.BG_CARD,
            text_color=Theme.TEXT_MAIN,
            font=Theme.FONT_SMALL,
            height=32,
        )
        self.filter_btn.set("All")
        self.filter_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            right_box,
            text="🔄 Refresh",
            font=Theme.FONT_SMALL,
            fg_color=Theme.BG_CARD,
            hover_color=Theme.BG_CARD_HOVER,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            width=90,
            height=32,
            command=self.load_users,
        ).pack(side="left")

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
        self.th.grid_columnconfigure(1, weight=3)
        self.th.grid_columnconfigure(2, weight=2)
        self.th.grid_columnconfigure(3, weight=2)
        self.th.grid_columnconfigure(4, weight=2)
        self.th.grid_columnconfigure(5, weight=2)

        ctk.CTkLabel(self.th, text="USER NAME", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self.th, text="EMAIL ADDRESS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(self.th, text="ROLE", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(self.th, text="ACTIVITY", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(self.th, text="STATUS", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=4, sticky="w")
        ctk.CTkLabel(self.th, text="MODERATION", font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=5, sticky="w")

        ctk.CTkFrame(self.table_card, fg_color=Theme.BORDER_COLOR, height=1).pack(fill="x", padx=12, pady=(0, 4))

        self.scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=4, pady=4)

    def _on_filter_changed(self, value):
        self.role_filter = value
        self.render_rows()

    def load_users(self):
        ok, res = api_client.get_admin_users()
        if not ok:
            # Fallback to students
            ok_s, res_s = api_client.get_students()
            if ok_s:
                self.users = res_s
            else:
                self.users = []
        else:
            self.users = res

        self.render_rows()

    def render_rows(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        filtered = []
        for u in self.users:
            role = u.get("role", "participant").lower()
            if self.role_filter == "Participants" and role not in ("participant", "student"):
                continue
            if self.role_filter == "Organizers" and role != "organizer":
                continue
            if self.role_filter == "Admins" and role != "admin":
                continue
            filtered.append(u)

        if not filtered:
            ctk.CTkLabel(
                self.scroll,
                text="No accounts matching the selected filter criteria.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_DIM,
            ).pack(pady=40)
            return

        for u in filtered:
            row = ctk.CTkFrame(self.scroll, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=6)
            row.grid_columnconfigure(0, weight=3)
            row.grid_columnconfigure(1, weight=3)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=2)
            row.grid_columnconfigure(5, weight=2)

            # Name
            ctk.CTkLabel(row, text=u["full_name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=0, sticky="w")
            # Email
            ctk.CTkLabel(row, text=u["email"], font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED, anchor="w").grid(row=0, column=1, sticky="w")

            # Role Badge
            r_str = u.get("role", "participant").upper()
            if r_str in ("PARTICIPANT", "STUDENT"):
                r_color = Theme.PRIMARY
                r_bg = Theme.PRIMARY_LIGHT
            elif r_str == "ORGANIZER":
                r_color = Theme.SECONDARY
                r_bg = Theme.SECONDARY_LIGHT
            else:
                r_color = Theme.PURPLE
                r_bg = Theme.PURPLE_LIGHT

            ctk.CTkLabel(
                row,
                text=f" {r_str} ",
                font=Theme.FONT_SMALL,
                text_color=r_color,
                fg_color=r_bg,
                corner_radius=4,
            ).grid(row=0, column=2, sticky="w")

            # Activity
            att_cnt = u.get("attempts_count", 0)
            quiz_cnt = u.get("quizzes_created", 0)
            if u.get("role") == "organizer":
                act_text = f"{quiz_cnt} quizzes created"
            else:
                act_text = f"{att_cnt} tests taken"
            ctk.CTkLabel(row, text=act_text, font=Theme.FONT_SMALL, text_color=Theme.TEXT_MAIN, anchor="w").grid(row=0, column=3, sticky="w")

            # Status
            is_act = u.get("is_active", True)
            s_text = "ACTIVE" if is_act else "SUSPENDED"
            s_color = Theme.SUCCESS if is_act else Theme.DANGER
            s_bg = Theme.SUCCESS_BG if is_act else Theme.DANGER_BG
            ctk.CTkLabel(
                row,
                text=f" {s_text} ",
                font=Theme.FONT_SMALL,
                text_color=s_color,
                fg_color=s_bg,
                corner_radius=4,
            ).grid(row=0, column=4, sticky="w")

            # Moderation Action Button
            action_btn_text = "Suspend" if is_act else "Reactivate"
            action_btn_color = Theme.DANGER if is_act else Theme.SUCCESS

            ctk.CTkButton(
                row,
                text=action_btn_text,
                font=Theme.FONT_SMALL,
                fg_color=action_btn_color,
                width=90,
                height=26,
                corner_radius=6,
                command=lambda user_id=u["id"], active=is_act, uname=u["full_name"]: self._toggle_status(user_id, active, uname),
            ).grid(row=0, column=5, sticky="w")

    def _toggle_status(self, user_id: int, current_active: bool, user_name: str):
        target_state = not current_active
        action_verb = "suspend" if current_active else "reactivate"

        if not messagebox.askyesno(
            f"Confirm {action_verb.title()}",
            f"Are you sure you want to {action_verb} {user_name}'s account?\nSuspended users cannot sign in or attempt quizzes.",
        ):
            return

        ok, res = api_client.update_user_status(user_id, target_state, reason=f"Admin {action_verb}")
        if ok:
            messagebox.showinfo("Status Updated", f"User {user_name} has been {action_verb}ed successfully.")
            self.load_users()
        else:
            messagebox.showerror("Action Denied", str(res))
