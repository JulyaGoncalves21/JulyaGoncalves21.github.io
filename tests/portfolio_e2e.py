"""Browser checks for language switching, responsive layout and case-study dialogs."""

import json
import os
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.getenv("PORTFOLIO_URL", "http://127.0.0.1:8765/")
SCREENSHOT_DIR = os.getenv("PORTFOLIO_SCREENSHOT_DIR")
EDGE_BINARY = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def nested(content, path):
    value = content
    for key in path.split("."):
        value = value[key]
    return value


def assert_language(driver, language):
    expected = json.loads((ROOT / "content" / f"{language}.json").read_text(encoding="utf-8"))
    expected_lang = "pt-BR" if language == "pt" else "en"
    assert driver.find_element(By.TAG_NAME, "html").get_attribute("lang") == expected_lang

    for element in driver.find_elements(By.CSS_SELECTOR, "[data-i18n]"):
        key = element.get_attribute("data-i18n")
        assert element.get_attribute("textContent").strip() == nested(expected, key), key
    for element in driver.find_elements(By.CSS_SELECTOR, "[data-i18n-aria]"):
        key = element.get_attribute("data-i18n-aria")
        assert element.get_attribute("aria-label") == nested(expected, key), key
    for element in driver.find_elements(By.CSS_SELECTOR, "[data-i18n-alt]"):
        key = element.get_attribute("data-i18n-alt")
        assert element.get_attribute("alt") == nested(expected, key), key

    active = driver.find_element(By.CSS_SELECTOR, f"[data-lang='{language}']")
    assert active.get_attribute("aria-pressed") == "true"
    assert active.get_attribute("aria-current") == "true"


def switch_language(driver, language):
    driver.find_element(By.CSS_SELECTOR, f"[data-lang='{language}']").click()
    expected_lang = "pt-BR" if language == "pt" else "en"
    WebDriverWait(driver, 10).until(
        lambda item: item.find_element(By.TAG_NAME, "html").get_attribute("lang") == expected_lang
    )
    assert_language(driver, language)


def assert_dialogs(driver, width):
    for dialog_id in ("vehicle-dialog", "kaizen-dialog", "analytics-dialog"):
        trigger = driver.find_element(By.CSS_SELECTOR, f"[data-dialog='{dialog_id}']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
        WebDriverWait(driver, 5).until(lambda _: trigger.is_displayed() and trigger.is_enabled())
        trigger.send_keys(Keys.ENTER)
        dialog = driver.find_element(By.ID, dialog_id)
        WebDriverWait(driver, 5).until(lambda _: dialog.get_property("open") is True)
        if SCREENSHOT_DIR and dialog_id == "analytics-dialog":
            driver.save_screenshot(str(Path(SCREENSHOT_DIR) / f"{width}-analytics-dialog.png"))
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        WebDriverWait(driver, 5).until(lambda _: dialog.get_property("open") is False)
        assert driver.execute_script("return document.activeElement === arguments[0]", trigger)


def run_viewport(width, height):
    options = webdriver.EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument(f"--window-size={width},{height}")
    if EDGE_BINARY.exists():
        options.binary_location = str(EDGE_BINARY)

    driver = webdriver.Edge(options=options)
    try:
        driver.set_window_size(width, height)
        driver.get(f"{BASE_URL}?lang=en")
        WebDriverWait(driver, 10).until(
            lambda item: item.find_element(By.CSS_SELECTOR, "[data-lang='en']").get_attribute("aria-current") == "true"
        )
        assert_language(driver, "en")
        if SCREENSHOT_DIR:
            output = Path(SCREENSHOT_DIR)
            output.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(str(output / f"{width}-en.png"))
        switch_language(driver, "pt")
        if SCREENSHOT_DIR:
            driver.save_screenshot(str(output / f"{width}-pt.png"))
        switch_language(driver, "en")
        if SCREENSHOT_DIR:
            projects = driver.find_element(By.ID, "projects")
            driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", projects)
            driver.save_screenshot(str(output / f"{width}-projects.png"))
        assert_dialogs(driver, width)
        assert driver.execute_script("return document.documentElement.scrollWidth <= window.innerWidth + 1")

        if width <= 620:
            menu = driver.find_element(By.CSS_SELECTOR, ".menu-toggle")
            menu.click()
            assert menu.get_attribute("aria-expanded") == "true"
            assert "is-open" in driver.find_element(By.ID, "site-nav").get_attribute("class")
    finally:
        driver.quit()


if __name__ == "__main__":
    run_viewport(1440, 1000)
    run_viewport(390, 844)
    print("portfolio_e2e: PASS (EN/PT, dialogs, desktop, mobile)")
