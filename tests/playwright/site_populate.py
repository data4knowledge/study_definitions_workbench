import os
import pytest
from d4k_ms_base.service_environment import ServiceEnvironment
from playwright.sync_api import Playwright, expect

# site_url = f"https://d4k-sdw-staging.fly.dev"
site_url = f"https://d4k-sdw.fly.dev"


@pytest.fixture(scope="session", autouse=True)
def setup():
    os.environ["PYTHON_ENVIRONMENT"] = "playwright"
    yield
    os.environ["PYTHON_ENVIRONMENT"] = "development"


@pytest.mark.playwright
def test_populate(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(site_url)

    login(page)
    # delete_db(page)

    load_m11(page, path, "tests/test_files/m11/WA42380/WA42380.docx")
    load_m11(page, path, "tests/test_files/m11/ASP8062/ASP8062.docx")
    load_m11(page, path, "tests/test_files/m11/RadVax/RadVax.docx")
    load_m11(page, path, "tests/test_files/m11/LZZT/LZZT.docx")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/IGBJ_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/WA42380_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/ASP8062_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/DEUCRALIP_fhir_m11.json")
    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

    logout(page)

    context.close()
    browser.close()


def username():
    se = ServiceEnvironment()
    value = se.get("DEMO_USERNAME")
    return value


def display_name():
    return "Guest Demo"


def password():
    se = ServiceEnvironment()
    value = se.get("DEMO_PASSWORD")
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


def logout(page):
    page.get_by_role("link").first.click()
    page.get_by_role("link", name=" Logout").click()


def load_excel(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="USDM Excel (.xlsx)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)


def load_m11(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)


def load_fhir(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 FHIR v1, Dallas 2024").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)


def load_usdm(page, root_path, filepath, version, result):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role(f"link", name=f"USDM v{version} (.json)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text(f"{result}")).to_be_visible(timeout=30_000)


def delete_db(page):
    page.get_by_role("link", name=f" {display_name()}").click()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("link", name=" Delete Database").click()
    page.get_by_role("link", name=" Home").click()
