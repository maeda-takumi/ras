"""ポーリング実行画面UI。"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext

from ras_ui.logic.actions import ActionHandler
from ras_ui.style import theme


class PollingWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("RAS | LMessageスクレイピング")
        self.root.geometry("860x620")
        self.root.configure(bg=theme.BG_COLOR)

        self.datetime_var = tk.StringVar(value="2026-04-10 09:00")

        self._build_layout()
        self.actions = ActionHandler(self.append_log)
        self._bind_actions()
        self.append_log("[INFO] UI初期化完了")
        self.append_log("[INFO] 各機能の処理は実装中です")

    def _build_layout(self) -> None:
        container = tk.Frame(self.root, bg=theme.BG_COLOR)
        container.pack(fill="both", expand=True, padx=26, pady=24)

        self._build_header(container)
        self._build_control_card(container)
        self._build_log_card(container)

    def _build_header(self, parent: tk.Widget) -> None:
        header = tk.Frame(parent, bg=theme.BG_COLOR)
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="RAS / Polling Console",
            bg=theme.BG_COLOR,
            fg=theme.ACCENT_COLOR,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="LMessage スクレイピング実行",
            bg=theme.BG_COLOR,
            fg=theme.TEXT_COLOR,
            font=(theme.FONT_FAMILY, 20, "bold"),
        ).pack(anchor="w", pady=(4, 2))

        tk.Label(
            header,
            text="ポーリング実行と手動実行、ログイン情報保存を行う管理画面（UIモック）",
            bg=theme.BG_COLOR,
            fg=theme.MUTED_TEXT_COLOR,
            font=(theme.FONT_FAMILY, 10),
        ).pack(anchor="w")

    def _build_control_card(self, parent: tk.Widget) -> None:
        card = tk.Frame(parent, bg=theme.CARD_COLOR, highlightbackground=theme.BORDER_COLOR, highlightthickness=1)
        card.pack(fill="x", pady=(0, 14))

        content = tk.Frame(card, bg=theme.CARD_COLOR)
        content.pack(fill="x", padx=18, pady=16)

        tk.Label(
            content,
            text="ポーリング実行日時",
            bg=theme.CARD_COLOR,
            fg=theme.TEXT_COLOR,
            font=(theme.FONT_FAMILY, 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        entry = tk.Entry(
            content,
            textvariable=self.datetime_var,
            bg=theme.SUBTLE_COLOR,
            fg=theme.TEXT_COLOR,
            insertbackground=theme.TEXT_COLOR,
            relief="flat",
            font=(theme.FONT_FAMILY, 11),
        )
        entry.pack(fill="x", ipady=9)

        button_row = tk.Frame(content, bg=theme.CARD_COLOR)
        button_row.pack(fill="x", pady=(14, 0))

        self.polling_button = tk.Button(button_row, text="ポーリング実行", **theme.button_style(primary=True))
        self.polling_button.pack(side="left", padx=(0, 8))

        self.immediate_button = tk.Button(button_row, text="即時実行", **theme.button_style())
        self.immediate_button.pack(side="left", padx=8)

        self.save_login_button = tk.Button(button_row, text="ログイン情報保存実行", **theme.button_style())
        self.save_login_button.pack(side="left", padx=8)

    def _build_log_card(self, parent: tk.Widget) -> None:
        card = tk.Frame(parent, bg=theme.CARD_COLOR, highlightbackground=theme.BORDER_COLOR, highlightthickness=1)
        card.pack(fill="both", expand=True)

        content = tk.Frame(card, bg=theme.CARD_COLOR)
        content.pack(fill="both", expand=True, padx=18, pady=16)

        title_row = tk.Frame(content, bg=theme.CARD_COLOR)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="ログ",
            bg=theme.CARD_COLOR,
            fg=theme.TEXT_COLOR,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(side="left")

        tk.Label(
            title_row,
            text="read only",
            bg=theme.SUBTLE_COLOR,
            fg=theme.MUTED_TEXT_COLOR,
            font=(theme.FONT_FAMILY, 8),
            padx=8,
            pady=3,
        ).pack(side="right")

        self.log_area = scrolledtext.ScrolledText(
            content,
            bg="#f8f9fb",
            fg="#252934",
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
            wrap="word",
        )
        self.log_area.pack(fill="both", expand=True, pady=(10, 0))
        self.log_area.configure(state="disabled")

    def _bind_actions(self) -> None:
        self.polling_button.configure(command=self.actions.on_polling_execute)
        self.immediate_button.configure(command=self.actions.on_immediate_execute)
        self.save_login_button.configure(command=self.actions.on_save_login_info)

    def append_log(self, message: str) -> None:
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()
