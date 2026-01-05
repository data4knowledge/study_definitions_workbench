import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Playwright, expect
from app.__init__ import VERSION

# url = f"https://d4k-sdw-staging.fly.dev"
url = "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def setup():
    os.environ["PYTHON_ENVIRONMENT"] = "playwright"
    load_dotenv(".playwright_env", override=True)
    yield
    os.environ["PYTHON_ENVIRONMENT"] = "development"


@pytest.mark.playwright
def test_splash(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)

    expect(page.get_by_role("paragraph")).to_contain_text(
        "Welcome to the d4k Study Definitions Workbench. Click on the button below to register or login."
    )
    expect(page.get_by_role("paragraph")).to_contain_text(
        "A basic user guide can be downloaded from"
    )
    expect(page.get_by_role("paragraph")).to_contain_text(
        "Our privacy policy can be downloaded from"
    )
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
    # path = filepath()
    page.goto(url)

    login(page)

    page.get_by_role("link", name=" Logout").click()
    expect(page.get_by_role("paragraph")).to_contain_text(
        "Welcome to the d4k Study Definitions Workbench. Click on the button below to register or login."
    )

    context.close()
    browser.close()


@pytest.mark.playwright
def test_clear_db(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)

    login(page)

    page.get_by_role("link", name=f" {display_name()}").click()
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

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/m11/RadVax/RadVax.docx")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of 'RadVax.docx'")).to_be_visible(
        timeout=30_000
    )
    page.get_by_role("link").first.click()
    expect(
        page.get_by_text(
            "RADVAX™: A Stratified Phase I Trial of Pembrolizumab with Hypofractionated Radiotherapy in Patients with Advanced and Metastatic Cancers"
        )
    ).to_be_visible()

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

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="USDM Excel (.xlsx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/excel/pilot.xlsx")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of 'pilot.xlsx'")).to_be_visible(
        timeout=30_000
    )
    page.get_by_role("link").first.click()
    expect(
        page.get_by_text(
            "Safety and Efficacy of the Xanomeline Transdermal Therapeutic System (TTS) in Patients with Mild to Moderate Alzheimer's Disease"
        )
    ).to_be_visible()

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

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
    page.set_input_files(
        "#files",
        os.path.join(path, "tests/test_files/fhir_v1/from/ASP8062_fhir_m11.json"),
    )
    page.locator("text = Upload File(s)").last.click()
    expect(
        page.get_by_text("Success: Import of 'ASP8062_fhir_m11.json'")
    ).to_be_visible(timeout=30_000)
    page.get_by_role("link").first.click()
    expect(
        page.get_by_text(
            "A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants"
        )
    ).to_be_visible()

    context.close()
    browser.close()


