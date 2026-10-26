"""
Interactive KPI / Stat Card Component for CustomTkinter.
Matches the exact visual design of the reference image:
- Colored icon badge square
- Clean title label
- Large bold metric value
- Trend / Context subtitle (e.g. '↑ 12% from last month')
- Clickable drilldown action
"""
import customtkinter as ctk
from app.utils.theme import Theme


class StatCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: str = "📊",
        badge_color: str = Theme.COLOR_STUDENTS,
        trend_text: str = "",
        trend_color: str = Theme.SUCCESS,
        command=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER_COLOR,
            **kwargs
        )
        self.command = command

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        # Top row: Icon Badge + Title
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 6))

        # Icon badge square with rounded corners
        self.icon_badge = ctk.CTkLabel(
            top_row,
            text=f" {icon} ",
            font=("Segoe UI", 12, "bold"),
            fg_color=badge_color,
            text_color="#FFFFFF",
            corner_radius=8,
            width=32,
            height=32,
        )
        self.icon_badge.pack(side="left", padx=(0, 10))

        # Title Label
        self.title_label = ctk.CTkLabel(
            top_row,
            text=title,
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        # Stat Value
        self.value_label = ctk.CTkLabel(
            inner,
            text=value,
            font=("Segoe UI", 20, "bold"),
            text_color=Theme.TEXT_MAIN,
            anchor="w",
        )
        self.value_label.pack(fill="x", pady=(0, 4))

        # Trend / Context text
        self.trend_label = ctk.CTkLabel(
            inner,
            text=trend_text if trend_text else "Real-time system metric",
            font=("Segoe UI", 8, "bold" if trend_text.startswith("↑") or trend_text.startswith("+") else "normal"),
            text_color=trend_color if (trend_text.startswith("↑") or trend_text.startswith("+")) else Theme.TEXT_MUTED,
            anchor="w",
        )
        self.trend_label.pack(fill="x")

        # Hover & Click bindings for interactivity
        if command:
            self._bind_click(command)

    def set_value(self, val: str, trend: str = None):
        self.value_label.configure(text=val)
        if trend is not None:
            self.trend_label.configure(text=trend)

    def _bind_click(self, cmd):
        self.configure(cursor="hand2")
        for widget in (self, self.title_label, self.value_label, self.trend_label):
            widget.bind("<Button-1>", lambda e: cmd())
            widget.bind("<Enter>", lambda e: self.configure(fg_color="#F8FAFC", border_color=Theme.PRIMARY))
            widget.bind("<Leave>", lambda e: self.configure(fg_color=Theme.BG_CARD, border_color=Theme.BORDER_COLOR))
