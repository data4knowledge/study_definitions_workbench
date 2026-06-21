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
        "A basic user guide can be viewed"
    )
    expect(page.get_by_role("paragraph")).to_contain_text(
        "Our privacy policy can be viewed"
    )
    page.get_by_role("link", name="here").first.click()
    expect(page.locator("h4")).to_contain_text("User Guide")
    page.go_back()
    page.get_by_role("link", name="here").nth(1).click()
    expect(page.locator("h4")).to_contain_text("Privacy Policy")

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


# @pytest.mark.playwright
# def test_load_fhir_v1(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     path = filepath()
#     page.goto(url)

#     login(page)

#     page.get_by_role("button", name=" Import").click()
#     page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
#     page.set_input_files(
#         "#files",
#         os.path.join(path, "tests/test_files/fhir_v1/from/ASP8062_fhir_m11.json"),
#     )
#     page.locator("text = Upload File(s)").last.click()
#     expect(
#         page.get_by_text("Success: Import of 'ASP8062_fhir_m11.json'")
#     ).to_be_visible(timeout=30_000)
#     page.get_by_role("link").first.click()
#     expect(
#         page.get_by_text(
#             "A Phase 1 Randomized, Placebo-controlled Study to Assess the Safety, Tolerability and Pharmacokinetics of Multiple Doses of ASP8062 with a Single Dose of Morphine in Recreational Opioid Using Participants"
#         )
#     ).to_be_visible()

#     context.close()
#     browser.close()


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
    page.get_by_role("link", name="User Guide").click()
    expect(page.locator("h4")).to_contain_text("User Guide")
    page.get_by_role("button", name=" Help").click()
    page.get_by_role("link", name="Privacy Policy").click()
    expect(page.locator("h4")).to_contain_text("Privacy Policy")

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
    expect(page.locator("#navBarMain")).to_contain_text("M11 Protocol")
    expect(page.locator("#navBarMain")).to_contain_text("Version History")

    page.get_by_role("link", name="Safety View").click()
    page.get_by_role("button", name=" Views").click()
    expect(page.locator("#navBarMain")).to_contain_text("Summary View")
    expect(page.locator("#navBarMain")).to_contain_text("Statistics View")
    expect(page.locator("#navBarMain")).to_contain_text("Version History")

    page.get_by_role("link", name="Statistics View").click()
    page.get_by_role("button", name=" Views").click()
    expect(page.locator("#navBarMain")).to_contain_text("Summary View")
    expect(page.locator("#navBarMain")).to_contain_text("Safety View")
    expect(page.locator("#navBarMain")).to_contain_text("Version History")

    page.get_by_role("link", name="Version History").click()
    page.get_by_role("button", name=" Views").click()
    expect(page.locator("#navBarMain")).to_contain_text("Summary View")
    expect(page.locator("#navBarMain")).to_contain_text("Safety View")
    expect(page.locator("#navBarMain")).to_contain_text("Statistics View")

    context.close()
    browser.close()


# @pytest.mark.playwright
# def test_export_import(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     path = filepath()
#     page.goto(url)

#     login(page)

#     page.get_by_role("link", name=f" {display_name()}").click()
#     page.once("dialog", lambda dialog: dialog.accept())
#     page.get_by_role("link", name=" Delete Database").click()
#     page.get_by_role("link", name=" Home").click()

#     page.get_by_role("button", name=" Import").click()
#     page.get_by_role("link", name="M11 Document (.docx)").click()
#     page.set_input_files(
#         "#files", os.path.join(path, "tests/test_files/m11/WA42380/WA42380.docx")
#     )
#     page.locator("text = Upload File(s)").last.click()
#     expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)
#     page.get_by_role("link").first.click()

#     page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
#     _ = download_info.value
#     page.get_by_role("navigation").get_by_role("link").first.click()
#     page.get_by_role("button", name=" Import").click()
#     page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
#     page.set_input_files(
#         "#files",
#         os.path.join(path, "tests/test_files/fhir_v1/from/WA42380_fhir_m11.json"),
#     )
#     page.locator("text = Upload File(s)").last.click()
#     expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=30_000)
#     page.get_by_role("link").first.click()

