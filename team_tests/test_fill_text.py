"""Team 01 live browser tests for team_tools/fill_text.py.

Needs the Internet and Chromium, so it is separate from the offline tests.py.

Run from the repository folder:
    python3 team_tests/test_fill_text.py            # pause; you click to the passenger page
    python3 team_tests/test_fill_text.py --auto     # Playwright clicks there itself
    python3 team_tests/test_fill_text.py --auto --headless   # no visible window

Each test prints the tool call, validate()/run() results, an independent
browser read-back, and PASS/FAIL. Log: team_tests/fill_text_test_output.txt
Screenshots: team_tests/evidence/
"""

import os
import sys

from playwright.sync_api import sync_playwright

# Let Python find the team_tools folder, which sits one level above this file.
TEST_FOLDER = os.path.dirname(os.path.abspath(__file__))
REPO_FOLDER = os.path.dirname(TEST_FOLDER)
sys.path.insert(0, REPO_FOLDER)

from team_tools import fill_text  # noqa: E402  (import after the path fix)

SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"
LOG_FILE = os.path.join(TEST_FOLDER, "fill_text_test_output.txt")
EVIDENCE_FOLDER = os.path.join(TEST_FOLDER, "evidence")

# Fake test data only. No real personal information.
TEST_DATE = "2026-12-15"
TEST_NAME = "Alex Student"
TEST_EMAIL = "alex@example.com"

# The page IDs the tool should write into. The test reads these itself.
FIELD_IDS = {
    "departure_date": "#departureDate",
    "full_name": "#passengerName",
    "email": "#passengerEmail",
}

log_lines = []
results = []


def log(text):
    """Print a line and keep a copy for the saved log file."""
    print(text)
    log_lines.append(text)


def read_field(page, field):
    """Independent check: read a field's value straight from the browser."""
    return page.locator(FIELD_IDS[field]).input_value()


def snapshot(page):
    """Record the URL and all three field values, to prove nothing changed."""
    state = {"url": page.url}
    for field in FIELD_IDS:
        state[field] = read_field(page, field)
    return state


def save_screenshot(page, name):
    """Save a screenshot as visual evidence of what the browser displayed."""
    os.makedirs(EVIDENCE_FOLDER, exist_ok=True)
    path = os.path.join(EVIDENCE_FOLDER, name + ".png")
    page.screenshot(path=path, full_page=True)
    log("Screenshot saved: team_tests/evidence/" + name + ".png")


def run_test(name, test_function, page):
    """Run one test. An AssertionError means FAIL; anything else is reported too."""
    log("")
    log("=" * 70)
    log("TEST: " + name)
    log("=" * 70)
    try:
        test_function(page)
        log("RESULT: PASS")
        results.append((name, "PASS"))
    except AssertionError as error:
        log("RESULT: FAIL - " + str(error))
        results.append((name, "FAIL"))
    except Exception as error:
        log("RESULT: FAIL - unexpected error: " + repr(error))
        results.append((name, "FAIL"))


def call_tool(page, argument):
    """Call the tool the way the shared agent will: validate first, then run."""
    log("Tool call: " + str(argument))
    valid, reason = fill_text.validate(argument)
    log("validate() returned: (" + str(valid) + ", " + repr(reason) + ")")

    if not valid:
        # The rule: if validation fails, run() is not called.
        log("run() NOT called because validation failed.")
        return valid, None

    result = fill_text.run(page, argument, {})
    log("run() returned: " + str(result))
    return valid, result


def check_success(page, field, value):
    """Shared steps for a successful fill: call the tool, then verify the page."""
    valid, result = call_tool(page, {"field": field, "value": value})
    assert valid is True, "validate() should accept this argument"

    # The return shape must have exactly these three keys.
    assert set(result) == {"ok", "message", "data"}, "wrong return keys"
    assert result["ok"] is True, "tool reported ok=False"

    # Do NOT trust ok=True by itself. Read the browser ourselves.
    browser_value = read_field(page, field)
    log("Independent browser read of " + FIELD_IDS[field] + ": " + repr(browser_value))
    assert browser_value == value, "browser shows " + repr(browser_value)

    # The tool's reported value must match what the browser really shows.
    assert result["data"]["actual_value"] == browser_value, "tool's actual_value differs from browser"
    log("Browser contains exactly " + repr(value) + ".")


# ---------------------------------------------------------------------------
# Tests on the search screen
# ---------------------------------------------------------------------------

def test_valid_departure_date(page):
    check_success(page, "departure_date", TEST_DATE)
    save_screenshot(page, "1_departure_date_filled")


def test_hidden_field_on_search_screen(page):
    """full_name exists but is hidden on the search screen. The tool must refuse."""
    before = snapshot(page)
    valid, result = call_tool(page, {"field": "full_name", "value": TEST_NAME})
    assert valid is True, "argument itself is valid; the problem is the page"
    assert result["ok"] is False, "tool must not report success on a hidden field"

    after = snapshot(page)
    log("Before: " + str(before))
    log("After:  " + str(after))
    assert after == before, "page changed even though the tool refused"
    log("Tool refused the hidden field and the page is unchanged.")


