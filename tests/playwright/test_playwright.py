
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

  expect(page.get_by_role("paragraph")).to_contain_text("Welcome to the d4k Study Definitions Workbench. Click on the button below to register or login.")
  expect(page.get_by_role("paragraph")).to_contain_text("A basic user guide can be downloaded from")
  expect(page.get_by_role("paragraph")).to_contain_text("Our privacy policye can be downloaded from")  
  with page.expect_download() as download_info:
    page.get_by_role("link", name="here").first.click()
  download = download_info.value
  download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
  with page.expect_download() as download_info:
    page.get_by_role("link", name="here").nth(1).click()
  download = download_info.value
  download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

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
  expect(page.locator("body")).to_contain_text("USDM Version")
  expect(page.locator("body")).to_contain_text("Licence Information")
  page.get_by_role("button", name=" Help").click()
  page.get_by_role("link", name="Examples").click()
  expect(page.locator("h4")).to_contain_text("Example Files")
  page.get_by_role("button", name=" Help").click()
  page.get_by_role("link", name="Issues & Feedback").click()
  expect(page.locator("h4")).to_contain_text("Issues and Feedback")
  expect(page.get_by_role("link", name="bug / issue")).to_be_visible()
  expect(page.get_by_role("link", name="discussion topic")).to_be_visible()
  page.get_by_role("button", name=" Help").click()
  with page.expect_download() as download_info:
      page.get_by_role("link", name="User Guide").click()
  download = download_info.value
  download.save_as(f"tests/test_files/downloads/help/{download.suggested_filename}")
  page.get_by_role("button", name=" Help").click()
  with page.expect_download() as download_info:
      page.get_by_role("link", name="Privacy Policy").click()
  download = download_info.value
  download.save_as(f"tests/test_files/downloads/help/{download.suggested_filename}")

  context.close()
  browser.close()

@pytest.mark.playwright
def test_view_menu(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.get_by_role("link").first.click()
  page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
  page.get_by_role("button", name=" Views").click()
  expect(page.locator("#navBarMain")).to_contain_text("Safety View")
  expect(page.locator("#navBarMain")).to_contain_text("Statistics View")
  expect(page.locator("#navBarMain")).to_contain_text("Protocol")
  expect(page.locator("#navBarMain")).to_contain_text("Version History")

  page.get_by_role("link", name="Safety View").click()
  page.get_by_role("button", name=" Views").click()
  expect(page.locator("#navBarMain")).to_contain_text("Summary View")
  expect(page.locator("#navBarMain")).to_contain_text("Statistics View")
  expect(page.locator("#navBarMain")).to_contain_text("Protocol")
  expect(page.locator("#navBarMain")).to_contain_text("Version History")

  page.get_by_role("link", name="Statistics View").click()
  page.get_by_role("button", name=" Views").click()
  expect(page.locator("#navBarMain")).to_contain_text("Summary View")
  expect(page.locator("#navBarMain")).to_contain_text("Safety View")
  expect(page.locator("#navBarMain")).to_contain_text("Protocol")
  expect(page.locator("#navBarMain")).to_contain_text("Version History")

  page.get_by_role("link", name="Protocol").click()
  page.get_by_role("button", name=" Views").click()
  expect(page.locator("#navBarMain")).to_contain_text("Summary View")
  expect(page.locator("#navBarMain")).to_contain_text("Safety View")
  expect(page.locator("#navBarMain")).to_contain_text("Statistics View")
  expect(page.locator("#navBarMain")).to_contain_text("Version History")

  page.get_by_role("link", name="Version History").click()
  page.get_by_role("button", name=" Views").click()
  expect(page.locator("#navBarMain")).to_contain_text("Summary View")
  expect(page.locator("#navBarMain")).to_contain_text("Safety View")
  expect(page.locator("#navBarMain")).to_contain_text("Statistics View")
  expect(page.locator("#navBarMain")).to_contain_text("Protocol")

  context.close()
  browser.close()

@pytest.mark.playwright
def test_export_import(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.get_by_role("link", name=" DIH").click()
  page.once("dialog", lambda dialog: dialog.accept())
  page.get_by_role("link", name=" Delete Database").click()
  page.get_by_role("link", name=" Home").click()

  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/m11/WA42380/WA42380.docx"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of M11")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()
  
  page.get_by_role("link", name=" View Details").click()
  page.get_by_role("button", name=" Export").click()
  with page.expect_download() as download_info:
      page.get_by_role("link", name="M11 FHIR v1, Dallas 2024").click()
  download = download_info.value
  page.get_by_role("navigation").get_by_role("link").first.click()
  page.get_by_role("button", name=" Import").click()
  page.get_by_role("link", name="M11 FHIR v1, Dallas 2024").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/fhir_v1/WA42380.json"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of FHIR")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()
  
  expect(page.locator("#card_1_div")).to_contain_text("A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA")
  expect(page.locator("#card_2_div")).to_contain_text("A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA")
  page.locator("#card_2_div").get_by_role("link", name=" View Details").click()
  expect(page.get_by_role("img", name="alt text")).to_be_visible()
  page.get_by_role("navigation").get_by_role("link").first.click()
  page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
  expect(page.get_by_role("img", name="alt text")).to_be_visible()

  context.close()
  browser.close()

