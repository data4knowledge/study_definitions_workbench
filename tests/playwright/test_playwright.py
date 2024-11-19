
import os
import time
import uvicorn
import pytest
from multiprocessing import Process
from app.main import app
from app.model.database_manager import DatabaseManager
from playwright.sync_api import Playwright, sync_playwright, expect

port = 8000
url = f"http://localhost:{port}"

def start_server():
  uvicorn.run(app, host="0.0.0.0", port=port)

@pytest.fixture(scope="session", autouse=True)
def setup():
  proc = Process(target=start_server, args=())
  proc.start()
  time.sleep(2)
  yield
  proc.terminate()

@pytest.mark.playwright
def test_login(playwright: Playwright, db) -> None:
  database = DatabaseManager(db)
  database.clear_all()
  database.clear_users()
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
  value = os.environ["USERNAME"]
  return value

def password():
  value = os.environ["PASSWORD"]
  return value
