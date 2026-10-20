"""Team 07 Test Suite for show_flight_details.

Demonstrates:
1. Normal success case: Open details for AA101, compare extracted facts against
   actual page values, verify dialog closes, and confirm flight is not selected.
2. Failure test: Request non-existent flight AA999, verify refusal and unchanged page state.
3. Edge case: Request partial ID AA2 (part of AA205), verify refusal and that no dialog opened.
4. Independent browser checks using Playwright selectors.
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

            # 2. Compare returned details with actual page DOM elements and card text
            actual_dialog_title = page.locator("#dialogTitle").text_content().strip()
            actual_dialog_body = page.locator("#dialogBody").text_content().strip()
            card_text = page.locator(".flight-card[data-flight-id='AA101']").inner_text()

            assert result_success["data"]["dialog_title"] == actual_dialog_title, "Returned title must match actual #dialogTitle"
            assert result_success["data"]["dialog_title"] == "AA101 details", "Dialog title must be 'AA101 details'"
            assert result_success["data"]["details"] == actual_dialog_body, "Returned details must match actual #dialogBody"
            assert result_success["data"]["route"] == "DCA to BOS", "Route must match 'DCA to BOS'"
            assert result_success["data"]["time"] == "8:10 AM to 9:35 AM", "Time must match '8:10 AM to 9:35 AM'"
            assert result_success["data"]["stops"] == "Nonstop", "Stops must match 'Nonstop'"
            assert result_success["data"]["price"] == "$129 per passenger.", "Price must match '$129 per passenger.'"
            assert "AA101" in card_text and "$129" in card_text, "Extracted info must match visible AA101 flight card"

            # 3. Dialog must be closed in actual DOM
            dialog_visible = page.locator("#flightDialog").is_visible()
            assert not dialog_visible, "Independent check: #flightDialog must be hidden"

            # 4. Flight should NOT have been selected (results stage must remain active)
            results_visible = page.locator("#resultsStage").is_visible()
            seat_visible = page.locator("#seatStage").is_visible()
            assert results_visible and not seat_visible, "Independent check: page must stay on results without selecting flight"

            print("INDEPENDENT CHECK: #dialogTitle & #dialogBody match actual page values: True")
            print("INDEPENDENT CHECK: #flightDialog is hidden:", not dialog_visible)
            print("INDEPENDENT CHECK: still on results, no flight chosen:", results_visible and not seat_visible)
            print("PASS: Test 1 succeeded with verified dialog closure, exact data match, and unchanged stage.")

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
            results_visible_fail = page.locator("#resultsStage").is_visible()
            seat_visible_fail = page.locator("#seatStage").is_visible()
            assert results_visible_fail and not seat_visible_fail, "Independent check: page must stay on results"
            print("INDEPENDENT CHECK: #flightDialog remains closed:", not dialog_visible_fail)
            print("INDEPENDENT CHECK: still on results, no flight chosen:", results_visible_fail and not seat_visible_fail)
            print("PASS: Test 2 safely rejected non-existent flight ID AA999.")

            # -------------------------------------------------------------
            # TEST 3: EDGE CASE (AA2 - only part of the real ID AA205)
            # -------------------------------------------------------------
            print("\n--- TEST 3: EDGE CASE (Partial Flight ID: AA2) ---")
            arg_partial = {"flight_id": "AA2"}

            # Remember the dialog title before the call. Opening any flight's
            # details changes it (for example to "AA205 details"), and the new
            # title stays on the page even after the dialog closes.
            title_before = page.locator("#dialogTitle").text_content()

            # Step 1: Validate argument (format is valid, but no card has this exact ID)
            val_ok, val_note = show_flight_details.validate(arg_partial)
            print("Validation Check:", val_ok, "-", val_note)

            # Step 2: Execute the tool
            result_partial = show_flight_details.run(page, arg_partial, context={})
            print("Tool Return OK:", result_partial["ok"])
            print("Tool Return Message:", result_partial["message"])

            # Step 3: Independent browser checks
            # 1. Tool must report ok == False
            assert result_partial["ok"] is False, "Tool should refuse the partial ID AA2"
            # 2. No flight's details were opened, not even briefly
            title_after = page.locator("#dialogTitle").text_content()
            assert title_after == title_before, "Independent check: no details dialog should have opened"
            # 3. Dialog is closed and the page is still on the results stage
            dialog_visible_partial = page.locator("#flightDialog").is_visible()
            assert not dialog_visible_partial, "Independent check: #flightDialog must remain closed"
            results_visible = page.locator("#resultsStage").is_visible()
            seat_visible = page.locator("#seatStage").is_visible()
            assert results_visible and not seat_visible, "Independent check: page must stay on results"
            print("INDEPENDENT CHECK: dialog title unchanged ('" + title_after + "'):", title_after == title_before)
            print("INDEPENDENT CHECK: #flightDialog remains closed:", not dialog_visible_partial)
            print("INDEPENDENT CHECK: still on results, no flight chosen:", results_visible and not seat_visible)
            print("PASS: Test 3 refused partial flight ID AA2.")

            print("\n" + "=" * 65)
            print("ALL TESTS PASSED SUCCESSFULLY (3/3)")
            print("=" * 65)

        finally:
            browser.close()


if __name__ == "__main__":
    run_tests()