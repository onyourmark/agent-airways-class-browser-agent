
import browser_tools

from team_tools.wait_for_flight_results import validate, run


def main():
    # Start the browser using the class starter.
    browser_tools.start_browser()

    try:
        browser_tools.open_site()
        page = browser_tools.page
        print("Actual browser URL:", repr(page.url))
        print("Expected URL:", repr(browser_tools.SITE_URL))

        print("\n=== TEST 1: Timeout without searching ===")

        # The search page has no flight results yet.
        result = run(page, {"timeout_seconds": 1}, {})
        print("Tool returned:", result)

        # Independently inspect the actual page.
        actual_count = page.locator(".flight-card:visible").count()
        print("Actual visible cards:", actual_count)

        assert result["ok"] is False
        assert "Timed out" in result["message"]
        assert actual_count == 0
        assert result["data"]["visible_flight_count"] == actual_count

        print("PASS: Timeout correctly reported.")
        page.screenshot(path="team_tests/team06_failure.png")

        print("\n=== TEST 2: Invalid timeout ===")

        valid, reason = validate({"timeout_seconds": 20})
        print("Validation:", valid, reason)

        assert valid is False

        # Confirm that run also rejects the input.
        result = run(page, {"timeout_seconds": 20}, {})
        assert result["ok"] is False

        print("PASS: Invalid timeout rejected.")

        print("\n=== TEST 3: Successful flight results ===")

        print("Use the opened Chromium browser to prepare a flight search.")
        print("Select From, To, Passengers, and a future date.")
        print("Do not click Search flights yet.")

        input("Return here and press Enter when the form is ready...")

        # Independently verify the test begins without results.
        assert page.locator(".flight-card:visible").count() == 0

        # Clicking Search is only test setup.
        # Our assigned tool itself never searches or clicks.
        page.locator("#searchFlights").click()

        # Call Team 06's tool right after searching.
        result = run(page, {"timeout_seconds": 5}, {})
        print("Tool returned:", result)

        # Independent verification using Playwright.
        actual_count = page.locator(".flight-card:visible").count()

        print("Actual visible cards:", actual_count)

        assert result["ok"] is True
        assert actual_count > 0
        assert result["data"]["visible_flight_count"] == actual_count

        print("PASS: Flight results independently verified.")
        page.screenshot(path="team_tests/team06_success.png")

        print("\nALL TEAM 06 TESTS PASSED!")

    finally:
        browser_tools.close_browser()


if __name__ == "__main__":
    main()
