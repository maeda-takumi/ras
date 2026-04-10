"""Seleniumを使ったログイン情報保存処理。"""

from __future__ import annotations

import json
import sqlite3
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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
        parsed_rows = self._collect_friend_rows_from_all_pages(driver)

        db_path = self.setting.friend_table_db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        scraped_at = datetime.now().isoformat()

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS line_user_table (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scraped_at TEXT NOT NULL,
                    detail_url TEXT UNIQUE,
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
            self._ensure_line_user_table_schema(conn)
            conn.executemany(
                """
                INSERT INTO line_user_table (
                    scraped_at,
                    detail_url,
                    row_no,
                    friend_added_at,
                    latest_message_at,
                    line_registered_name,
                    system_display_name,
                    email_address,
                    step_delivery_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(detail_url) DO UPDATE SET
                    scraped_at = excluded.scraped_at,
                    row_no = excluded.row_no,
                    friend_added_at = excluded.friend_added_at,
                    latest_message_at = excluded.latest_message_at,
                    line_registered_name = excluded.line_registered_name,
                    system_display_name = excluded.system_display_name,
                    email_address = excluded.email_address,
                    step_delivery_status = excluded.step_delivery_status
                """,
                [
                    (
                        scraped_at,
                        row["detail_url"],
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
    
    def _collect_friend_rows_from_all_pages(self, driver: webdriver.Chrome) -> list[dict[str, str]]:
        visited_page_urls: set[str] = set()
        unique_rows_by_url: "OrderedDict[str, dict[str, str]]" = OrderedDict()
        fallback_rows: list[dict[str, str]] = []

        while True:
            current_url = driver.current_url
            if current_url in visited_page_urls:
                break
            visited_page_urls.add(current_url)

            for row in self._parse_visible_rows(driver):
                detail_url = row["detail_url"]
                if detail_url:
                    unique_rows_by_url[detail_url] = row
                else:
                    fallback_rows.append(row)

            next_page_url = self._find_unvisited_page_url(driver, visited_page_urls)
            if not next_page_url:
                break
            driver.get(next_page_url)

        return [*unique_rows_by_url.values(), *fallback_rows]

    def _parse_visible_rows(self, driver: webdriver.Chrome) -> list[dict[str, str]]:
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
                    "detail_url": self._extract_detail_url(row, driver.current_url),
                    "row_no": self._normalize_cell_text(cells[0].text),
                    "friend_added_at": self._normalize_cell_text(cells[1].text),
                    "latest_message_at": self._normalize_cell_text(cells[2].text),
                    "line_registered_name": self._normalize_cell_text(cells[3].text),
                    "system_display_name": self._normalize_cell_text(cells[4].text),
                    "email_address": self._normalize_cell_text(cells[5].text),
                    "step_delivery_status": self._normalize_cell_text(cells[6].text),
                }
            )
        return parsed_rows

    @staticmethod
    def _extract_detail_url(row, current_url: str) -> str:
        anchors = row.find_elements(By.CSS_SELECTOR, "a[href]")
        for anchor in anchors:
            href = (anchor.get_attribute("href") or "").strip()
            if "/basic/friendlist/my_page/" in href:
                return urljoin(current_url, href)
        return "-"

    @staticmethod
    def _find_unvisited_page_url(driver: webdriver.Chrome, visited_page_urls: set[str]) -> str | None:
        page_anchors = driver.find_elements(By.CSS_SELECTOR, "ul.pagenavi li a[href]")
        for anchor in page_anchors:
            href = (anchor.get_attribute("href") or "").strip()
            if not href:
                continue
            absolute_href = urljoin(driver.current_url, href)
            if absolute_href not in visited_page_urls:
                return absolute_href
        return None

    @staticmethod
    def _ensure_line_user_table_schema(conn: sqlite3.Connection) -> None:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(line_user_table)").fetchall()
        }
        if "detail_url" not in columns:
            conn.execute("ALTER TABLE line_user_table ADD COLUMN detail_url TEXT")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_line_user_table_detail_url ON line_user_table(detail_url)"
        )
    
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
