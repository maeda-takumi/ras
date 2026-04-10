"""Seleniumを使ったログイン情報保存処理。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By


@dataclass(frozen=True)
class LoginSetting:
    login_url: str = "https://step.lme.jp/"
    login_id: str = "miomama0605@gmail.com"
    login_password: str = "20250606@Mio"
    output_path: Path = Path("data/login_session.json")


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
        payload: dict[str, Any] = {
            "saved_at": datetime.now().isoformat(),
            "target_url": driver.current_url,
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

        target_url = session_data.get("target_url") or self.setting.login_url
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

        driver.get(target_url)
        return driver

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
    "NoSuchElementException",
    "WebDriverException",
]
