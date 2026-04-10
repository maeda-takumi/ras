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
