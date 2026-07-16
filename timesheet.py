import os
from pathlib import Path

from authautomate import get_auth_code
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv(Path(__file__).parent / ".env")

EMPLOYEE_ID = os.environ["EMPLOYEE_ID"]
TIMESHEET_URL = os.environ["TIMESHEET_URL"]
TIMESHEET_HOURS = os.environ["TIMESHEET_HOURS"]

options = webdriver.EdgeOptions()
options.add_experimental_option("detach", True)
driver = webdriver.Edge(options=options)

try:
    driver.get(TIMESHEET_URL)
    wait = WebDriverWait(driver, 10)

    wait.until(EC.visibility_of_element_located((By.ID, "form1"))).send_keys(
        EMPLOYEE_ID
    )
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains( text(),'Proceed')]"))
    ).click()
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains( text(),'AuthCode')]"))
    ).click()

    auth_code = get_auth_code()

    wait.until(EC.visibility_of_element_located((By.ID, "authcode1"))).send_keys(
        auth_code
    )
    wait.until(EC.element_to_be_clickable((By.ID, "form-submit"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='menu-icon']"))).click()

    parentWindow = driver.current_window_handle
    wait.until(
        EC.element_to_be_clickable((By.XPATH, "(//a[text()='Timesheet Entry'])[3]"))
    ).click()

    wait.until(lambda d: len(d.window_handles) > 1)
    for window in driver.window_handles:
        if window != parentWindow:
            driver.switch_to.window(window)
            break

    wait.until(EC.url_contains("timesheetEntry"))
    effort_field = wait.until(
        EC.visibility_of_element_located((By.ID, "effortAssign01"))
    )
    effort_field.clear()
    effort_field.send_keys(TIMESHEET_HOURS)

    wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Submit')]"))
    ).click()

finally:
    raise Exception("Report to me, something isnt working and i will figure it out")
    driver.quit()