#     expect(page.locator("#card_1_div")).to_contain_text(
#         "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
#     )
#     expect(page.locator("#card_2_div")).to_contain_text(
#         "A RANDOMIZED, DOUBLE-BLIND, PLACEBO-CONTROLLED, MULTICENTER STUDY TO EVALUATE THE SAFETY AND EFFICACY OF TOCILIZUMAB IN PATIENTS WITH SEVERE COVID 19 PNEUMONIA"
#     )
#     page.locator("#card_2_div").get_by_role("link", name=" View Details").click()
#     expect(page.get_by_role("img", name="alt text")).to_be_visible()
#     page.get_by_role("navigation").get_by_role("link").first.click()
#     page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
#     expect(page.get_by_role("img", name="alt text")).to_be_visible()

#     context.close()
#     browser.close()


@pytest.mark.playwright
def test_selection_menu(playwright: Playwright) -> None:
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
def test_compare_sections(playwright: Playwright) -> None:
    """Section-by-section compare on the multi-study list page.

    Smoke test of the wiring only — we deliberately don't assert on the
    section content (it varies by protocol and the renderer evolves).
    What we pin: the Sections tab activates, its slide-in Table of
    Contents can be opened, and clicking a section entry swaps some
    content into the compare pane (the placeholder table appears)."""
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
    page.locator("#card_1_div").get_by_role("button", name=" Select").click()
    page.locator("#card_2_div").get_by_role("button", name=" Select").click()
    page.get_by_role("button", name=" Selection").click()
    page.get_by_role("button", name=" List selected studies").click()

    # The Sections tab activates when clicked.
    page.get_by_role("tab", name="Sections").click()
    expect(page.locator("#sections_tab")).to_be_visible()

    # Its slide-in Table of Contents can be displayed.
    page.locator("#sections_tab").get_by_role("link", name="Sections").click()
    expect(page.locator("#section_menu")).to_be_visible()

    # Picking a section swaps some content into the compare pane.
    page.locator("#section_toc a.section-link").first.click()
    expect(page.locator("#section_compare table")).to_be_visible()

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


# @pytest.mark.playwright
# def test_fhir_export_madrid_excel(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     path = filepath()
#     page.goto(url)

#     login(page)
#     delete_db(page)

#     load_excel(page, path, "tests/test_files/excel/pilot.xlsx")

#     page.get_by_role("link").first.click()
#     page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
#     download = download_info.value
#     download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Madrid (.").click()
#     download = download_info.value
#     download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Pittsburgh (PRISM 3").click()
#     download = download_info.value
#     download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

#     context.close()
#     browser.close()


# @pytest.mark.playwright
# def test_fhir_export_madrid_word(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     path = filepath()
#     page.goto(url)

#     login(page)
#     delete_db(page)

#     load_m11(page, path, "tests/test_files/m11/LZZT/LZZT.docx")

