"""UIテーマ定義。"""

BG_COLOR = "#f2f3f5"
CARD_COLOR = "#ffffff"
SUBTLE_COLOR = "#eceef1"
TEXT_COLOR = "#1f2328"
MUTED_TEXT_COLOR = "#666f7a"
ACCENT_COLOR = "#7f1d1d"
ACCENT_HOVER = "#681515"
BORDER_COLOR = "#d7dbe2"

FONT_FAMILY = "Yu Gothic UI"


def button_style(primary: bool = False) -> dict[str, str]:
    if primary:
        return {
            "bg": ACCENT_COLOR,
            "activebackground": ACCENT_HOVER,
            "fg": "#ffffff",
            "activeforeground": "#ffffff",
            "bd": 0,
            "relief": "flat",
            "cursor": "hand2",
            "font": (FONT_FAMILY, 10, "bold"),
            "padx": 14,
            "pady": 10,
        }

    return {
        "bg": SUBTLE_COLOR,
        "activebackground": "#e2e5ea",
        "fg": TEXT_COLOR,
        "activeforeground": TEXT_COLOR,
        "bd": 0,
        "relief": "flat",
        "cursor": "hand2",
        "font": (FONT_FAMILY, 10, "bold"),
        "padx": 14,
        "pady": 10,
    }
