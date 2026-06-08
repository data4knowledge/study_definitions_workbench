import os
import pytest
from playwright.sync_api import Playwright, expect

# site_url = "https://d4k-sdw-staging.fly.dev"
# site_url = f"https://d4k-sdw.fly.dev"
site_url = f"http://localhost:8000"


@pytest.mark.playwright
def test_populate(playwright: Playwright) -> None:
    # Target runs in single-user mode (SINGLE_USER set), so the server
    # auto-provisions the session — no login/registration step required.
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(site_url)

    load_m11(page, path, "tests/test_files/m11/WA42380/WA42380.docx")
    load_m11(page, path, "tests/test_files/m11/ASP8062/ASP8062.docx")
    load_m11(page, path, "tests/test_files/m11/RadVax/RadVax.docx")
    load_m11(page, path, "tests/test_files/m11/LZZT/LZZT.docx")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/IGBJ_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/WA42380_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/ASP8062_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/DEUCRALIP_fhir_m11.json")
    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

    context.close()
    browser.close()


def filepath():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_excel(page, root_path, filepath):
    home_page_wait(page)
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="USDM Excel (.xlsx)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=60_000)


def load_m11(page, root_path, filepath):
    home_page_wait(page)
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=60_000)


def load_fhir(page, root_path, filepath):
    home_page_wait(page)
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 FHIR, IG (PRISM 3)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=60_000)


def load_usdm(page, root_path, filepath, version, result):
    home_page_wait(page)
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name=f"USDM v{version} (.json)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text(f"{result}")).to_be_visible(timeout=60_000)


def home_page_wait(page):
    # Navigate straight to /index rather than clicking the first link on the
    # page — on the splash/help pages the first link is the user-guide link,
    # which is what previously derailed the run.
    page.goto(f"{site_url}/index")
    page.wait_for_load_state("domcontentloaded")