#     page.get_by_role("link").first.click()
#     page.locator("#card_1_div").get_by_role("link", name=" View Details").click()
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Dallas (PRISM 2) (.").click()
#     download = download_info.value
#     download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Madrid (.").click()
#     download = download_info.value
#     download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")
#     page.get_by_role("button", name=" Export").click()
#     with page.expect_download() as download_info:
#         page.get_by_role("link", name="M11 FHIR, Pittsburgh (PRISM 3").click()
#     download = download_info.value
#     download.save_as(f"tests/test_files/downloads/splash/{download.suggested_filename}")

#     context.close()
#     browser.close()


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
    with page.expect_download():
        page.get_by_role("link", name="Patient Journey: Simple (.").click()
    page.get_by_role("button", name=" Export").click()
    with page.expect_download():
        page.get_by_role("link", name="Patient Journey: Expanded (.").click()

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
def test_import_usdm_with_validation_findings(playwright: Playwright) -> None:
    """USDM v3 / v4 files with rule violations import successfully and
    their findings remain downloadable via the Errors File link.

    USDM rules validation is advisory at import time (see
    ``docs/lessons_learned.md`` lesson 16): findings are persisted to
    the errors file but do not gate the import. This test pins both
    halves of that contract — the success message lands AND the
    persisted findings are still streamed by ``/import/{id}/errors``."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)
    delete_db(page)

    # USDM v3 file with rule failures — used to be rejected, now lands.
    load_usdm(
        page,
        path,
        "tests/test_files/usdm3/errors.json",
        "3",
        "Success: Import of",
    )

    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="Import Status").click()
    with page.expect_download() as download_info:
        page.get_by_role("link", name=" Errors File").click()
    _ = download_info.value
    page.get_by_role("link", name=" Back").click()

    # Same contract for USDM v4 — rule failures, but the import still
    # succeeds and the errors file is still downloadable.
    load_usdm(
        page,
        path,
        "tests/test_files/usdm4/errors.json",
        "4",
        "Success: Import of",
    )

    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="Import Status").click()
    # Two imports in this run (v3 then v4), so the v4 row is the
    # second Errors File link in the status table.
    with page.expect_download() as download_info:
        page.get_by_role("link", name=" Errors File").nth(1).click()
    _ = download_info.value

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
            name="Sponsor: Eli Lilly | Phase: Phase II Trial | Identifier: H2Q-MC-LZZT | Version: 2",
        )
    ).to_be_visible()
    page.get_by_role("link", name=" Back").click()
    page.get_by_role("link", name=" USDM JSON Diff").click()
    expect(
        page.get_by_role(
            "heading",
            name="Sponsor: Eli Lilly | Phase: Phase II Trial | Identifier: H2Q-MC-LZZT | Version: 2",
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


# --- Validate menu ---------------------------------------------------------
#
# Three quick smoke tests for the Validate dropdown. They confirm the menu
# surfaces the three engines, that the CDISC CORE and d4k Engine USDM v4
# routes render their results partial after upload, and that the M11 docx
# route does the same. We deliberately don't assert on specific rule ids
# or finding counts — the engines evolve and this layer is about the menu
# wiring + results rendering, not the rule content. Findings detail is
# already covered by the unit tests under tests/routers/test_validate.py.
#
# Timeouts: USDM rules / M11 docx finish in seconds; CDISC CORE can take
# several minutes on a cold cache (see ``USDM4.validate_core``). The CORE
# test therefore allows a generous timeout.


@pytest.mark.playwright
def test_validate_menu(playwright: Playwright) -> None:
    """The Validate dropdown surfaces all three engines with stable labels."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" Validate").click()
    expect(page.locator("#navBarMain")).to_contain_text(
        "USDM v4 — CDISC Engine (.json)"
    )
    expect(page.locator("#navBarMain")).to_contain_text("USDM v4 — d4k Engine (.json)")
    expect(page.locator("#navBarMain")).to_contain_text("ICH M11 Protocol (.docx)")

    context.close()
    browser.close()


@pytest.mark.playwright
def test_validate_usdm_d4k(playwright: Playwright) -> None:
    """USDM v4 — d4k Engine: pick a clean USDM4 JSON, run validation,
    confirm the results partial renders. We don't pin to specific
    finding content — the engine evolves; what we care about here is
    that the menu link routes correctly and the HTMX swap returns a
    results fragment. The most reliable "swap completed" signal is the
    upload form disappearing (``hx-swap='outerHTML'`` on ``#form_div``
    removes the form unconditionally on a successful response)."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" Validate").click()
    page.get_by_role("link", name="USDM v4 — d4k Engine (.json)").click()
    expect(page.locator("h4")).to_contain_text("Validate USDM JSON")
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/usdm4/no_errors.json")
    )
    page.locator("text = Upload File(s)").last.click()
    # Wait for HTMX to remove ``#form_div`` — that's the swap-completed
    # signal and is independent of finding count or template wording.
    expect(page.locator("#form_div")).to_have_count(0, timeout=180_000)

    context.close()
    browser.close()


@pytest.mark.playwright
def test_validate_usdm_cdisc(playwright: Playwright) -> None:
    """USDM v4 — CDISC Engine: same shape as the d4k test, but
    against the CDISC engine (CORE under the hood — CDISC's only
    engine). CORE downloads JSONata files / schemas / rules / CT
    packages on first run, which can take several minutes on a cold
    cache (subsequent runs hit the persistent cache directory and
    complete much faster). Timeout sized so a warm-cache CI box
    finishes well within budget without a cold run holding the suite
    hostage indefinitely."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" Validate").click()
    page.get_by_role("link", name="USDM v4 — CDISC Engine (.json)").click()
    expect(page.locator("h4")).to_contain_text("Validate USDM JSON")
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/usdm4/no_errors.json")
    )
    page.locator("text = Upload File(s)").last.click()
    expect(page.locator("#form_div")).to_have_count(0, timeout=300_000)

    context.close()
    browser.close()


