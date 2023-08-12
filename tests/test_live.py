# import pytest
# from playwright.async_api import Page, expect
# from pytest_django.live_server_helper import LiveServer

# def test_homepage_has_Playwright_in_title_and_get_started_link_linking_to_the_intro_page(page: Page):
#     page.goto("https://playwright.dev/")

#     # Expect a title "to contain" a substring.
#     expect(page).to_have_title(re.compile("Playwright"))

#     # create a locator
#     get_started = page.get_by_role("link", name="Get started")

#     # Expect an attribute "to be strictly equal" to the value.
#     expect(get_started).to_have_attribute("href", "/docs/intro")

#     # Click the get started link.
#     get_started.click()

#     # Expects the URL to contain intro.
#     expect(page).to_have_url(re.compile(".*intro"))


# @pytest.mark.asyncio
# async def test_dispatch_raises_exception_when_not_in_debug_mode(page: Page, live_server: LiveServer):
#     await page.goto(live_server.url + "/app")

#     expect(page).to_have_title("pre_body_/app")
#     expect(page).to_have_title("post_body_/app")

#     btn_goto_2 = page.get_by_role("link", name="/app/second")
#     expect(btn_goto_2).to_have_attribute("href", "/app/second")

#     btn_goto_2.click()

#     expect()
