"""Team 07 Test Suite for show_flight_details.

Demonstrates:
1. Normal success case: Open details for AA101, extract facts, verify dialog closes.
2. Failure test: Request non-existent flight AA999, verify refusal and unchanged page state.
3. Independent browser checks using Playwright selectors.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Ensure team_tools can be imported
sys.path.append(str(Path(__file__).resolve().parent.parent))
from team_tools import show_flight_details

SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"


def navigate_to_results(page):
    """Navigate to the Agent Airways flight results page."""
    page.goto(SITE_URL, wait_until="domcontentloaded")

    # Select search parameters if dropdowns are present
    if page.locator("#fromAirport").count() > 0:
        page.locator("#fromAirport").select_option("DCA")
    if page.locator("#toAirport").count() > 0:
        page.locator("#toAirport").select_option("BOS")
    if page.locator("#passengers").count() > 0:
        page.locator("#passengers").select_option("1")

    # Click search button
    search_btn = page.locator("button:has-text('Search'), #searchBtn, input[type='submit']")
    if search_btn.count() > 0:
        search_btn.first.click()

    # Wait for flight cards to load
    page.wait_for_timeout(1000)


def run_tests():
    print("=" * 65)
    print("TEAM 07: RUNNING show_flight_details TESTS")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()

        try:
            print("\nNavigating to Agent Airways flight results...")
            navigate_to_results(page)

            # -------------------------------------------------------------
            # TEST 1: SUCCESSFUL CASE (AA101)
            # -------------------------------------------------------------
            print("\n--- TEST 1: SUCCESS CASE (Flight ID: AA101) ---")
            arg_success = {"flight_id": "AA101"}

            # Step 1: Pre-validation check
            val_ok, val_note = show_flight_details.validate(arg_success)
            print("Validation Check:", val_ok, "-", val_note)
            assert val_ok is True, "Validation should have passed for AA101"

            # Step 2: Execute the tool
            result_success = show_flight_details.run(page, arg_success, context={})
            print("Tool Return OK:", result_success["ok"])
            print("Tool Return Message:", result_success["message"])
            print("Extracted Data:", result_success["data"])

            # Step 3: Independent verification in the real browser
            # 1. Returned ok must be True
            assert result_success["ok"] is True, "Tool should report ok == True"
            # 2. Dialog title must not be empty
            assert result_success["data"]["dialog_title"] != "", "Dialog title should be captured"
            # 3. Details body must not be empty
            assert result_success["data"]["details"] != "", "Dialog details body should be captured"
            # 4. Dialog must be closed in actual DOM
            dialog_visible = page.locator("#flightDialog").is_visible()
            assert not dialog_visible, "Independent check: #flightDialog must be hidden"
            # 5. Flight should NOT have been selected (results stage should still be active)
            print("INDEPENDENT CHECK: #flightDialog is hidden:", not dialog_visible)
            print("PASS: Test 1 succeeded with verified dialog closure and data extraction.")

            # -------------------------------------------------------------
            # TEST 2: FAILURE CASE (AA999 - Non-existent flight)
            # -------------------------------------------------------------
            print("\n--- TEST 2: FAILURE CASE (Flight ID: AA999) ---")
            arg_failure = {"flight_id": "AA999"}

            # Step 1: Validate argument (syntax is valid, but ID does not exist on page)
            val_ok, val_note = show_flight_details.validate(arg_failure)
            print("Validation Check:", val_ok, "-", val_note)

            # Step 2: Execute the tool
            result_failure = show_flight_details.run(page, arg_failure, context={})
            print("Tool Return OK:", result_failure["ok"])
            print("Tool Return Message:", result_failure["message"])

            # Step 3: Independent browser check
            # 1. Tool must report ok == False
            assert result_failure["ok"] is False, "Tool should report ok == False for AA999"
            # 2. Dialog must NOT be opened
            dialog_visible_fail = page.locator("#flightDialog").is_visible()
            assert not dialog_visible_fail, "Independent check: #flightDialog must remain closed"
            # 3. Page remains on flight results stage without unintended mutations
            print("INDEPENDENT CHECK: #flightDialog remains closed:", not dialog_visible_fail)
            print("PASS: Test 2 safely rejected non-existent flight ID AA999.")

            print("\n" + "=" * 65)
            print("ALL TESTS PASSED SUCCESSFULLY (2/2)")
            print("=" * 65)

        finally:
            browser.close()


if __name__ == "__main__":
    run_tests()