@pytest.mark.playwright
def test_help(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    # path = filepath()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" Help").click()
    page.get_by_role("link", name="About").click()
    expect(page.locator("body")).to_contain_text(
        f"d4k Study Definitions Workbench (v{VERSION})"
    )
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
    # path = filepath()
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

    page.get_by_role("link", name=f" {display_name()}").click()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("link", name=" Delete Database").click()
    page.get_by_role("link", name=" Home").click()

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/m11/WA42380/WA42380.docx")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)
    page.get_by_role("link").first.click()

    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
    _ = download_info.value
    page.get_by_role("navigation").get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
    page.set_input_files(
        "#files",
        os.path.join(path, "tests/test_files/fhir_v1/from/WA42380_fhir_m11.json"),
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)
    page.get_by_role("link").first.click()

    expect(page.locator("#card_1_div")).to_contain_text(
        "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
    )
    expect(page.locator("#card_2_div")).to_contain_text(
        "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
    )
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
    # path = filepath()
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

    page.get_by_role("link", name=f" {display_name()}").click()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("link", name=" Delete Database").click()
    page.get_by_role("link", name=" Home").click()

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/m11/WA42380/WA42380.docx")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)
    page.get_by_role("link").first.click()

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/m11/ASP8062/ASP8062.docx")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)
    page.get_by_role("link").first.click()

    page.locator("#card_1_div").get_by_role("button", name=" Select").click()
    page.locator("#card_2_div").get_by_role("button", name=" Select").click()
    page.get_by_role("button", name=" Selection").click()
    page.get_by_role("button", name=" List selected studies").click()
    expect(page.get_by_role("rowgroup")).to_contain_text(
        "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
    )
    expect(page.get_by_role("rowgroup")).to_contain_text(
        "A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants"
    )

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
    expect(page.get_by_role("paragraph")).to_contain_text(
        "You have not loaded any studies yet. Use the import menu to upload one or more studies. Examples files can be downloaded by clicking on the help menu and selcting the examples option."
    )

    context.close()
    browser.close()


@pytest.mark.playwright
def test_soa_export(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

    page.get_by_role("link").first.click()
    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    page.locator("li").filter(has_text="Main Timeline View").get_by_role("link").click()
    expect(page.locator("body")).to_contain_text(
        "Schedule of Activities: Main Timeline Back"
    )
    expect(page.locator("#navBarMain")).to_contain_text("Export")
    page.get_by_role("button", name=" Export").click()
    expect(page.locator("#navBarMain")).to_contain_text("FHIR SoA message (.json)")
    with page.expect_download() as download_info:
        page.get_by_role("link", name="FHIR SoA message (.json)").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

    context.close()
    browser.close()


@pytest.mark.playwright
def test_fhir_export_madrid_excel(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

    page.get_by_role("link").first.click()
    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Madrid (.").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Pittsburgh (PRISM 3").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

    context.close()
    browser.close()


@pytest.mark.playwright
def test_fhir_export_madrid_word(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_m11(page, path, "tests/test_files/m11/LZZT/LZZT.docx")

    page.get_by_role("link").first.click()
    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Madrid (.").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="M11 FHIR, Pittsburgh (PRISM 3").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

    context.close()
    browser.close()


@pytest.mark.playwright
def test_excel_v4_export(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_m11(page, path, "tests/test_files/m11/WA42380/WA42380.docx")

    page.get_by_role("link").first.click()
    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    expect(page.locator("#navBarMain")).to_contain_text("Export")
    page.get_by_role("button", name=" Export").click()
    expect(page.locator("#navBarMain")).to_contain_text("USDM v4 format Excel (.xlsx)")
    with page.expect_download() as download_info:
        page.get_by_role("link", name="USDM v4 format Excel (.xlsx)").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

    context.close()
    browser.close()


@pytest.mark.playwright
def test_excel_v3_export(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_m11(page, path, "tests/test_files/m11/WA42380/WA42380.docx")

    page.get_by_role("link").first.click()
    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    expect(page.locator("#navBarMain")).to_contain_text("Export")
    page.get_by_role("button", name=" Export").click()
    expect(page.locator("#navBarMain")).to_contain_text("USDM v3 format Excel (.xlsx)")
    with page.expect_download() as download_info:
        page.get_by_role("link", name="USDM v3 format Excel (.xlsx)").click()
    download = download_info.value
    download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

    context.close()
    browser.close()


@pytest.mark.playwright
def test_load_export_pj(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)
    
    login(page)
    delete_db(page)

    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="USDM Excel (.xlsx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/excel/pilot.xlsx")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of 'pilot.xlsx'")).to_be_visible(
        timeout=30_000
    )
    page.get_by_role("link").first.click()
    expect(
        page.get_by_text(
            "Safety and Efficacy of the Xanomeline Transdermal Therapeutic System (TTS) in Patients with Mild to Moderate Alzheimer's Disease"
        )
    ).to_be_visible()

    page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
    page.locator("li").filter(has_text="Main Timeline View").get_by_role("link").click()
    page.get_by_role("button", name=" Views").click()
    page.get_by_role("link", name="Patient Journey: Simple").click()
    page.get_by_role("tab", name=" Screen Two").click()
    page.get_by_role("tab", name=" Dose").click()
    page.get_by_role("tab", name=" Week 2", exact=True).click()
    page.get_by_role("tab", name=" Week 4").click()
    page.get_by_role("link", name=" Back").click()
    page.get_by_role("button", name=" Views").click()
    page.get_by_role("link", name="Patient Journey: Expanded").click()
    expect(page.locator("#timeline-svg").get_by_text("Screen One")).to_be_visible()
    page.get_by_role("link", name=" Back").click()

    # Exports
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Patient Journey: Simple (.").click()
    download = download_info.value
    page.get_by_role("button", name=" Export").click()
    with page.expect_download() as download1_info:
        page.get_by_role("link", name="Patient Journey: Expanded (.").click()
    download1 = download1_info.value

    context.close()
    browser.close()


@pytest.mark.playwright
def test_import_usdm_menus(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    # path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    page.get_by_role("button", name=" Import").click()
    expect(page.get_by_role("link", name="USDM v3 (.json)")).to_be_visible()
    expect(page.get_by_role("link", name="USDM v4 (.json)")).to_be_visible()
    page.get_by_role("button", name=" Import").click()

    context.close()
    browser.close()


@pytest.mark.playwright
def test_import_usdm(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_usdm(
        page, path, "tests/test_files/usdm3/no_errors.json", "3", "Success: Import of"
    )

    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="Import Status").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name=" Errors File").click()
    _ = download_info.value
    page.get_by_role("link", name=" Back").click()

    load_usdm(
        page, path, "tests/test_files/usdm4/no_errors.json", "4", "Success: Import of"
    )

    context.close()
    browser.close()


@pytest.mark.playwright
def test_import_usdm_errors(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_usdm(
        page,
        path,
        "tests/test_files/usdm3/errors.json",
        "3",
        "Error: Error encountered",
    )

    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="Import Status").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name=" Errors File").click()
    _ = download_info.value
    page.get_by_role("link", name=" Back").click()

    load_usdm(
        page,
        path,
        "tests/test_files/usdm4/errors.json",
        "4",
        "Error: Error encountered",
    )

    context.close()
    browser.close()


@pytest.mark.playwright
def test_import_status_and_diff(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_m11(page, path, "tests/test_files/m11/LZZT/LZZT.docx")
    load_usdm(
        page, path, "tests/test_files/usdm3/no_errors.json", "3", "Success: Import of"
    )
    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")
    load_excel(page, path, "tests/test_files/excel/pilot_tweak.xlsx")

    page.get_by_role("navigation").get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="Import Status").click()
    expect(page.get_by_role("cell", name="LZZT.docx")).to_be_visible()
    expect(page.get_by_role("cell", name="no_errors.json")).to_be_visible()
    expect(page.get_by_role("cell", name="pilot.xlsx")).to_be_visible()
    expect(page.get_by_role("cell", name="pilot_tweak.xlsx")).to_be_visible()
    # expect(page.get_by_text("No errors file available")).to_be_visible()

    cell = page.locator("table > tbody > tr").nth(0).locator("td").nth(2)
    expect(cell).to_contain_text("LZZT.docx")
    cell = page.locator("table > tbody > tr").nth(1).locator("td").nth(2)
    expect(cell).to_contain_text("no_errors.json")
    cell = page.locator("table > tbody > tr").nth(2).locator("td").nth(2)
    expect(cell).to_contain_text("pilot.xlsx")
    cell = page.locator("table > tbody > tr").nth(3).locator("td").nth(2)
    expect(cell).to_contain_text("pilot_tweak.xlsx")
    with page.expect_download() as download_info:
        cell = page.locator("table > tbody > tr").nth(1).locator("td").nth(4)
        cell.get_by_role("link").click()
    _ = download_info.value
    with page.expect_download() as download_info1:
        cell = page.locator("table > tbody > tr").nth(3).locator("td").nth(4)
        cell.get_by_role("link").click()
    _ = download_info1.value
    page.get_by_role("link", name=" Back").click()
    page.locator("#card_3_div").get_by_role("link", name=" View Details").click()
    page.get_by_role("button", name=" Views").click()
    page.get_by_role("link", name="Version History").click()
    expect(page.get_by_role("cell", name="pilot.xlsx")).to_be_visible()
    expect(page.get_by_role("cell", name="pilot_tweak.xlsx")).to_be_visible()
    expect(page.get_by_role("link", name=" USDM JSON Diff")).to_be_visible()
    row = page.get_by_role("row", name="1 pilot.xlsx USDM_EXCEL")
    link = row.get_by_role("link", name=" USDM JSON Viewer").first
    link.click()
    expect(
        page.get_by_role(
            "heading",
            name="Sponsor: Eli Lilly | Phase: Phase II Trial | Identifier: | Version: 2",
        )
    ).to_be_visible()
    page.get_by_role("link", name=" Back").click()
    page.get_by_role("link", name=" USDM JSON Diff").click()
    expect(
        page.get_by_role(
            "heading",
            name="Sponsor: Eli Lilly | Phase: Phase II Trial | Identifier: | Version: 2",
        )
    ).to_be_visible()
    expect(page.get_by_role("cell", name='"text": "LZZT - NEW"')).to_be_visible()
    expect(page.get_by_role("cell", name='"text": "New public title"')).to_be_visible()
    page.get_by_role("link", name=" Back").click()
    page.get_by_role("navigation").get_by_role("link").first.click()

    # ---------------------
    context.close()
    browser.close()


@pytest.mark.playwright
def test_json_explorer(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")
    page.get_by_role("link").first.click()
    page.get_by_role("link", name=" View Details").click()

    page.get_by_role("button", name=" Views").click()
    page.get_by_role("link", name="Version History").click()
    page.get_by_role("link", name=" USDM JSON Explorer").click()
    page.get_by_label("Select Class:").select_option("Activity")
    page.get_by_label("Select Instance:").select_option("Activity_1")
    page.locator("circle").first.click()
    expect(page.locator("#detailsPanelTitle")).to_contain_text("Activity")
    expect(page.locator("#detailsContent")).to_contain_text("Activity_1")

    context.close()
    browser.close()


# ---------------------------------------------------------
# Add tests before here and leave the following to run last
# ---------------------------------------------------------


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
    load_fhir(page, path, "tests/test_files/fhir_v1/from/IGBJ_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/WA42380_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/ASP8062_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v1/from/DEUCRALIP_fhir_m11.json")
    load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

    page.get_by_role("link").first.click()
    page.get_by_label("Items: 12 4 8 12 24 48").click()
    expect(page.get_by_label("Items: 12 4 8 12 24 48")).to_be_visible()
    page.get_by_role("link", name="8", exact=True).click()
    expect(
        page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")
    ).to_be_visible()
    expect(page.get_by_role("button", name="«", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="1", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="2", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="»", exact=True)).to_be_visible()
    page.get_by_role("button", name="2", exact=True).click()
    expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()
    page.get_by_label("Items: 8 4 8 12 24 48").click()
    expect(page.get_by_label("Items: 8 4 8 12 24 48")).to_be_visible()
    page.get_by_label("Items: 8 4 8 12 24 48").click()
    expect(page.get_by_role("button", name="«", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="1", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="2", exact=True)).to_be_visible()
    expect(page.get_by_role("button", name="»", exact=True)).to_be_visible()
    page.get_by_role("button", name="1", exact=True).click()
    expect(
        page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")
    ).to_be_visible()
    # expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()
    page.get_by_role("button", name="»", exact=True).click()
    expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()
    page.get_by_role("button", name="«", exact=True).click()
    expect(
        page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")
    ).to_be_visible()
    page.get_by_label("Items: 8 4 8 12 24 48").click()
    page.get_by_role("link", name="48", exact=True).click()
    page.get_by_label("Items: 48 4 8 12 24 48").click()
    expect(
        page.get_by_role("heading", name="University of Pennsylvania: IRB# 821403")
    ).to_be_visible()
    expect(page.get_by_text("USDM Excel", exact=True)).to_be_visible()

    context.close()
    browser.close()


# Expects data from previous test
@pytest.mark.playwright
def test_filter(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)

    login(page)

    expect(page.get_by_role("button", name=" Sponsors")).to_be_visible()
    expect(page.get_by_role("button", name=" Phases")).to_be_visible()
    expect(page.get_by_role("button", name=" Filter")).to_be_visible()

    # Check sponsor menu
    page.get_by_role("button", name=" Sponsors").click()
    expect(page.get_by_text("Astellas Pharma", exact=True)).to_be_visible()
    expect(page.get_by_text("Eli Lilly", exact=True)).to_be_visible()
    expect(page.get_by_text("Eli Lilly and Company", exact=True)).to_be_visible()
    expect(page.get_by_text("University of Pennsylvania", exact=True)).to_be_visible()
    page.get_by_role("button", name=" Sponsors").click()

    # Check Phase menu
    page.get_by_role("button", name=" Phases").click()
    expect(page.get_by_text("Phase I Trial Phase II Trial")).to_be_visible()
    page.get_by_role("button", name=" Phases").click()

    # Check filter
    page.get_by_role("button", name=" Sponsors").click()
    page.locator("li").filter(has_text="Astellas Pharma").get_by_role(
        "checkbox"
    ).uncheck()
    page.get_by_role("button", name=" Phases").click()
    page.locator("li").filter(has_text="Phase I Trial").get_by_role(
        "checkbox"
    ).uncheck()
    page.locator("li").filter(has_text="Phase II Trial").get_by_role(
        "checkbox"
    ).uncheck()
    page.get_by_role("button", name=" Filter").click()
    expect(page.get_by_text("« 1 »")).to_be_visible()
    expect(page.locator("#card_1_div")).to_contain_text(
        "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
    )
    expect(page.locator("#card_4_div")).to_contain_text(
        "Safety and Efficacy of the Xanomeline Transdermal Therapeutic System (TTS) in Patients with Mild to Moderate Alzheimer’s Disease"
    )
    expect(page.locator("#card_6_div")).to_contain_text(
        "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
    )

    # Check filter
    page.get_by_role("button", name=" Sponsors").click()
    page.locator("li").filter(has_text="Astellas Pharma").get_by_role(
        "checkbox"
    ).check()
    page.locator("li:nth-child(2) > .ms-1").first.uncheck()
    page.locator("li").filter(has_text="Eli Lilly Japan K.K").get_by_role(
        "checkbox"
    ).uncheck()
    page.locator("li").filter(has_text="Eli Lilly and Company").get_by_role(
        "checkbox"
    ).uncheck()
    page.locator("li").filter(has_text="F. Hoffmann-La Roche Ltd").get_by_role(
        "checkbox"
    ).uncheck()
    page.locator("li").filter(has_text="Rheinische Friedrich-Wilhelms").get_by_role(
        "checkbox"
    ).uncheck()
    page.locator("li").filter(has_text="University of Pennsylvania").get_by_role(
        "checkbox"
    ).uncheck()
    page.get_by_role("button", name=" Phases").click()
    page.locator("li").filter(has_text="Phase I Trial").get_by_role("checkbox").check()
    page.locator("li").filter(has_text="Phase II Trial").get_by_role("checkbox").check()
    page.get_by_role("button", name=" Filter").click()
    expect(page.locator("#card_2_div")).to_contain_text(
        "A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants"
    )
    expect(page.locator("#card_7_div")).to_contain_text(
        "A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants"
    )
    expect(page.get_by_text("« 1 »")).to_be_visible()

    context.close()
    browser.close()


# Expects data from previous test
@pytest.mark.playwright
def test_m11(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" ICH M11").click()
    page.get_by_role("link", name="M11 Specification").click()
    page.get_by_role("link", name="Sponsor Confidentiality").click()
    page.locator("#specification-card div").filter(
        has_text="Template Specification Long"
    ).locator("i").click()
    expect(page.locator("#data-div")).to_contain_text(
        "M11 Specification: Sponsor Confidentiality Statement"
    )
    expect(page.locator("#template-div")).to_contain_text(
        "Enter Sponsor Confidentiality Statement"
    )
    page.locator("#specification-card i").nth(1).click()
    expect(page.locator("#technical-div")).to_contain_text(
        "Sponsor Confidentiality Statement"
    )
    page.locator("#specification-card div").filter(
        has_text="USDM Mapping Name Sponsor"
    ).locator("i").click()
    expect(page.locator("#usdm-div")).to_contain_text(
        "Sponsor Confidentiality Statement"
    )
    page.locator("#specification-card div").filter(
        has_text="FHIR M11 Mapping Resource"
    ).locator("i").click()
    expect(page.locator("#fhir-div")).to_contain_text(
        "ResearchStudy.extension[confidentialityStatement]"
    )

    context.close()
    browser.close()


def username():
    value = os.environ["USERNAME"]
    return value


def display_name():
    return username().split("@")[0]


def password():
    value = os.environ["PASSWORD"]
    return value


def filepath():
    value = os.environ["FILEPATH"]
    return value


def login(page):
    page.get_by_role("link", name="Click here to register or").click()
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(username())
    # pwd = page.get_by_label("Password")
    pwd = page.locator("#password")
    pwd.click()
    pwd.fill(password())
    page.get_by_role("button", name="Continue", exact=True).click()


def load_excel(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="USDM Excel (.xlsx)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)


def load_m11(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 Document (.docx)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)


def load_fhir(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)


def load_usdm(page, root_path, filepath, version, result):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name=f"USDM v{version} (.json)").click()
    page.set_input_files("#files", os.path.join(root_path, filepath))
    page.locator("text = Upload File(s)").last.click()
    expect(page.get_by_text(f"{result}")).to_be_visible(timeout=30_000)


def delete_db(page):
    page.get_by_role("link", name=f" {display_name()}").click()
    page.once("dialog", lambda dialog: dialog.accept())
    page.get_by_role("link", name=" Delete Database").click()
    page.get_by_role("link", name=" Home").click()
