"""
Modern Authentication Screen for Desktop App (Login and Teacher Registration).
Designed with SaaS aesthetic: elevated card, smooth pill toggles.
Students access quizzes via shared link — no login required.
"""
import customtkinter as ctk
from app.services.api_client import api_client
from app.utils.theme import Theme


class AuthView(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="#F8FAFC")
        self.on_login_success = on_login_success
        self.mode = "login"  # "login" or "register"

        self.pack(fill="both", expand=True)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        # Outer centering scroll container (ensures compatibility with any screen resolution & scaling)
        self.scroll_wrap = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_wrap.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll_wrap.grid_columnconfigure(0, weight=1)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        card_w = min(460, max(300, int(screen_w * 0.88)))
        pad_x = 32 if screen_w >= 1200 else (22 if screen_w >= 800 else 16)
        pad_y = 24 if screen_h >= 900 else (16 if screen_h >= 700 else 12)

        # Elevated Modern SaaS Card
        self.card = ctk.CTkFrame(
            self.scroll_wrap,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E2E8F0",
            width=card_w,
        )
        self.card.grid(row=0, column=0, pady=(12, 18))

        inner_card = ctk.CTkFrame(self.card, fg_color="transparent")
        inner_card.pack(fill="both", expand=True, padx=pad_x, pady=pad_y)

        # 1. Brand Logo Badge Row
        brand_row = ctk.CTkFrame(inner_card, fg_color="transparent")
        brand_row.pack(anchor="center", pady=(0, 6))

        logo_badge = ctk.CTkFrame(brand_row, fg_color="#EEF2FF", corner_radius=10)
        logo_badge.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            logo_badge,
            text=" ✦ ",
            font=("Segoe UI", 16, "bold"),
            text_color="#4F46E5",
        ).pack(padx=6, pady=4)

        ctk.CTkLabel(
            brand_row,
            text="QuizFlow",
            font=("Segoe UI", 26, "bold"),
            text_color="#0F172A",
        ).pack(side="left")

        ctk.CTkLabel(
            inner_card,
            text="Enterprise Assessment & Examination Suite",
            font=Theme.FONT_SMALL,
            text_color="#64748B",
        ).pack(anchor="center", pady=(0, 18))

        # 2. Modern Segmented Mode Toggle (Sign In / Create Teacher Account)
        self.mode_toggle = ctk.CTkSegmentedButton(
            inner_card,
            values=["Sign In", "Create Teacher Account"],
            command=self._on_mode_change,
            selected_color="#4F46E5",
            unselected_color="#F1F5F9",
            text_color="#0F172A",
            font=("Segoe UI", 13, "bold"),
            height=36,
            corner_radius=8,
        )
        self.mode_toggle.set("Sign In")
        self.mode_toggle.pack(fill="x", pady=(0, 16))

        # 3. Status / Error Message Banner
        self.status_label = ctk.CTkLabel(
            inner_card,
            text="",
            font=Theme.FONT_SMALL,
            text_color=Theme.DANGER,
            wraplength=380,
        )
        self.status_label.pack(fill="x", pady=(0, 8))

        # 4. Dynamic Form Fields Frame
        self.form_frame = ctk.CTkFrame(inner_card, fg_color="transparent")
        self.form_frame.pack(fill="x", pady=(0, 4))

        # Render initial mode
        self._render_form()

    def _on_mode_change(self, value):
        self.mode = "login" if value == "Sign In" else "register"
        self.status_label.configure(text="")
        self._render_form()

    def _render_form(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        if self.mode == "login":
            # Email Field
            ctk.CTkLabel(
                self.form_frame,
                text="Email Address",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(2, 3))

            self.email_entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="name@example.com",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                font=Theme.FONT_BODY,
                height=40,
                corner_radius=8,
            )
            self.email_entry.pack(fill="x", pady=(0, 12))

            # Password Field with Eye Toggle
            ctk.CTkLabel(
                self.form_frame,
                text="Password",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 3))

            pwd_box = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            pwd_box.pack(fill="x", pady=(0, 18))

            self.password_entry = ctk.CTkEntry(
                pwd_box,
                placeholder_text="Enter your password",
                show="*",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                font=Theme.FONT_BODY,
                height=40,
                corner_radius=8,
            )
            self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

            self.login_pwd_visible = False
            def _toggle_login_pwd():
                self.login_pwd_visible = not self.login_pwd_visible
                self.password_entry.configure(show="" if self.login_pwd_visible else "*")
                eye_btn.configure(text="🔒" if self.login_pwd_visible else "👁️")

            eye_btn = ctk.CTkButton(
                pwd_box,
                text="👁️",
                width=42,
                height=40,
                font=("Segoe UI", 14),
                fg_color="#F1F5F9",
                hover_color="#E2E8F0",
                text_color="#334155",
                border_width=1,
                border_color="#CBD5E1",
                corner_radius=8,
                command=_toggle_login_pwd,
            )
            eye_btn.pack(side="right")

            self.password_entry.bind("<Return>", lambda _: self._handle_login())
            self.email_entry.bind("<Return>", lambda _: self.password_entry.focus())

            # Submit Button
            self.submit_btn = ctk.CTkButton(
                self.form_frame,
                text="Sign In to QuizFlow →",
                font=("Segoe UI", 14, "bold"),
                fg_color="#4F46E5",
                hover_color="#4338CA",
                text_color="#FFFFFF",
                height=42,
                corner_radius=8,
                command=self._handle_login,
            )
            self.submit_btn.pack(fill="x", pady=(4, 16))

        else:
            # Registration Mode: Teacher Only
            info_banner = ctk.CTkFrame(self.form_frame, fg_color="#EEF2FF", corner_radius=8)
            info_banner.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                info_banner,
                text="✦ Creating an Organizer (Teacher) Account",
                font=("Segoe UI", 12, "bold"),
                text_color="#4F46E5",
            ).pack(anchor="w", padx=10, pady=(6, 0))
            ctk.CTkLabel(
                info_banner,
                text="Students access quizzes via a shared link — no login required.",
                font=("Segoe UI", 11),
                text_color="#64748B",
            ).pack(anchor="w", padx=10, pady=(2, 6))

            # Full Name
            ctk.CTkLabel(
                self.form_frame,
                text="Full Name",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 2))
            self.name_entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="e.g. Jane Doe",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                height=38,
                corner_radius=8,
            )
            self.name_entry.pack(fill="x", pady=(0, 8))

            # Email
            ctk.CTkLabel(
                self.form_frame,
                text="Email Address",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 2))
            self.reg_email_entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="name@example.com",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                height=38,
                corner_radius=8,
            )
            self.reg_email_entry.pack(fill="x", pady=(0, 8))

            # Password with Eye Toggle
            ctk.CTkLabel(
                self.form_frame,
                text="Password (min 6 characters)",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 2))

            reg_pwd_box = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            reg_pwd_box.pack(fill="x", pady=(0, 8))

            self.reg_password_entry = ctk.CTkEntry(
                reg_pwd_box,
                placeholder_text="Create secure password",
                show="*",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                height=38,
                corner_radius=8,
            )
            self.reg_password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

            self.reg_pwd_visible = False
            def _toggle_reg_pwd():
                self.reg_pwd_visible = not self.reg_pwd_visible
                self.reg_password_entry.configure(show="" if self.reg_pwd_visible else "*")
                reg_eye_btn.configure(text="🔒" if self.reg_pwd_visible else "👁️")

            reg_eye_btn = ctk.CTkButton(
                reg_pwd_box,
                text="👁️",
                width=40,
                height=38,
                font=("Segoe UI", 13),
                fg_color="#F1F5F9",
                hover_color="#E2E8F0",
                text_color="#334155",
                border_width=1,
                border_color="#CBD5E1",
                corner_radius=8,
                command=_toggle_reg_pwd,
            )
            reg_eye_btn.pack(side="right")

            # Confirm Password with Eye Toggle
            ctk.CTkLabel(
                self.form_frame,
                text="Confirm Password",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 2))

            conf_pwd_box = ctk.CTkFrame(self.form_frame, fg_color="transparent")
            conf_pwd_box.pack(fill="x", pady=(0, 14))

            self.confirm_password_entry = ctk.CTkEntry(
                conf_pwd_box,
                placeholder_text="Re-type password",
                show="*",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                height=38,
                corner_radius=8,
            )
            self.confirm_password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

            self.conf_pwd_visible = False
            def _toggle_conf_pwd():
                self.conf_pwd_visible = not self.conf_pwd_visible
                self.confirm_password_entry.configure(show="" if self.conf_pwd_visible else "*")
                conf_eye_btn.configure(text="🔒" if self.conf_pwd_visible else "👁️")

            conf_eye_btn = ctk.CTkButton(
                conf_pwd_box,
                text="👁️",
                width=40,
                height=38,
                font=("Segoe UI", 13),
                fg_color="#F1F5F9",
                hover_color="#E2E8F0",
                text_color="#334155",
                border_width=1,
                border_color="#CBD5E1",
                corner_radius=8,
                command=_toggle_conf_pwd,
            )
            conf_eye_btn.pack(side="right")

            # Submit Button
            self.submit_btn = ctk.CTkButton(
                self.form_frame,
                text="Create Teacher Account →",
                font=("Segoe UI", 14, "bold"),
                fg_color="#4F46E5",
                hover_color="#4338CA",
                text_color="#FFFFFF",
                height=42,
                corner_radius=8,
                command=self._handle_register,
            )
            self.submit_btn.pack(fill="x", pady=(4, 6))

    def _handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not email or not password:
            self.status_label.configure(text="Please enter both email and password.", text_color=Theme.DANGER)
            return

        self.submit_btn.configure(state="disabled", text="Authenticating...")
        ok, res = api_client.login(email, password)
        self.submit_btn.configure(state="normal", text="Sign In to QuizFlow →")

        if ok:
            self.status_label.configure(text="Login successful!", text_color=Theme.SUCCESS)
            self.on_login_success(res["user"])
        else:
            self.status_label.configure(text=str(res), text_color=Theme.DANGER)

    def _handle_register(self):
        name = self.name_entry.get().strip()
        email = self.reg_email_entry.get().strip()
        password = self.reg_password_entry.get().strip()
        confirm = self.confirm_password_entry.get().strip()
        # Registration is always for Teacher/Organizer role (students use shared links)
        role = "organizer"

        if not name or not email or not password:
            self.status_label.configure(text="Please complete all required fields.", text_color=Theme.DANGER)
            return

        if password != confirm:
            self.status_label.configure(text="Passwords do not match.", text_color=Theme.DANGER)
            return

        self.submit_btn.configure(state="disabled", text="Creating Account...")
        ok, res = api_client.register(email, name, password, confirm, role=role)
        self.submit_btn.configure(state="normal", text="Create Teacher Account →")

        if ok:
            # Auto login upon registration
            login_ok, login_res = api_client.login(email, password)
            if login_ok:
                self.on_login_success(login_res["user"])
            else:
                self.mode_toggle.set("Sign In")
                self._on_mode_change("Sign In")
                self.status_label.configure(text="Account created! Please sign in with your credentials.", text_color=Theme.SUCCESS)
        else:
            self.status_label.configure(text=str(res), text_color=Theme.DANGER)
