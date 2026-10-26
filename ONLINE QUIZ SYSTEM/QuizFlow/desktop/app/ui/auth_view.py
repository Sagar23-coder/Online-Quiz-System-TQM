"""
Modern Authentication Screen for Desktop App (Login and Multi-Role Registration).
Designed with SaaS aesthetic: elevated card, smooth pill toggles, and role-based guidance.
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
        # Outer centering scroll container (ensures compatibility with any screen resolution)
        self.scroll_wrap = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_wrap.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self.scroll_wrap.grid_columnconfigure(0, weight=1)

        # Elevated Modern SaaS Card
        self.card = ctk.CTkFrame(
            self.scroll_wrap,
            fg_color="#FFFFFF",
            corner_radius=16,
            border_width=1,
            border_color="#E2E8F0",
            width=460,
        )
        self.card.grid(row=0, column=0, pady=20)

        inner_card = ctk.CTkFrame(self.card, fg_color="transparent")
        inner_card.pack(fill="both", expand=True, padx=36, pady=28)

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

        # 2. Modern Segmented Mode Toggle (Sign In / Create Account)
        self.mode_toggle = ctk.CTkSegmentedButton(
            inner_card,
            values=["Sign In", "Create Account"],
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

            # Password Field
            ctk.CTkLabel(
                self.form_frame,
                text="Password",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 3))

            self.password_entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Enter your password",
                show="*",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                font=Theme.FONT_BODY,
                height=40,
                corner_radius=8,
            )
            self.password_entry.pack(fill="x", pady=(0, 18))
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
            # Registration Mode: Role Selection
            ctk.CTkLabel(
                self.form_frame,
                text="Choose Account Role",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

            self.role_toggle = ctk.CTkSegmentedButton(
                self.form_frame,
                values=["Participant (Student)", "Organizer (Teacher)"],
                command=self._on_role_change,
                selected_color="#4F46E5",
                unselected_color="#F8FAFC",
                text_color="#0F172A",
                font=("Segoe UI", 12, "bold"),
                height=34,
                corner_radius=8,
            )
            self.role_toggle.set("Participant (Student)")
            self.role_toggle.pack(fill="x", pady=(0, 4))

            # Dynamic role guide banner
            self.role_hint = ctk.CTkLabel(
                self.form_frame,
                text="✓ Take assessments, enter private join codes, and view graded scorecards",
                font=("Segoe UI", 11),
                text_color="#64748B",
                anchor="w",
            )
            self.role_hint.pack(fill="x", pady=(0, 10))

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

            # Password
            ctk.CTkLabel(
                self.form_frame,
                text="Password (min 6 characters)",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 2))
            self.reg_password_entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Create secure password",
                show="*",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                height=38,
                corner_radius=8,
            )
            self.reg_password_entry.pack(fill="x", pady=(0, 8))

            # Confirm Password
            ctk.CTkLabel(
                self.form_frame,
                text="Confirm Password",
                font=("Segoe UI", 12, "bold"),
                text_color="#334155",
                anchor="w",
            ).pack(fill="x", pady=(0, 2))
            self.confirm_password_entry = ctk.CTkEntry(
                self.form_frame,
                placeholder_text="Re-type password",
                show="*",
                fg_color="#F8FAFC",
                border_color="#CBD5E1",
                height=38,
                corner_radius=8,
            )
            self.confirm_password_entry.pack(fill="x", pady=(0, 14))

            # Submit Button
            self.submit_btn = ctk.CTkButton(
                self.form_frame,
                text="Create Student Account →",
                font=("Segoe UI", 14, "bold"),
                fg_color="#4F46E5",
                hover_color="#4338CA",
                text_color="#FFFFFF",
                height=42,
                corner_radius=8,
                command=self._handle_register,
            )
            self.submit_btn.pack(fill="x", pady=(4, 6))

    def _on_role_change(self, value):
        is_teacher = "Organizer" in value
        if is_teacher:
            self.role_hint.configure(text="✓ Create curriculum tests, issue private join codes, and evaluate students")
            self.submit_btn.configure(text="Create Teacher Account →")
        else:
            self.role_hint.configure(text="✓ Take assessments, enter private join codes, and view graded scorecards")
            self.submit_btn.configure(text="Create Student Account →")

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
        is_teacher = "Organizer" in self.role_toggle.get()
        role = "organizer" if is_teacher else "participant"

        if not name or not email or not password:
            self.status_label.configure(text="Please complete all required fields.", text_color=Theme.DANGER)
            return

        if password != confirm:
            self.status_label.configure(text="Passwords do not match.", text_color=Theme.DANGER)
            return

        self.submit_btn.configure(state="disabled", text="Creating Account...")
        ok, res = api_client.register(email, name, password, confirm, role=role)
        role_title = "Teacher" if is_teacher else "Student"
        self.submit_btn.configure(state="normal", text=f"Create {role_title} Account →")

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
