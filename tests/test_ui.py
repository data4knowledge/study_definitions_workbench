import re
from playwright.sync_api import Page, expect

def test_splash(page: Page):
    page.goto("https://d4k-sdw.fly.dev")
    expect(page).to_have_title(re.compile("d4k Protocl to USDM Tool"))

# def test_get_started_link(page: Page):
#     page.goto("https://playwright.dev/")
#     # Click the get started link.
#     page.get_by_role("link", name="Get started").click()
#     # Expects page to have a heading with the name of Installation.
#     expect(page.get_by_role("heading", name="Installation")).to_be_visible()