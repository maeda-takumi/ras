"""Seleniumを使ったログイン情報保存処理。"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By


@dataclass(frozen=True)
class LoginSetting:
    login_url: str = "https://step.lme.jp/"
    friend_list_url: str = "https://step.lme.jp/basic/friendlist"
    login_id: str = "miomama0605@gmail.com"
    login_password: str = "20250606@Mio"
    output_path: Path = Path("data/login_session.json")
    friend_table_db_path: Path = Path("data/friend_list.db")


class LoginInfoSaver:
    def __init__(self, setting: LoginSetting | None = None) -> None:
        self.setting = setting or LoginSetting()

    def open_login_page_and_fill(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-popup-blocking")

        driver = webdriver.Chrome(options=options)
        driver.get(self.setting.login_url)
        driver.maximize_window()

        id_input = self._find_first(
            driver,
            [
                (By.ID, "email_login"),
                (By.NAME, "email_login"),
                (By.NAME, "login_id"),
                (By.NAME, "email"),
                (By.NAME, "mail_address"),
                (By.ID, "login_id"),
                (By.ID, "email"),
                (By.CSS_SELECTOR, "input.input100#email_login"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name*='mail']"),
            ],
        )
        pw_input = self._find_first(
            driver,
            [
                (By.ID, "password_login"),
                (By.NAME, "password_login"),
                (By.NAME, "password"),
                (By.NAME, "login_password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input.input100#password_login"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ],
        )

        id_input.clear()
        id_input.send_keys(self.setting.login_id)
        pw_input.clear()
        pw_input.send_keys(self.setting.login_password)

        return driver

    def save_session(self, driver: webdriver.Chrome) -> Path:
        try:
            current_url = driver.current_url
        except InvalidSessionIdException as exc:
            raise WebDriverException(
                "ブラウザ接続が切断されました。ログイン完了後にブラウザを閉じず、同じウィンドウでOKを押してください。"
            ) from exc
        payload: dict[str, Any] = {
            "saved_at": datetime.now().isoformat(),
            "target_url": current_url,
            "cookies": driver.get_cookies(),
            "local_storage": driver.execute_script(
                """
                const data = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    data[key] = localStorage.getItem(key);
                }
                return data;
                """
            ),
            "session_storage": driver.execute_script(
                """
                const data = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    data[key] = sessionStorage.getItem(key);
                }
                return data;
                """
            ),
        }

        self.setting.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.setting.output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.setting.output_path

    def load_session_and_open(self, session_path: Path | None = None) -> webdriver.Chrome:
        target_path = session_path or self.setting.output_path
        session_data = self._read_session_file(target_path)

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-popup-blocking")

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        login_origin = self.setting.login_url
        driver.get(login_origin)

        for cookie in session_data.get("cookies", []):
            normalized_cookie = self._normalize_cookie(cookie)
            if normalized_cookie:
                try:
                    driver.add_cookie(normalized_cookie)
                except WebDriverException:
                    continue

        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        for key, value in session_data.get("local_storage", {}).items():
            driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)
        for key, value in session_data.get("session_storage", {}).items():
            driver.execute_script("window.sessionStorage.setItem(arguments[0], arguments[1]);", key, value)

        driver.get(self.setting.friend_list_url)
        return driver

    def save_friend_table_to_db(self, driver: webdriver.Chrome) -> Path:
        rows = driver.find_elements(By.CSS_SELECTOR, "#tableLineUser tbody tr")
        parsed_rows: list[dict[str, str]] = []

        for row in rows:
            if "display: none" in (row.get_attribute("style") or "").lower():
                continue

            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 7:
                continue

            parsed_rows.append(
                {
                    "row_no": self._normalize_cell_text(cells[0].text),
                    "friend_added_at": self._normalize_cell_text(cells[1].text),
                    "latest_message_at": self._normalize_cell_text(cells[2].text),
                    "line_registered_name": self._normalize_cell_text(cells[3].text),
                    "system_display_name": self._normalize_cell_text(cells[4].text),
                    "email_address": self._normalize_cell_text(cells[5].text),
                    "step_delivery_status": self._normalize_cell_text(cells[6].text),
                }
            )

        db_path = self.setting.friend_table_db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        scraped_at = datetime.now().isoformat()

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS line_user_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scraped_at TEXT NOT NULL,
                    row_no TEXT,
                    friend_added_at TEXT,
                    latest_message_at TEXT,
                    line_registered_name TEXT,
                    system_display_name TEXT,
                    email_address TEXT,
                    step_delivery_status TEXT
                )
                """
            )
            conn.execute("DELETE FROM line_user_table")
            conn.executemany(
                """
                INSERT INTO line_user_table (
                    scraped_at,
                    row_no,
                    friend_added_at,
                    latest_message_at,
                    line_registered_name,
                    system_display_name,
                    email_address,
                    step_delivery_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        scraped_at,
                        row["row_no"],
                        row["friend_added_at"],
                        row["latest_message_at"],
                        row["line_registered_name"],
                        row["system_display_name"],
                        row["email_address"],
                        row["step_delivery_status"],
                    )
                    for row in parsed_rows
                ],
            )
            conn.commit()

        return db_path
    
    @staticmethod
    def _read_session_file(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"セッションファイルが見つかりません: {path}")
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        if not isinstance(data, dict):
            raise ValueError("セッションファイルの形式が不正です")
        return data

    @staticmethod
    def _normalize_cookie(cookie: dict[str, Any]) -> dict[str, Any] | None:
        name = cookie.get("name")
        value = cookie.get("value")
        if not name or value is None:
            return None

        normalized: dict[str, Any] = {"name": name, "value": value}
        for key in ("domain", "path", "secure", "httpOnly", "sameSite", "expiry"):
            if key in cookie and cookie[key] is not None:
                normalized[key] = cookie[key]
        return normalized
    
    @staticmethod
    def _normalize_cell_text(value: str) -> str:
        compact = " ".join(value.split())
        return compact if compact else "-"
    
    @staticmethod
    def _find_first(
        driver: webdriver.Chrome,
        selectors: list[tuple[str, str]],
    ):
        for by, value in selectors:
            elements = driver.find_elements(by, value)
            if elements:
                return elements[0]
        raise NoSuchElementException(f"対象要素が見つかりません: {selectors}")


__all__ = [
    "LoginInfoSaver",
    "LoginSetting",
    "InvalidSessionIdException",
    "NoSuchElementException",
    "WebDriverException",
]
