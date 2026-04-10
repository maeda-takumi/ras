"""ボタン押下時の処理（現時点ではモック）。"""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox

from ras_ui.logic.login_info_saver import (
    LoginInfoSaver,
    NoSuchElementException,
    WebDriverException,
)

class ActionHandler:
    def __init__(self, add_log_callback):
        self.add_log = add_log_callback

    def on_polling_execute(self) -> None:
        self._show_implementing("ポーリング実行")

    def on_immediate_execute(self) -> None:
        self._show_implementing("即時実行")

    def on_save_login_info(self) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_log(f"[{timestamp}] ログイン画面を開き、ID/PW入力を開始します")

        saver = LoginInfoSaver()
        driver = None
        try:
            driver = saver.open_login_page_and_fill()
            self.add_log(f"[{timestamp}] ID/PWの自動入力が完了しました")

            messagebox.showinfo(
                "手動ログイン待機",
                "手動ログイン完了後、OKボタンを押してください",
            )

            saved_path = saver.save_session(driver)
            done_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{done_at}] ログイン情報を保存しました: {saved_path}")
            messagebox.showinfo("完了", f"ログイン情報を保存しました\n{saved_path}")
        except (NoSuchElementException, WebDriverException) as exc:
            error_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{error_at}] ログイン情報保存エラー: {exc}")
            messagebox.showerror("エラー", f"ログイン情報の保存に失敗しました。\n{exc}")
        finally:
            if driver is not None:
                driver.quit()

    def _show_implementing(self, action_name: str) -> None:
        message = f"{action_name}：実装中です"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_log(f"[{timestamp}] {message}")
        messagebox.showinfo("お知らせ", message)
