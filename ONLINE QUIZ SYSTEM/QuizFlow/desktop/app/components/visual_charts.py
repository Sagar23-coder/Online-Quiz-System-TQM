"""
Modern Canvas-based Visual Charts and Gauges for CustomTkinter.
Renders circular progress rings, vertical bar charts, and sparklines matching modern SaaS analytics.
"""
import math
import tkinter as tk
import customtkinter as ctk
from app.utils.theme import Theme


class CircularProgress(ctk.CTkFrame):
    """Circular radial ring gauge with center percentage text."""
    def __init__(
        self,
        master,
        percentage: float = 75.0,
        size: int = 100,
        ring_width: int = 10,
        ring_color: str = Theme.PURPLE,
        track_color: str = "#E2E8F0",
        label: str = "",
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.size = size
        self.ring_width = ring_width
        self.ring_color = ring_color
        self.track_color = track_color
        self.percentage = max(0.0, min(100.0, percentage))
        self.label_text = label

        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=Theme.BG_CARD,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(padx=2, pady=2)
        self.draw()

    def set_percentage(self, pct: float, center_text: str = None):
        self.percentage = max(0.0, min(100.0, pct))
        if center_text is not None:
            self.label_text = center_text
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        s = self.size
        w = self.ring_width
        pad = w / 2 + 2

        # Draw background track circle
        self.canvas.create_oval(
            pad, pad, s - pad, s - pad,
            outline=self.track_color,
            width=w,
        )

        # Draw progress arc (starts at 90 deg = top, goes clockwise)
        extent = -(self.percentage / 100.0) * 360.0
        if abs(extent) > 0.5:
            self.canvas.create_arc(
                pad, pad, s - pad, s - pad,
                start=90,
                extent=extent,
                outline=self.ring_color,
                width=w,
                style="arc",
            )

        # Center Text
        txt = self.label_text if self.label_text else f"{int(self.percentage)}%"
        self.canvas.create_text(
            s / 2, s / 2,
            text=txt,
            fill=Theme.TEXT_MAIN,
            font=("Segoe UI", int(s * 0.18), "bold"),
        )


class MiniSparkline(ctk.CTkFrame):
    """Cute mini vertical bar sparkline (matching Tabor Study card)."""
    def __init__(
        self,
        master,
        values=(40, 65, 30, 85, 50, 70, 95, 45, 80, 60),
        bar_color=Theme.PURPLE,
        width=140,
        height=36,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=Theme.BG_CARD,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()
        self.values = values
        self.bar_color = bar_color
        self.w = width
        self.h = height
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        n = len(self.values)
        if n == 0:
            return
        bar_w = (self.w - (n * 3)) / n
        max_val = max(self.values) if max(self.values) > 0 else 100

        for i, val in enumerate(self.values):
            x0 = i * (bar_w + 3) + 2
            x1 = x0 + bar_w
            bar_h = (val / max_val) * (self.h - 6)
            y0 = self.h - bar_h - 2
            y1 = self.h - 2

            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill=self.bar_color,
                outline="",
            )


class PerformanceBarChart(ctk.CTkFrame):
    """Vertical dual-colored performance bar chart (matching Cognify design)."""
    def __init__(
        self,
        master,
        items=None,
        width=520,
        height=190,
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.BG_CARD, corner_radius=12, **kwargs)
        self.w = width
        self.h = height
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=Theme.BG_CARD,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=10)

        # Default sample data if none provided
        self.items = items or [
            {"label": "Quiz 1", "total": 100, "score": 85},
            {"label": "Quiz 2", "total": 100, "score": 68},
            {"label": "Quiz 3", "total": 100, "score": 92},
            {"label": "Quiz 4", "total": 100, "score": 74},
            {"label": "Quiz 5", "total": 100, "score": 88},
            {"label": "Quiz 6", "total": 100, "score": 60},
        ]
        self.draw()

    def set_data(self, items):
        self.items = items
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        if not self.items:
            self.canvas.create_text(
                self.w / 2,
                self.h / 2,
                text="Complete your first quiz to view performance analytics",
                fill=Theme.TEXT_DIM,
                font=Theme.FONT_BODY,
            )
            return

        w = self.w
        h = self.h
        bottom_pad = 32
        top_pad = 20
        chart_h = h - bottom_pad - top_pad

        # Draw subtle grid horizontal lines
        for step in [0.25, 0.5, 0.75, 1.0]:
            y = h - bottom_pad - (chart_h * step)
            self.canvas.create_line(30, y, w - 20, y, fill="#F1F5F9", width=1)

        n = len(self.items)
        col_w = (w - 60) / max(n, 1)
        bar_w = min(col_w * 0.5, 34)

        for i, item in enumerate(self.items):
            cx = 40 + (i * col_w) + (col_w / 2)
            x0 = cx - (bar_w / 2)
            x1 = cx + (bar_w / 2)

            total = item.get("total", 100) or 100
            score = item.get("score", 0)

            # Total marks bar (Blue)
            tot_h = min(chart_h, (total / 100.0) * chart_h)
            tot_y0 = h - bottom_pad - tot_h
            tot_y1 = h - bottom_pad

            # Soft background pillar
            self.canvas.create_rectangle(
                x0, h - bottom_pad - chart_h, x1, tot_y1,
                fill="#F8FAFC", outline="",
            )

            # Blue total bar
            self.canvas.create_rectangle(
                x0, tot_y0, x1, tot_y1,
                fill=Theme.SECONDARY, outline="",
            )

            # Score bar (Green) inside or overlapping
            score_pct = min(1.0, score / max(total, 1))
            score_h = score_pct * tot_h
            score_y0 = h - bottom_pad - score_h

            self.canvas.create_rectangle(
                x0, score_y0, x1, tot_y1,
                fill=Theme.SUCCESS, outline="",
            )

            # Label below
            lbl = item.get("label", f"Q{i+1}")
            if len(lbl) > 8:
                lbl = lbl[:7] + ".."
            self.canvas.create_text(
                cx, h - bottom_pad + 16,
                text=lbl,
                fill=Theme.TEXT_MUTED,
                font=("Segoe UI", 9),
            )


