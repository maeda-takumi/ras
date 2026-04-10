"""ボタン押下時の処理（現時点ではモック）。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from ras_ui.logic.login_info_saver import (
    InvalidSessionIdException,
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_log(f"[{timestamp}] 保存済みログイン情報を使ってブラウザを起動します")

        saver = LoginInfoSaver()
        try:
            driver = saver.load_session_and_open(Path("data/login_session.json"))
            opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{opened_at}] ログイン済み画面を開きました: {driver.current_url}")
            messagebox.showinfo(
                "即時実行",
                "保存済みセッションでブラウザを起動しました。\nログイン状態を確認してください。",
            )
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
            error_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{error_at}] セッション読込エラー: {exc}")
            messagebox.showerror("エラー", f"保存済みログイン情報の読込に失敗しました。\n{exc}")
        except (NoSuchElementException, WebDriverException) as exc:
            error_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{error_at}] 即時実行エラー: {exc}")
            messagebox.showerror("エラー", f"即時実行に失敗しました。\n{exc}")

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
        except (NoSuchElementException, WebDriverException, InvalidSessionIdException) as exc:
            error_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_log(f"[{error_at}] ログイン情報保存エラー: {exc}")
            messagebox.showerror("エラー", f"ログイン情報の保存に失敗しました。\n{exc}")
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except InvalidSessionIdException:
                    pass

    def _show_implementing(self, action_name: str) -> None:
        message = f"{action_name}：実装中です"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_log(f"[{timestamp}] {message}")
        messagebox.showinfo("お知らせ", message)
