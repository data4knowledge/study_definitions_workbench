
import os
import pytest
from d4kms_generic.service_environment import ServiceEnvironment
from playwright.sync_api import Playwright, expect
from app.__init__ import VERSION

#url = f"https://d4k-sdw-staging.fly.dev"
url = f"http://localhost:8000"

@pytest.fixture(scope="session", autouse=True)
def setup():
  os.environ["PYTHON_ENVIRONMENT"] = "playwright"
  yield
  os.environ["PYTHON_ENVIRONMENT"] = "development"


@pytest.mark.playwright
def test_splash(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  page.goto(url)

  expect(page.get_by_role("paragraph")).to_contain_text("Welcome to the d4k Study Definitions Workbench. Click on the button below to register or login. A basic user guide can be downloaded from here.")
  with page.expect_download() as download_info:
    page.get_by_role("link", name="here", exact=True).click()
  download = download_info.value

  context.close()
  browser.close()

@pytest.mark.playwright
def test_login(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  page.goto(url)

  login(page)

  context.close()
  browser.close()

@pytest.mark.playwright
def test_logout(playwright: Playwright) -> None:

  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)
  
  login(page)

  page.get_by_role("link", name=" Logout").click()
  expect(page.get_by_role("paragraph")).to_contain_text("Welcome to the d4k Study Definitions Workbench. Click on the button below to register or login.")

  context.close()
  browser.close()

@pytest.mark.playwright
def test_clear_db(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  page.goto(url)

  login(page)

  page.get_by_role("link", name=" DIH").click()
  page.once("dialog", lambda dialog: dialog.accept())
  page.get_by_role("link", name=" Delete Database").click()

  context.close()
  browser.close()

@pytest.mark.playwright
def test_load_m11(playwright: Playwright) -> None:

  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)
  
  login(page)
  
  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/m11/RadVax/RadVax.docx"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of M11")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()
  expect(page.get_by_text("RADVAX™: A Stratified Phase I Trial of Pembrolizumab with Hypofractionated Radiotherapy in Patients with Advanced and Metastatic Cancers")).to_be_visible()
  
  context.close()
  browser.close()

@pytest.mark.playwright
def test_load_excel(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="USDM Excel (.xlsx)").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/excel/pilot.xlsx"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of Excel")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()
  expect(page.get_by_text("Safety and Efficacy of the Xanomeline Transdermal Therapeutic System (TTS) in Patients with Mild to Moderate Alzheimer's Disease")).to_be_visible()

  context.close()
  browser.close()

@pytest.mark.playwright
def test_load_fhir_v1(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 FHIR v1, Dallas 2024").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/fhir_v1/ASP8062.json"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of FHIR")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()
  expect(page.get_by_text("A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants")).to_be_visible()

  context.close()
  browser.close()

@pytest.mark.playwright
def test_help(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.get_by_role("button", name=" Help").click()
  page.get_by_role("link", name="About").click()
  expect(page.locator("body")).to_contain_text(f"d4k Study Definitions Workbench (v{VERSION})")
  expect(page.locator("body")).to_contain_text("Release Log")
  expect(page.locator("body")).to_contain_text("Licence Information")
  page.get_by_role("button", name=" Help").click()
  page.get_by_role("link", name="Examples").click()
  expect(page.locator("h4")).to_contain_text("Example Files")
  page.get_by_role("button", name=" Help").click()
  page.get_by_role("link", name="Issues & Feedback").click()
  expect(page.locator("h4")).to_contain_text("Issues and Feedback")
  expect(page.get_by_role("link", name="bug / issue")).to_be_visible()
  expect(page.get_by_role("link", name="discussion topic")).to_be_visible()

def username():
  se = ServiceEnvironment()
  value = se.get("USERNAME")
  return value

def password():
  se = ServiceEnvironment()
  value = se.get("PASSWORD")
  return value

def filepath():
  se = ServiceEnvironment()
  value = se.get("FILEPATH")
  return value

def login(page):
  page.get_by_role("link", name="Click here to register or").click()
  page.get_by_label("Email address").click()
  page.get_by_label("Email address").fill(username())
  page.get_by_label("Password").click()
  page.get_by_label("Password").fill(password())
  page.get_by_role("button", name="Show password").click()
  page.get_by_role("button", name="Continue", exact=True).click()
