
import os
import pytest
from d4kms_generic.service_environment import ServiceEnvironment
from playwright.sync_api import Playwright

url = f"https://d4k-sdw-staging.fly.dev"

@pytest.fixture(scope="session", autouse=True)
def setup():
  os.environ["PYTHON_ENVIRONMENT"] = "playwright"
  yield
  os.environ["PYTHON_ENVIRONMENT"] = "development"

@pytest.mark.playwright
def test_login(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  page.goto(url)
  page.get_by_role("link", name="Click here to register or").click()
  page.get_by_label("Email address").fill(username())
  page.get_by_label("Password").click()
  page.get_by_label("Password").fill(password())
  page.get_by_role("button", name="Show password").click()
  page.get_by_role("button", name="Continue", exact=True).click()
  context.close()
  browser.close()

@pytest.mark.playwright
def test_load_m11(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  page.goto(url)
  page.get_by_role("link", name="Click here to register or").click()
  page.get_by_label("Email address").click()
  page.get_by_label("Email address").fill("daveih1664dk@gmail.com")
  page.get_by_label("Password").click()
  page.get_by_label("Password").fill("Something34#Secure")
  page.get_by_role("button", name="Show password").click()
  page.get_by_role("button", name="Continue", exact=True).click()
  page.get_by_role("button", name=" Import").click()
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.locator("#files").click()
  page.locator("#files").set_input_files("/Users/daveih/Documents/python/study_definitions_workbench/tests/test_files/M11-Protocols/ICH_M11_Template_RadVax_Example_Mods.docx")
  page.get_by_role("button", name=" Upload File(s)").click()
  page.get_by_role("link").first.click()
  page.get_by_role("button", name=" Import").click()
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.locator("#files").click()
  page.locator("#files").set_input_files("/Users/daveih/Documents/python/study_definitions_workbench/tests/test_files/M11-Protocols/ICH_M11_Template_LZZT_Example_Estimand.docx")
  page.get_by_role("button", name=" Upload File(s)").click()
  page.get_by_role("button", name="Home").click()
  page.get_by_role("button", name=" Import").click()
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.locator("#files").click()
  page.locator("#files").set_input_files("/Users/daveih/Documents/python/study_definitions_workbench/tests/test_files/M11-Protocols/ICH_M11_Template_IGBJ_Example_Estimand.docx")
  page.get_by_role("button", name=" Upload File(s)").click()
  page.get_by_role("link").first.click()
  context.close()
  browser.close()

def username():
  se = ServiceEnvironment()
  value = se.get("USERNAME")
  return value

def password():
  se = ServiceEnvironment()
  value = se.get("PASSWORD")
  return value