class TrendWaveChart(ctk.CTkFrame):
    """Smooth wave trend area chart (matching Tabor Study Exam Taken Times)."""
    def __init__(
        self,
        master,
        points=(15, 12, 18, 22, 17, 32, 28, 20, 24, 19, 23, 27),
        labels=("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
        width=480,
        height=180,
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.BG_CARD, corner_radius=12, **kwargs)
        self.w = width
        self.h = height
        self.points = points
        self.labels = labels
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=Theme.BG_CARD,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=10)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        w = self.w
        h = self.h
        bottom_pad = 28
        top_pad = 20
        plot_h = h - bottom_pad - top_pad

        # Background grid
        for step in [0.25, 0.5, 0.75, 1.0]:
            y = h - bottom_pad - (plot_h * step)
            self.canvas.create_line(30, y, w - 20, y, fill="#F8FAFC", width=1)

        n = len(self.points)
        if n < 2:
            return
        step_x = (w - 60) / (n - 1)
        max_val = max(self.points) if max(self.points) > 0 else 40

        coords = []
        for i, val in enumerate(self.points):
            x = 30 + (i * step_x)
            y = h - bottom_pad - ((val / max_val) * plot_h)
            coords.extend([x, y])

        # Smooth spline curve
        self.canvas.create_line(
            *coords,
            smooth=True,
            fill=Theme.PURPLE,
            width=3,
        )

        # Plot circles on vertices
        for i, val in enumerate(self.points):
            x = 30 + (i * step_x)
            y = h - bottom_pad - ((val / max_val) * plot_h)
            self.canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill="#FFFFFF", outline=Theme.PURPLE, width=2,
            )
            # Label below
            if i < len(self.labels):
                self.canvas.create_text(
                    x, h - bottom_pad + 14,
                    text=self.labels[i],
                    fill=Theme.TEXT_DIM,
                    font=("Segoe UI", 8),
                )