@pytest.mark.playwright
def test_selection_menu(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.locator("#card_1_div").get_by_role("button", name=" Select").click()
  expect(page.get_by_role("button", name=" Selection")).to_be_visible()
  page.get_by_role("button", name=" Selection").click()
  expect(page.get_by_role("button", name=" Delete selected studies")).to_be_visible()
  expect(page.get_by_role("button", name=" List selected studies")).to_be_visible()
  page.get_by_role("button", name=" Deselect").click()
  expect(page.get_by_role("button", name=" Selection")).to_be_hidden()

  context.close()
  browser.close()

@pytest.mark.playwright
def test_selection_list(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)

  page.get_by_role("link", name=" DIH").click()
  page.once("dialog", lambda dialog: dialog.accept())
  page.get_by_role("link", name=" Delete Database").click()
  page.get_by_role("link", name=" Home").click()
  
  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/m11/WA42380/WA42380.docx"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of M11")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()

  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.set_input_files("#files", os.path.join(path, "tests/test_files/m11/ASP8062/ASP8062.docx"))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of M11")).to_be_visible(timeout=30_000)
  page.get_by_role("link").first.click()

  page.locator("#card_1_div").get_by_role("button", name=" Select").click()
  page.locator("#card_2_div").get_by_role("button", name=" Select").click()
  page.get_by_role("button", name=" Selection").click()
  page.get_by_role("button", name=" List selected studies").click()
  expect(page.get_by_role("rowgroup")).to_contain_text("A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA")
  expect(page.get_by_role("rowgroup")).to_contain_text("A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants")
  
  context.close()
  browser.close()

@pytest.mark.playwright
def test_selection_delete(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)
  delete_db(page)
  
  load_m11(page, path, "tests/test_files/m11/WA42380/WA42380.docx")
  load_m11(page, path, "tests/test_files/m11/ASP8062/ASP8062.docx")
  
  page.get_by_role("link").first.click()
  page.locator("#card_1_div").get_by_role("button", name=" Select").click()
  page.locator("#card_2_div").get_by_role("button", name=" Select").click()
  page.get_by_role("button", name=" Selection").click()
  page.once("dialog", lambda dialog: dialog.accept())
  page.get_by_role("button", name=" Delete selected studies").click()
  expect(page.get_by_role("paragraph")).to_contain_text("You have not loaded any studies yet. Use the import menu to upload one or more studies. Examples files can be downloaded by clicking on the help menu and selcting the examples option.")
  
  context.close()
  browser.close()

@pytest.mark.playwright
def test_pagination(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  path = filepath()
  page.goto(url)

  login(page)
  delete_db(page)

  load_m11(page, path, "tests/test_files/m11/WA42380/WA42380.docx")
  load_m11(page, path, "tests/test_files/m11/ASP8062/ASP8062.docx")
  load_m11(page, path, "tests/test_files/m11/RadVax/RadVax.docx")
  load_m11(page, path, "tests/test_files/m11/LZZT/LZZT.docx")
  load_fhir(page, path, "tests/test_files/fhir_v1/IGBJ.json")
  load_fhir(page, path, "tests/test_files/fhir_v1/WA42380.json")
  load_fhir(page, path, "tests/test_files/fhir_v1/ASP8062.json")
  load_fhir(page, path, "tests/test_files/fhir_v1/DEUCRALIP.json")
  load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

  page.get_by_role("link").first.click()
  page.get_by_label("Items to Display: 12 8 12 24 48").click()
  expect(page.get_by_label("Items to Display: 12 8 12 24 48")).to_be_visible()
  page.get_by_role("link", name="8", exact=True).click()
  expect(page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")).to_be_visible()
  expect(page.get_by_role("button", name="«")).to_be_visible()
  expect(page.get_by_role("button", name="1")).to_be_visible()
  expect(page.get_by_role("button", name="2")).to_be_visible()
  expect(page.get_by_role("button", name="»")).to_be_visible()
  page.get_by_role("button", name="2").click()
  expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()
  page.get_by_label("Items to Display: 8 8 12 24 48").click()
  expect(page.get_by_label("Items to Display: 8 8 12 24 48")).to_be_visible()
  page.get_by_label("Items to Display: 8 8 12 24 48").click()
  expect(page.get_by_role("button", name="«")).to_be_visible()
  expect(page.get_by_role("button", name="1")).to_be_visible()
  expect(page.get_by_role("button", name="2")).to_be_visible()
  expect(page.get_by_role("button", name="»")).to_be_visible()
  page.get_by_role("button", name="1").click()
  expect(page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")).to_be_visible()
  #expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()
  page.get_by_role("button", name="»").click()
  expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()
  page.get_by_role("button", name="«").click()
  expect(page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")).to_be_visible()
  page.get_by_label("Items to Display: 8 8 12 24 48").click()
  page.get_by_role("link", name="96").click()
  page.get_by_label("Items to Display: 96 8 12 24 48").click()
  expect(page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")).to_be_visible()
  expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()

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
  page.get_by_role("button", name="Continue", exact=True).click()

def load_excel(page, root_path, filepath):
  page.get_by_role("link").first.click()
  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="USDM Excel (.xlsx)").click()
  page.set_input_files("#files", os.path.join(root_path, filepath))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of Excel")).to_be_visible(timeout=30_000)

def load_m11(page, root_path, filepath):
  page.get_by_role("link").first.click()
  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 Document (.docx)").click()
  page.set_input_files("#files", os.path.join(root_path, filepath))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of M11")).to_be_visible(timeout=30_000)

def load_fhir(page, root_path, filepath):
  page.get_by_role("link").first.click()
  page.get_by_role("button", name=" Import").click()  
  page.get_by_role("link", name="M11 FHIR v1, Dallas 2024").click()
  page.set_input_files("#files", os.path.join(root_path, filepath))
  page.locator("text = Upload File(s)").last.click()
  expect(page.get_by_text("Success: Import of FHIR")).to_be_visible(timeout=30_000)

def delete_db(page):
  page.get_by_role("link", name=" DIH").click()
  page.once("dialog", lambda dialog: dialog.accept())
  page.get_by_role("link", name=" Delete Database").click()
  page.get_by_role("link", name=" Home").click()
