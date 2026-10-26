"""
QuizFlow Desktop Design System - Premium Light Modern SaaS Theme.
Inspired by modern education analytics platforms (Cognify & Tabor Study).
"""


class Theme:
    # Appearance Mode
    APPEARANCE_MODE = "Light"  # Clean, modern light SaaS design
    COLOR_THEME = "blue"

    # Backgrounds & Cards
    BG_MAIN = "#F8FAFC"         # Soft slate canvas background
    BG_DARK = "#F8FAFC"
    BG_CARD = "#FFFFFF"         # Crisp pure white cards
    BG_CARD_HOVER = "#F1F5F9"   # Very subtle card hover
    BG_SIDEBAR = "#0F172A"      # Dark Navy Sidebar (matching reference design)
    BG_HEADER = "#FFFFFF"       # Top white header bar
    BG_INPUT = "#F8FAFC"        # Light input background
    BORDER_COLOR = "#E2E8F0"    # Subtle border (Slate 200)
    BORDER_LIGHT = "#F1F5F9"

    # Sidebar Theme Tokens
    SIDEBAR_HOVER = "#1E293B"
    SIDEBAR_ACTIVE = "#4F46E5"   # Vibrant indigo active pill
    SIDEBAR_TEXT = "#94A3B8"     # Slate 400
    SIDEBAR_TEXT_ACTIVE = "#FFFFFF"

    # Role & KPI Color Palette (Matching Reference Image)
    COLOR_STUDENTS = "#3B82F6"  # Blue (Total Students)
    COLOR_TEACHERS = "#8B5CF6"  # Purple (Total Teachers)
    COLOR_QUIZZES = "#10B981"   # Emerald (Total Quizzes)
    COLOR_ATTEMPTS = "#F59E0B"  # Amber (Total Attempts)
    COLOR_AVERAGE = "#06B6D4"   # Cyan (Average Score)
    COLOR_PASSRATE = "#6366F1"  # Indigo (Pass Rate)

    # Primary & Secondary Accents
    PRIMARY = "#4F46E5"         # Modern Indigo
    PRIMARY_HOVER = "#4338CA"
    PRIMARY_LIGHT = "#EEF2FF"   # Soft indigo tint
    SECONDARY = "#3B82F6"       # Vivid Blue
    SECONDARY_HOVER = "#2563EB"
    SECONDARY_LIGHT = "#EFF6FF"
    PURPLE = "#8B5CF6"          # Violet accent
    PURPLE_LIGHT = "#F5F3FF"

    # Semantic Status
    SUCCESS = "#10B981"         # Emerald
    SUCCESS_LIGHT = "#ECFDF5"
    SUCCESS_BG = "#ECFDF5"
    DANGER = "#EF4444"          # Rose Red
    DANGER_HOVER = "#DC2626"
    DANGER_LIGHT = "#FEF2F2"
    DANGER_BG = "#FEF2F2"
    WARNING = "#F59E0B"         # Amber
    WARNING_LIGHT = "#FFFBEB"
    INFO = "#06B6D4"            # Cyan
    INFO_LIGHT = "#ECFEFF"

    # Typography / Neutrals
    TEXT_MAIN = "#0F172A"       # Slate 900 (Deep, high contrast)
    TEXT_MUTED = "#64748B"      # Slate 500 (Subtitles, labels)
    TEXT_DIM = "#94A3B8"        # Slate 400 (Dividers, hints)
    TEXT_WHITE = "#FFFFFF"

    # Fonts
    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = ("Segoe UI", 20, "bold")
    FONT_HEADING = ("Segoe UI", 15, "bold")
    FONT_SUBTITLE = ("Segoe UI", 13, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_BODY_BOLD = ("Segoe UI", 11, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")
    FONT_STAT = ("Segoe UI", 26, "bold")
    FONT_TIMER = ("Segoe UI", 20, "bold")