class QuizActivityLineChart(ctk.CTkFrame):
    """
    Dual-series line chart for Admin Dashboard (Quizzes vs Attempts over Mon-Sun / Months).
    Matches the exact layout in the reference image.
    """
    def __init__(
        self,
        master,
        quizzes_points=None,
        attempts_points=None,
        labels=None,
        width=520,
        height=190,
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR, **kwargs)
        self.w = width
        self.h = height
        self.quizzes_points = quizzes_points or [2, 3, 1, 4, 3, 5, 2]
        self.attempts_points = attempts_points or [12, 18, 15, 26, 22, 35, 28]
        self.labels = labels or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg="#FFFFFF",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=10)
        self.canvas.bind("<Configure>", self._on_resize)
        self.draw()

    def _on_resize(self, event):
        if event.width > 20 and event.height > 20:
            self.draw()

    def set_data(self, quizzes_points, attempts_points, labels=None):
        self.quizzes_points = quizzes_points
        self.attempts_points = attempts_points
        if labels:
            self.labels = labels
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 10:
            w = self.w
        if h <= 10:
            h = self.h

        bottom_pad = 32
        top_pad = 26
        left_pad = 42
        right_pad = 24
        plot_w = max(10, w - left_pad - right_pad)
        plot_h = max(10, h - bottom_pad - top_pad)

        all_pts = list(self.quizzes_points) + list(self.attempts_points)
        max_val = max(max(all_pts) if all_pts else 40, 10)
        max_val = int(math.ceil(max_val / 10.0) * 10)

        # Draw grid lines & y-axis labels
        for i in range(5):
            val = int((max_val / 4) * i)
            y = h - bottom_pad - ((val / max_val) * plot_h)
            self.canvas.create_line(left_pad, y, w - right_pad, y, fill="#E2E8F0", width=1)
            self.canvas.create_text(
                left_pad - 10, y,
                text=str(val),
                fill="#64748B",
                font=("Segoe UI", 9),
                anchor="e",
            )

        n = len(self.labels)
        if n < 2:
            return
        step_x = plot_w / (n - 1)

        # 1. Series: Attempts (Purple #8B5CF6)
        att_coords = []
        for i, val in enumerate(self.attempts_points[:n]):
            x = left_pad + (i * step_x)
            y = h - bottom_pad - ((val / max_val) * plot_h)
            att_coords.extend([x, y])

        if len(att_coords) >= 4:
            self.canvas.create_line(*att_coords, fill="#8B5CF6", width=3, smooth=True)
            for i, val in enumerate(self.attempts_points[:n]):
                x = left_pad + (i * step_x)
                y = h - bottom_pad - ((val / max_val) * plot_h)
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#FFFFFF", outline="#8B5CF6", width=2.5)

        # 2. Series: Quizzes Created (Blue #3B82F6)
        q_coords = []
        for i, val in enumerate(self.quizzes_points[:n]):
            x = left_pad + (i * step_x)
            y = h - bottom_pad - ((val / max_val) * plot_h)
            q_coords.extend([x, y])

        if len(q_coords) >= 4:
            self.canvas.create_line(*q_coords, fill="#3B82F6", width=3, smooth=True)
            for i, val in enumerate(self.quizzes_points[:n]):
                x = left_pad + (i * step_x)
                y = h - bottom_pad - ((val / max_val) * plot_h)
                self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#FFFFFF", outline="#3B82F6", width=2.5)

        # X-axis date labels
        for i, lbl in enumerate(self.labels):
            x = left_pad + (i * step_x)
            self.canvas.create_text(
                x, h - bottom_pad + 16,
                text=lbl,
                fill="#475569",
                font=("Segoe UI", 9, "bold"),
            )


class PerformanceDoubleBarChart(ctk.CTkFrame):
    """
    Double bar chart for Teacher Dashboard (Average Score vs Pass Rate across months).
    Matches the exact layout in the reference image.
    """
    def __init__(
        self,
        master,
        months=None,
        avg_scores=None,
        pass_rates=None,
        width=480,
        height=190,
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR, **kwargs)
        self.w = width
        self.h = height
        self.months = months or ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        self.avg_scores = avg_scores or [65, 72, 68, 75, 70, 78, 82]
        self.pass_rates = pass_rates or [70, 78, 72, 80, 74, 85, 88]

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg="#FFFFFF",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=10)
        self.canvas.bind("<Configure>", self._on_resize)
        self.draw()

    def _on_resize(self, event):
        if event.width > 20 and event.height > 20:
            self.draw()

    def set_data(self, months, avg_scores, pass_rates):
        self.months = months
        self.avg_scores = avg_scores
        self.pass_rates = pass_rates
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 10:
            w = self.w
        if h <= 10:
            h = self.h

        bottom_pad = 32
        top_pad = 26
        left_pad = 42
        right_pad = 24
        plot_w = max(10, w - left_pad - right_pad)
        plot_h = max(10, h - bottom_pad - top_pad)

        # Grid lines (0, 25, 50, 75, 100)
        for pct in [0, 25, 50, 75, 100]:
            y = h - bottom_pad - ((pct / 100.0) * plot_h)
            self.canvas.create_line(left_pad, y, w - right_pad, y, fill="#E2E8F0", width=1)
            self.canvas.create_text(
                left_pad - 10, y,
                text=f"{pct}%",
                fill="#64748B",
                font=("Segoe UI", 8),
                anchor="e",
            )

        n = len(self.months)
        if n == 0:
            return
        col_w = plot_w / n
        single_bar_w = min(col_w * 0.34, 18)

        for i, m in enumerate(self.months):
            cx = left_pad + (i * col_w) + (col_w / 2)

            # Bar 1: Avg Score (Cyan/Blue #06B6D4)
            s_val = self.avg_scores[i] if i < len(self.avg_scores) else 0
            s_h = (s_val / 100.0) * plot_h
            bx1_0 = cx - single_bar_w - 2
            bx1_1 = cx - 2
            by1_0 = h - bottom_pad - s_h
            by1_1 = h - bottom_pad
            self.canvas.create_rectangle(bx1_0, by1_0, bx1_1, by1_1, fill="#06B6D4", outline="")
            if s_h > 15:
                self.canvas.create_text((bx1_0 + bx1_1) / 2, by1_0 - 7, text=f"{int(s_val)}", font=("Segoe UI", 7, "bold"), fill="#0891B2")

            # Bar 2: Pass Rate (Emerald/Green #10B981)
            p_val = self.pass_rates[i] if i < len(self.pass_rates) else 0
            p_h = (p_val / 100.0) * plot_h
            bx2_0 = cx + 2
            bx2_1 = cx + single_bar_w + 2
            by2_0 = h - bottom_pad - p_h
            by2_1 = h - bottom_pad
            self.canvas.create_rectangle(bx2_0, by2_0, bx2_1, by2_1, fill="#10B981", outline="")
            if p_h > 15:
                self.canvas.create_text((bx2_0 + bx2_1) / 2, by2_0 - 7, text=f"{int(p_val)}", font=("Segoe UI", 7, "bold"), fill="#059669")

            # Month label
            self.canvas.create_text(
                cx, h - bottom_pad + 16,
                text=m,
                fill="#475569",
                font=("Segoe UI", 9, "bold"),
            )


