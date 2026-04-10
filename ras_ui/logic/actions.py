"""ボタン押下時の処理（現時点ではモック）。"""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox


class ActionHandler:
    def __init__(self, add_log_callback):
        self.add_log = add_log_callback

    def on_polling_execute(self) -> None:
        self._show_implementing("ポーリング実行")

    def on_immediate_execute(self) -> None:
        self._show_implementing("即時実行")

    def on_save_login_info(self) -> None:
        self._show_implementing("ログイン情報保存実行")

    def _show_implementing(self, action_name: str) -> None:
        message = f"{action_name}：実装中です"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_log(f"[{timestamp}] {message}")
        messagebox.showinfo("お知らせ", message)
