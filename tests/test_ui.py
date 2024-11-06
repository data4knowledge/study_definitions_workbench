import os
from d4kms_generic.service_environment import ServiceEnvironment
from playwright.sync_api import Playwright, sync_playwright, expect

base_url = "http://localhost:8000"

def test_run(playwright: Playwright) -> None:
  browser = playwright.chromium.launch(headless=False)
  context = browser.new_context()
  page = context.new_page()
  page.goto("http://localhost:8000/")
  page.get_by_role("link", name="Click here to register or").click()
  page.get_by_label("Email address").fill(username())
  page.get_by_label("Password").click()
  page.get_by_label("Password").fill(password())
  page.get_by_role("button", name="Show password").click()
  page.get_by_role("button", name="Continue", exact=True).click()
  page.get_by_text("Proof of concept study (").click()
  page.get_by_text("A Phase 3 Study of Nasal").click()
  page.get_by_role("button", name=" List selected studies").click()
  page.get_by_role("button", name=" Import").click()
  page.get_by_role("link", name="M11 Document (.docx)").click()
  with page.expect_file_chooser() as fc_info:
    page.locator("#files").click()
  file_chooser = fc_info.value
  file_chooser.set_files("./tests/test_files/m11.docx")
  page.locator('text=m11.docx').click();
  page.get_by_role("button", name=" Upload File(s)").click()
  page.get_by_role("link").first.click()
  page.locator("#card_3_div").get_by_role("link", name=" View Details").click()
  page.get_by_role("button", name=" Views").click()
  page.get_by_role("link", name="Safety View").click()
  page.get_by_role("button", name=" Views").click()
  page.get_by_role("link", name="Statistics View").click()
  page.get_by_role("button", name=" Views").click()
  page.get_by_role("link", name="Protocol").click()
  context.close()
  browser.close()

def username():
  se = ServiceEnvironment()
  value = se.get("USERNAME")
  #print(f"USERNAME: {value}")
  return value

def password():
  se = ServiceEnvironment()
  value = se.get('PASSWORD')  
  #print(f"PASSWORD: {value}")
  return value