def test_invalid_inputs_are_rejected(page):
    """Bad arguments must be rejected by validate() before touching the browser."""
    bad_arguments = [
        {"field": "full_name", "value": ""},
        {"field": "full_name", "value": "   "},
        {"field": "departure_date", "value": "2026/12/15"},
        {"field": "departure_date", "value": "2026-02-30"},
        {"field": "departure_date", "value": "12-15-2026"},
        {"field": "email"},
        "full_name=Alex Student",
    ]
    before = snapshot(page)
    for argument in bad_arguments:
        valid, result = call_tool(page, argument)
        assert valid is False, "validate() accepted a bad argument: " + repr(argument)
        assert result is None, "run() should not have been called"

    after = snapshot(page)
    assert after == before, "page changed after rejected arguments"
    log("All " + str(len(bad_arguments)) + " bad arguments were rejected; page unchanged.")


# ---------------------------------------------------------------------------
# Tests on the passenger screen
# ---------------------------------------------------------------------------

def test_full_name_alex_student(page):
    check_success(page, "full_name", TEST_NAME)
    save_screenshot(page, "2_full_name_alex_student")


def test_email(page):
    check_success(page, "email", TEST_EMAIL)
    save_screenshot(page, "3_passenger_name_and_email_filled")


def test_credit_card_refused(page):
    """The required failure test: credit_card is not on the allowed list."""
    before = snapshot(page)
    log("Before: " + str(before))

    valid, result = call_tool(page, {"field": "credit_card", "value": "4111111111111111"})
    assert valid is False, "validate() must reject credit_card"
    assert result is None, "run() should not have been called"

    # Extra safety: even if someone skips validate() and calls run() directly,
    # run() checks again and must refuse.
    direct = fill_text.run(page, {"field": "credit_card", "value": "4111111111111111"}, {})
    log("Direct run() call (skipping validate) returned: " + str(direct))
    assert direct["ok"] is False, "run() must also refuse credit_card"

    after = snapshot(page)
    log("After:  " + str(after))
    assert after == before, "page changed after a refused request"
    log("credit_card was refused and the page is unchanged.")
    save_screenshot(page, "4_after_credit_card_refused")


# ---------------------------------------------------------------------------
# Getting to the passenger screen (setup, not the tool being graded)
# ---------------------------------------------------------------------------

def go_to_passenger_screen_automatically(page):
    """Setup only: click through search, flight and seat with plain Playwright."""
    log("Setup: Playwright clicks DCA -> BOS, Search, Choose AA101, seat 1A, Continue.")
    page.select_option("#fromAirport", "DCA")
    page.select_option("#toAirport", "BOS")
    page.click("#searchFlights")
    page.get_by_role("button", name="Choose AA101").click()
    page.get_by_role("button", name="Seat 1A", exact=True).click()
    page.click("#continueFromSeat")


def go_to_passenger_screen_by_hand(page):
    """Setup only: the person clicks through in the Playwright window."""
    print("")
    input(
        "In the Playwright Chromium window, choose From/To, search, choose a flight\n"
        "and a seat, and stop at '4. Passenger information'. Then press Enter here..."
    )
    log("Setup: tester navigated to the passenger screen by hand.")


def main():
    auto = "--auto" in sys.argv
    headless = "--headless" in sys.argv

    if headless and not auto:
        print("--headless needs --auto, because nobody can click in a hidden window.")
        sys.exit(2)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_default_timeout(10000)

        page.goto(SITE_URL, wait_until="domcontentloaded")
        log("Opened " + page.url)

        # Part 1: the opening search screen.
        run_test("Valid departure date on search screen", test_valid_departure_date, page)
        run_test("Hidden full_name on search screen is refused", test_hidden_field_on_search_screen, page)
        run_test("Bad arguments rejected before any typing", test_invalid_inputs_are_rejected, page)

        # Part 2: move to the passenger screen.
        if auto:
            go_to_passenger_screen_automatically(page)
        else:
            go_to_passenger_screen_by_hand(page)

        if not page.locator("#passengerName").is_visible():
            log("SETUP FAILED: the passenger screen is not showing. URL: " + page.url)
            results.append(("Reach passenger screen", "FAIL"))
        else:
            log("Passenger screen is showing. URL: " + page.url)
            run_test("Full name = Alex Student", test_full_name_alex_student, page)
            run_test("Email = alex@example.com", test_email, page)
            run_test("credit_card refused, page unchanged", test_credit_card_refused, page)

        browser.close()

    # Summary
    log("")
    log("=" * 70)
    log("SUMMARY")
    log("=" * 70)
    failures = 0
    for name, status in results:
        log(status + ": " + name)
        if status != "PASS":
            failures = failures + 1
    log(str(len(results) - failures) + " passed, " + str(failures) + " failed.")

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(log_lines) + "\n")
    print("Log saved to team_tests/fill_text_test_output.txt")

    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
