from playwright.sync_api import sync_playwright
from team_tools.list_flights import run, validate

SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"


def failure_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SITE_URL)

        result = run(page, {}, {})

        print("Failure test:", result)
        assert result["ok"] is False

        browser.close()


def success_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SITE_URL)

        page.locator("#fromAirport").select_option("DCA")
        page.locator("#toAirport").select_option("BOS")
        page.locator("#departureDate").fill("2026-11-15")
        page.locator("#searchFlights").click()

        page.locator(".flight-card").first.wait_for()

        result = run(page, {}, {})

        # Independent browser check
        actual_id = page.locator(".flight-card").first.get_attribute("data-flight-id")

        print("Success test:", result)
        assert result["ok"] is True
        assert result["data"]["flights"][0]["flight_id"] == actual_id

        browser.close()


def invalid_input_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SITE_URL)

        result = run(page, {"flight_id": "AA101"}, {})

        print("Invalid input test:", result)

        assert result["ok"] is False
        assert result["message"] == "Use an empty dictionary: {}"

        browser.close()


failure_test()
success_test()
invalid_input_test()

print("All Team 05 tests passed.")