@pytest.mark.playwright
def test_validate_m11(playwright: Playwright) -> None:
    """ICH M11 Protocol: drive the M11Validator route with a known-good
    sample DOCX. Confirms the picker page loads, the upload reaches the
    validator, and the unified results partial replaces the picker
    card with the rendered findings. The M11 flow now renders the
    same ``validate/partials/results.html`` partial as the CDISC and
    d4k flows (HX-Retarget replaces ``#picker_card``), so the
    swap-completed signal mirrors the d4k test: ``#form_div`` is gone
    once the response lands."""
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" Validate").click()
    page.get_by_role("link", name="ICH M11 Protocol (.docx)").click()
    expect(page.locator("h4")).to_contain_text("Validate M11 Protocol")
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/m11/RadVax/RadVax.docx")
    )
    page.locator("text = Upload File(s)").last.click()
    # ``#form_div`` disappearing is the swap-completed signal — once
    # the HX-Retarget header is honoured the whole ``#picker_card``
    # (and therefore ``#form_div`` inside it) is replaced by the
    # results card. Mirrors the d4k / CDISC playwright tests so the
    # three M11 / d4k / CDISC flows assert on the same signal.
    expect(page.locator("#form_div")).to_have_count(0, timeout=180_000)
    # And the rendered results card carries the uploaded filename in
    # its subtitle ("File: RadVax.docx ...") — proves the response
    # actually contained results, not an error page.
    expect(page.get_by_text("RadVax.docx")).to_be_visible()

    context.close()
    browser.close()


@pytest.mark.playwright
def test_validate_m11_downloads(playwright: Playwright) -> None:
    """Click each of the four findings-download buttons on the M11
    results page and confirm a download fires with the expected
    filename slug.

    Sister to ``test_validate_m11`` — that test stops at the swap-
    completed signal; this one drives the form's hidden-input round-
    trip through to ``/validate/download/{fmt}``.  Covers:

    * the four download buttons (CSV / JSON / Markdown / XLSX) are
      still rendered on the unified ``results.html`` partial after
      the M11 migration;
    * each button's ``formaction`` points at a route that returns
      ``200`` with ``Content-Disposition: attachment`` (otherwise no
      download event fires);
    * the ``kind`` slug (``"m11-findings"``) is correctly threaded
      from the M11 router → results partial's hidden input →
      download route → ``default_filename()``, so the saved name
      matches ``{basename}-m11-findings-{YYYY-MM-DD}.{ext}``.

    M11 is the discriminating case across the three engines because
    its download metadata is the most distinct (slug ``m11-findings``
    vs ``usdm-cdisc-findings`` / ``usdm-d4k-findings``).  The shared
    ``results.html`` template means CDISC and d4k inherit the same
    button wiring; running this once for M11 validates the pipeline
    end-to-end without paying the CDISC cold-cache cost in CI.
    """
    import re
    from datetime import date

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    path = filepath()
    page.goto(url)

    login(page)

    page.get_by_role("button", name=" Validate").click()
    page.get_by_role("link", name="ICH M11 Protocol (.docx)").click()
    page.set_input_files(
        "#files", os.path.join(path, "tests/test_files/m11/RadVax/RadVax.docx")
    )
    page.locator("text = Upload File(s)").last.click()
    # Wait for the results swap before clicking the download buttons —
    # they don't exist on the picker page.
    expect(page.locator("#form_div")).to_have_count(0, timeout=180_000)

    # Mirror the splash / errors-file download tests' on-disk save
    # convention so a maintainer can eyeball what each format
    # actually produces.  ``exist_ok=True`` because the directory may
    # not exist on a fresh checkout.
    download_dir = "tests/test_files/downloads/m11_findings"
    os.makedirs(download_dir, exist_ok=True)

    today = date.today().isoformat()
    expected = re.compile(rf"^RadVax-m11-findings-{today}\.(csv|json|md|xlsx)$")

    # ``button`` text mirrors the labels rendered in
    # ``validate/partials/results.html`` (next to the bi-filetype-*
    # icons).  Each button submits the same form to its own
    # ``formaction``, so iterating like this exercises one route per
    # iteration without re-running the validation.
    for label in ("CSV", "JSON", "Markdown", "XLSX"):
        with page.expect_download() as download_info:
            page.get_by_role("button", name=label).click()
        download = download_info.value
        assert expected.match(download.suggested_filename), (
            f"{label} download had unexpected filename: "
            f"{download.suggested_filename!r} (expected match for {expected.pattern})"
        )
        download.save_as(os.path.join(download_dir, download.suggested_filename))

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
    load_fhir(page, path, "tests/test_files/fhir_v3/from/IGBJ_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/WA42380_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/ASP8062_fhir_m11.json")
    load_fhir(page, path, "tests/test_files/fhir_v3/from/DEUCRALIP_fhir_m11.json")
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
    expect(page.locator("li").filter(has_text="Phase I Trial")).to_be_visible()
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


