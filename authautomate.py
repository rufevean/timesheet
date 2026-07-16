import os
from pathlib import Path

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from dotenv import load_dotenv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv(Path(__file__).parent / ".env")

APPIUM_HOST = os.environ["APPIUM_HOST"]
APPIUM_PORT = os.environ["APPIUM_PORT"]
DEVICE_NAME = os.environ["DEVICE_NAME"]
DEVICE_UNLOCK_PIN = os.environ["DEVICE_UNLOCK_PIN"]
TOTP_APP_PIN = os.environ["TOTP_APP_PIN"]
TOTP_APP_PACKAGE = os.environ["TOTP_APP_PACKAGE"]
BIOMETRIC_CANCEL_ID = os.environ["BIOMETRIC_CANCEL_ID"]
TOTP_PIN_INPUT_ID = os.environ["TOTP_PIN_INPUT_ID"]
TOTP_COPY_ID = os.environ["TOTP_COPY_ID"]


def get_auth_code():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = DEVICE_NAME
    options.set_capability("appium:noReset", True)
    options.set_capability("appium:dontStopAppOnReset", True)
    options.set_capability("appium:unlockType", "pin")
    options.set_capability("appium:unlockKey", DEVICE_UNLOCK_PIN)
    options.set_capability("appium:skipUnlock", False)
    options.set_capability("appium:unlockStrategy", "uiautomator")

    driver = webdriver.Remote(f"http://{APPIUM_HOST}:{APPIUM_PORT}", options=options)
    driver.unlock()

    try:
        wait = WebDriverWait(driver, 10)

        driver.activate_app(TOTP_APP_PACKAGE)
        cancel_button = wait.until(
            EC.element_to_be_clickable((AppiumBy.ID, BIOMETRIC_CANCEL_ID))
        )
        cancel_button.click()
        text_place = wait.until(
            EC.presence_of_element_located((AppiumBy.ID, TOTP_PIN_INPUT_ID))
        )
        text_place.click()
        driver.execute_script("mobile: type", {"text": TOTP_APP_PIN})
        copy_code = wait.until(
            EC.presence_of_element_located((AppiumBy.ID, TOTP_COPY_ID))
        )
        copy_code.click()
        auth_code = driver.get_clipboard_text()
        print("Auth Code retrieved:", auth_code)
        return auth_code

    finally:
        driver.quit()


"""
if you ever want to test standalone
"""
if __name__ == "__main__":
    code = get_auth_code()
    print("Auth Code:", code)
