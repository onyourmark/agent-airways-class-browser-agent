"""Team 14 tests for team_tools/verify_confirmation.py.

Run from the repository folder:
    python team_tools/test_verify_confirmation.py
(on some Macs: python3 ...; with uv: uv run --no-project python ...)

A visible Chromium window opens and Playwright completes the pretend booking.
The setup clicks are NOT the tool being tested. The tool only reads the page.

Each test prints the tool call, the dictionary the tool returned, what the
browser actually shows (read separately by this test), and PASS or FAIL.
"""

import json
import os
import sys

# This file lives in team_tools/, but browser_tools.py is one folder up.
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
REPO_FOLDER = os.path.dirname(THIS_FOLDER)
sys.path.insert(0, REPO_FOLDER)
sys.path.insert(0, THIS_FOLDER)

import browser_tools
import verify_confirmation


# The pretend trip that the setup code books in the browser.
# Mock total: AA101 costs $129, plus $35 for one checked bag = $164.
TRIP = {
    "from": "DCA",
    "to": "BOS",
    "date": "2026-11-20",
    "flight": "AA101",
    "seat": "1A",
    "name": "Alex Student",
    "email": "alex@example.com",
    "checked_bag": True,
    "priority_boarding": False,
}


def make_goal():
    """Build the trusted goal that Python (not the model) gives the tool."""
    return {
        "route": TRIP["from"] + " → " + TRIP["to"],
        "date": TRIP["date"],
        "flight": TRIP["flight"],
        "seat": TRIP["seat"],
        "name": TRIP["name"],
        "email": TRIP["email"],
        "checked_bag": "Yes",
        "priority_boarding": "No",
        "mock_total": "$164",
    }


def show(title, value):
    """Print one labelled piece of evidence."""
    print("  " + title + ":")
    print("    " + json.dumps(value, indent=2, ensure_ascii=False).replace("\n", "\n    "))


def read_browser_evidence(page):
    """Read the confirmation screen directly, without using the tool.

    This is the independent check: it uses its own Playwright reads, so a
    bug inside the tool cannot make the test agree with it by accident.
    """
    stage = page.locator("#confirmationStage")
    evidence = {
        "url": page.url,
        "confirmation_visible": stage.is_visible(),
        "heading": "",
        "code": "",
        "details_text": "",
    }
    if evidence["confirmation_visible"]:
        evidence["heading"] = stage.locator("h2").inner_text().strip()
        evidence["code"] = page.locator("#confirmationCode").inner_text().strip()
        evidence["details_text"] = page.locator("#confirmationDetails").inner_text()
    return evidence


def book_pretend_trip(page):
    """Setup only: use plain Playwright to reach the confirmation screen."""
    # 1. Search.
    page.select_option("#fromAirport", TRIP["from"])
    page.select_option("#toAirport", TRIP["to"])
    page.fill("#departureDate", TRIP["date"])
    page.click("#searchFlights")

    # 2. Choose the flight (the cards appear after a short loading delay).
    page.click("button.choose[data-flight='" + TRIP["flight"] + "']")

    # 3. Choose the seat and continue.
    page.click("button.seat[data-seat='" + TRIP["seat"] + "']")
    page.click("#continueFromSeat")

    # 4. Passenger details and optional extras.
    page.fill("#passengerName", TRIP["name"])
    page.fill("#passengerEmail", TRIP["email"])
    page.set_checked("#checkedBag", TRIP["checked_bag"])
    page.set_checked("#priorityBoarding", TRIP["priority_boarding"])
    page.click("#continueToReview")

    # 5. Review: tick the website's own checkbox, then confirm.
    page.check("#confirmDetails")
    page.click("#confirmReservation")
    page.locator("#confirmationStage").wait_for(state="visible")


# ---------------------------------------------------------------------------
# Tests. Each returns True (PASS) or False (FAIL) and prints its evidence.
# ---------------------------------------------------------------------------