# # Expects data from previous test
# @pytest.mark.playwright
# def test_m11_specification(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto(url)

#     login(page)

#     page.get_by_role("button", name=" ICH M11").click()
#     page.get_by_role("link", name="M11 Specification").click()
#     page.get_by_role("link", name="Sponsor Confidentiality").click()
#     page.locator("#specification-card div").filter(
#         has_text="Template Specification Long"
#     ).locator("i").click()
#     expect(page.locator("#data-div")).to_contain_text(
#         "M11 Specification: Sponsor Confidentiality Statement"
#     )
#     expect(page.locator("#template-div")).to_contain_text(
#         "Enter Sponsor Confidentiality Statement"
#     )
#     page.locator("#specification-card i").nth(1).click()
#     expect(page.locator("#technical-div")).to_contain_text(
#         "Sponsor Confidentiality Statement"
#     )
#     page.locator("#specification-card div").filter(
#         has_text="USDM Mapping Name Sponsor"
#     ).locator("i").click()
#     expect(page.locator("#usdm-div")).to_contain_text(
#         "Sponsor Confidentiality Statement"
#     )
#     page.locator("#specification-card div").filter(
#         has_text="FHIR M11 Mapping Resource"
#     ).locator("i").click()
#     expect(page.locator("#fhir-div")).to_contain_text(
#         "ResearchStudy.extension[confidentialityStatement]"
#     )

#     context.close()
#     browser.close()


# Display name used when (self-)registering a test user. The nav shows
# this, so delete_db() and similar look it up via display_name().
TEST_DISPLAY_NAME = "Test User"


def d4k_email():
    """A @data4knowledge.dk address — auto-gets Admin + Transmit."""
    return os.environ["TEST_D4K_EMAIL"]


def non_d4k_email():
    """A non-d4k address — registers with no roles (for role tests)."""
    return os.environ["TEST_NON_D4K_EMAIL"]


def dev_code():
    """The fixed login code the dev-mode server issues (DEV_LOGIN_CODE)."""
    return os.environ["DEV_LOGIN_CODE"]


def display_name():
    return TEST_DISPLAY_NAME


def filepath():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def login(page, email=None, name=None):
    """Log in via the email-code flow.

    Uses /register so it self-provisions on a fresh database (registration
    is idempotent for an existing email). Defaults to the d4k address,
    which carries full rights. Pass non_d4k_email() to test a roleless user.
    Requires the server to run in dev mode with DEV_LOGIN_CODE set.
    """
    email = email or d4k_email()
    name = name or TEST_DISPLAY_NAME
    page.goto(f"{url}/register")
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Display name").click()
    page.get_by_label("Display name").fill(name)
    page.get_by_role("button", name="Register").click()
    page.get_by_label("Login code").click()
    page.get_by_label("Login code").fill(dev_code())
    page.get_by_role("button", name="Sign in").click()
    # A successful sign-in redirects to /index. If it doesn't, the server
    # is almost certainly not issuing the fixed DEV_LOGIN_CODE — fail fast
    # with guidance instead of letting later steps hang on a missing page.
    try:
        page.wait_for_url("**/index", timeout=10_000)
    except Exception:
        raise AssertionError(
            "Login did not complete (still on the verify page). Start the "
            "server with ./playwright_server.sh so it runs in dev mode with "
            "DEV_LOGIN_CODE=123456 — dev_server.sh emails a real random code "
            "and rejects the test code."
        )


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
    expect(page.get_by_text("Success: Import of")).to_be_visible(timeout=120_000)


def load_fhir(page, root_path, filepath):
    page.get_by_role("link").first.click()
    page.get_by_role("button", name=" Import").click()
    page.get_by_role("link", name="M11 FHIR, IG (PRISM 3)").click()
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