class StudentProgressAreaChart(ctk.CTkFrame):
    """
    Student Progress trend chart with blue line and soft gradient/area fill.
    Matches the exact layout in the reference image.
    """
    def __init__(
        self,
        master,
        points=None,
        labels=None,
        width=480,
        height=190,
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER_COLOR, **kwargs)
        self.w = width
        self.h = height
        self.points = points or [55, 62, 70, 75, 74, 82]
        self.labels = labels or ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]

        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg="#FFFFFF",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=10)
        self.canvas.bind("<Configure>", self._on_resize)
        self.draw()

    def _on_resize(self, event):
        if event.width > 20 and event.height > 20:
            self.draw()

    def set_data(self, points, labels=None):
        self.points = points
        if labels:
            self.labels = labels
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 10:
            w = self.w
        if h <= 10:
            h = self.h

        bottom_pad = 32
        top_pad = 28
        left_pad = 42
        right_pad = 24
        plot_w = max(10, w - left_pad - right_pad)
        plot_h = max(10, h - bottom_pad - top_pad)

        # Grid lines (0, 25, 50, 75, 100)
        for pct in [0, 25, 50, 75, 100]:
            y = h - bottom_pad - ((pct / 100.0) * plot_h)
            self.canvas.create_line(left_pad, y, w - right_pad, y, fill="#E2E8F0", width=1)
            self.canvas.create_text(
                left_pad - 10, y,
                text=f"{pct}%",
                fill="#64748B",
                font=("Segoe UI", 8),
                anchor="e",
            )

        n = len(self.points)
        if n < 2:
            return
        step_x = plot_w / (n - 1)

        # Compute point coordinates
        pts_coords = []
        for i, val in enumerate(self.points):
            x = left_pad + (i * step_x)
            y = h - bottom_pad - ((val / 100.0) * plot_h)
            pts_coords.append((x, y))

        # Build closed polygon for area fill below curve
        poly_coords = [pts_coords[0][0], h - bottom_pad]
        for x, y in pts_coords:
            poly_coords.extend([x, y])
        poly_coords.extend([pts_coords[-1][0], h - bottom_pad])

        # Soft blue area fill
        self.canvas.create_polygon(*poly_coords, fill="#DBEAFE", outline="")

        # Line on top
        flat_coords = [c for pt in pts_coords for c in pt]
        self.canvas.create_line(*flat_coords, fill="#2563EB", width=3, smooth=True)

        # Plot circular dots on vertices and display score text above each dot
        for i, (x, y) in enumerate(pts_coords):
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="#FFFFFF", outline="#2563EB", width=2.5)
            val = self.points[i] if i < len(self.points) else 0
            self.canvas.create_text(x, y - 12, text=f"{int(val)}%", font=("Segoe UI", 8, "bold"), fill="#1E3A8A")

        # X-axis week labels
        for i, lbl in enumerate(self.labels[:n]):
            x = left_pad + (i * step_x)
            self.canvas.create_text(
                x, h - bottom_pad + 16,
                text=lbl,
                fill="#475569",
                font=("Segoe UI", 9, "bold"),
            )