def test_validate_rejects_bad_arguments():
    """Edge case: only an empty dictionary is a valid argument."""
    print("\nTEST 1: validate() accepts {} and rejects anything else")
    cases = [
        ({}, True),
        ({"status": "confirmed"}, False),  # model trying to claim success
        ("done", False),                    # not a dictionary
        (None, False),
    ]
    all_passed = True
    for argument, expected_valid in cases:
        valid, reason = verify_confirmation.validate(argument)
        print("  CALL: validate(" + repr(argument) + ") -> " + repr((valid, reason)))
        if valid != expected_valid:
            print("    expected valid =", expected_valid)
            all_passed = False
    return all_passed


def test_matching_goal_passes(page):
    """Successful case: the goal matches the trip that was really booked."""
    print("\nTEST 2: run() with a goal matching the booked trip")
    goal = make_goal()
    result = verify_confirmation.run(page, {}, {"goal": goal})
    evidence = read_browser_evidence(page)
    print("  CALL: run(page, {}, {'goal': <matching goal>})")
    show("RETURNED", result)
    show("BROWSER", evidence)

    # Independent check of the real page, not of the tool's dictionary.
    page_ok = evidence["confirmation_visible"]
    if evidence["heading"] != "RESERVATION CONFIRMED":
        page_ok = False
    if evidence["code"] == "":
        page_ok = False
    for field in goal:
        if goal[field] not in evidence["details_text"]:
            print("    page does not show expected", field, "=", goal[field])
            page_ok = False

    # The tool should agree with the page, and every single check must pass.
    every_check_passed = True
    for name in result["data"]["checks"]:
        if result["data"]["checks"][name]["passed"] is not True:
            every_check_passed = False

    return page_ok and result["ok"] is True and every_check_passed


def test_wrong_email_fails(page):
    """Failure case: the page says confirmed, but the email is not the goal's."""
    print("\nTEST 3: run() with a wrong expected email must return ok=False")
    goal = make_goal()
    goal["email"] = "wrong@example.com"
    result = verify_confirmation.run(page, {}, {"goal": goal})
    evidence = read_browser_evidence(page)
    print("  CALL: run(page, {}, {'goal': <goal with email='wrong@example.com'>})")
    show("RETURNED", result)
    show("BROWSER", evidence)

    # The website really does say the reservation is confirmed...
    page_says_confirmed = evidence["heading"] == "RESERVATION CONFIRMED"
    # ...and the email it shows is the real one, not the wrong one.
    page_shows_real_email = TRIP["email"] in evidence["details_text"]
    page_shows_wrong_email = "wrong@example.com" in evidence["details_text"]

    # The tool must still fail, and it must blame the email check only.
    email_check = result["data"]["checks"].get("email", {})
    other_checks_passed = True
    for name in result["data"]["checks"]:
        if name != "email" and result["data"]["checks"][name]["passed"] is not True:
            other_checks_passed = False

    return (
        page_says_confirmed
        and page_shows_real_email
        and not page_shows_wrong_email
        and result["ok"] is False
        and email_check.get("passed") is False
        and other_checks_passed
    )


def record(results, name, passed):
    """Remember one test result and print PASS or FAIL."""
    results.append((name, passed))
    if passed:
        print("  PASS:", name)
    else:
        print("  FAIL:", name)


def main():
    results = []

    # Test 1 needs no browser.
    record(results, "validate accepts only {}", test_validate_rejects_bad_arguments())

    browser_tools.start_browser()
    try:
        page = browser_tools.page
        browser_tools.open_site()

        print("\nSETUP: booking the pretend trip with plain Playwright...")
        book_pretend_trip(page)
        print("  confirmation screen visible:", page.locator("#confirmationStage").is_visible())

        # Tests 2 and 3 run on the real confirmation screen.
        record(results, "matching goal passes", test_matching_goal_passes(page))
        record(results, "wrong email fails", test_wrong_email_fails(page))
    finally:
        browser_tools.close_browser()

    print("\nSUMMARY")
    failures = 0
    for name, passed in results:
        if passed:
            print("  PASS:", name)
        else:
            print("  FAIL:", name)
            failures = failures + 1

    if failures > 0:
        print(str(failures) + " test(s) failed.")
        sys.exit(1)
    print("All " + str(len(results)) + " Team 14 tests passed.")


if __name__ == "__main__":
    main()
