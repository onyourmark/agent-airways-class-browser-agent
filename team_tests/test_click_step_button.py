"""
Tests for the click_step_button tool (Team 03).

Run from the MAIN project folder (not inside team_tests):
    python3 -m team_tests.test_click_step_button

What happens:
  * The TEST (not the tool) uses Playwright to get to each screen:
    it chooses the airports, picks a flight, picks a seat, and fills in
    the passenger form. The tool only clicks.
  * Then the test calls the tool: click_step_button.run(page, argument, context)
  * After every call, the test looks at the REAL page itself, so we do not
    just trust what the tool says about itself.
  * All four approved buttons are tested end to end, plus a failure case
    and a safety case.
"""

import sys
import browser_tools
from team_tools import click_step_button

results = []   # list of (test name, passed?)


def record(name, passed):
    """Save and print one PASS/FAIL line."""
    results.append((name, passed))
    if passed:
        print("   PASS:", name)
    else:
        print("   FAIL:", name)


def is_valid(argument):
    """Ask the tool's validate(). It may return True/False or (True/False, reason)."""
    answer = click_step_button.validate(argument)
    if isinstance(answer, tuple):
        return answer[0]
    return answer


# ---------------------------------------------------------------------------
# Part A: argument checks (no browser needed)
# ---------------------------------------------------------------------------
print("=== PART A: validate() rejects bad arguments ===")

argument = {"button": "search_flights"}
print("validate(", argument, ")")
record("validate accepts search_flights", is_valid(argument) is True)

argument = {"button": "confirm_reservation"}
print("validate(", argument, ")")
record("validate REJECTS confirm_reservation", is_valid(argument) is False)

argument = {"button": "launch_rocket"}
print("validate(", argument, ")")
record("validate rejects an unknown button", is_valid(argument) is False)

argument = {}
print("validate(", argument, ")")
record("validate rejects a missing 'button'", is_valid(argument) is False)

# ---------------------------------------------------------------------------
# Part B: browser tests
# ---------------------------------------------------------------------------
browser_tools.start_browser()
try:
    browser_tools.open_site()
    page = browser_tools.page
    context = {}   # this tool does not need trusted context

    # ===== TEST 1: SUCCESS - click Search flights =========================
    print("\n=== TEST 1 (success): search_flights ===")

    # Setup done by the TEST, not the tool: choose From and To.
    page.select_option("#fromAirport", "DCA")
    page.select_option("#toAirport", "BOS")

    call = {"button": "search_flights"}
    print("Tool call:", call)
    result = click_step_button.run(page, call, context)
    print("Tool returned:", result)

    # Independent check: look at the real page ourselves.
    results_visible = page.locator("#resultsStage").is_visible()
    print("Browser evidence: #resultsStage visible =", results_visible)
    print("Browser evidence: URL =", page.url)

    record("search_flights: tool says ok", result["ok"] is True)
    record("search_flights: #resultsStage is really visible", results_visible)

    # ===== TEST 2: SUCCESS - close the flight details popup ===============
    print("\n=== TEST 2 (success): close_details ===")

    # Setup done by the TEST: wait for the flight list (about 1.2 seconds),
    # then open the details popup of the first flight.
    page.wait_for_selector("button.details")
    page.locator("button.details").first.click()
    page.wait_for_selector("#flightDialog", state="visible")
    print("Setup: #flightDialog visible =", page.locator("#flightDialog").is_visible())

    call = {"button": "close_details"}
    print("Tool call:", call)
    result = click_step_button.run(page, call, context)
    print("Tool returned:", result)

    # Independent check: the popup must really be closed.
    dialog_visible = page.locator("#flightDialog").is_visible()
    print("Browser evidence: #flightDialog visible =", dialog_visible)

    record("close_details: tool says ok", result["ok"] is True)
    record("close_details: #flightDialog is really closed", dialog_visible is False)

    # ===== TEST 3: FAILURE - Continue before choosing a seat ==============
    print("\n=== TEST 3 (failure): continue_from_seat with NO seat chosen ===")

    # Setup done by the TEST: choose the first flight so the seat screen appears.
    page.locator("button.choose").first.click()
    page.wait_for_selector("#seatStage", state="visible")

    call = {"button": "continue_from_seat"}
    print("Tool call:", call)
    result = click_step_button.run(page, call, context)
    print("Tool returned:", result)

    # Independent check: we must still be on the seat screen.
    seat_visible = page.locator("#seatStage").is_visible()
    passenger_visible = page.locator("#passengerStage").is_visible()
    print("Browser evidence: #seatStage visible =", seat_visible)
    print("Browser evidence: #passengerStage visible =", passenger_visible)

    # The tool should report that it did not click.
    clicked = result["data"].get("clicked")
    print("Tool says clicked =", clicked)

    record("continue_from_seat: tool reports ok = False", result["ok"] is False)
    record("continue_from_seat: tool reports clicked = False", clicked is False)
    record("continue_from_seat: #seatStage is still visible", seat_visible)
    record("continue_from_seat: #passengerStage is still hidden",
           passenger_visible is False)

    # ===== TEST 4: SAFETY - confirm_reservation must be refused ===========
    print("\n=== TEST 4 (safety): confirm_reservation is refused ===")
    call = {"button": "confirm_reservation"}
    print("Tool call:", call)
    result = click_step_button.run(page, call, context)
    print("Tool returned:", result)
    print("Tool says clicked =", result["data"].get("clicked"))

    # Independent check: the page must not have moved at all.
    review_visible = page.locator("#reviewStage").is_visible()
    seat_still_visible = page.locator("#seatStage").is_visible()
    print("Browser evidence: #reviewStage visible =", review_visible)
    print("Browser evidence: #seatStage still visible =", seat_still_visible)

    record("confirm_reservation: tool reports ok = False", result["ok"] is False)
    record("confirm_reservation: nothing clicked, still not on review",
           review_visible is False)
    record("confirm_reservation: page did not move (still on seat screen)",
           seat_still_visible)

    # ===== TEST 5: SUCCESS - continue_from_seat, then continue_to_review ==
    print("\n=== TEST 5 (success): continue_from_seat and continue_to_review ===")

    # Setup done by the TEST: pick the first available seat.
    page.locator("#seatMap button.seat:not(.unavailable)").first.click()
    print("Setup: chose a seat. Continue enabled =",
          page.locator("#continueFromSeat").is_enabled())

    call = {"button": "continue_from_seat"}
    print("Tool call:", call)
    result = click_step_button.run(page, call, context)
    print("Tool returned:", result)

    # Independent check: the passenger screen must really be showing now.
    passenger_visible = page.locator("#passengerStage").is_visible()
    print("Browser evidence: #passengerStage visible =", passenger_visible)

    record("continue_from_seat (seat chosen): tool says ok", result["ok"] is True)
    record("continue_from_seat (seat chosen): #passengerStage is really visible",
           passenger_visible)

    # Setup done by the TEST: fill in the passenger form with the class sample values.
    page.fill("#passengerName", "Alex Student")
    page.fill("#passengerEmail", "alex@example.com")

    call = {"button": "continue_to_review"}
    print("Tool call:", call)
    result = click_step_button.run(page, call, context)
    print("Tool returned:", result)

    # Independent check: the review screen must really be showing,
    # and the reservation must NOT have been confirmed.
    review_visible = page.locator("#reviewStage").is_visible()
    confirmation_visible = page.locator("#confirmationStage").is_visible()
    print("Browser evidence: #reviewStage visible =", review_visible)
    print("Browser evidence: #confirmationStage visible =", confirmation_visible)

    record("continue_to_review: tool says ok", result["ok"] is True)
    record("continue_to_review: #reviewStage is really visible", review_visible)
    record("continue_to_review: reservation was NOT confirmed",
           confirmation_visible is False)

finally:
    browser_tools.close_browser()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n=== SUMMARY ===")
failed = 0
for name, passed in results:
    if passed:
        print("PASS ", name)
    else:
        print("FAIL ", name)
        failed = failed + 1
print(str(len(results) - failed) + " passed, " + str(failed) + " failed")

if failed > 0:
    sys.exit(1)