"""Team 13 tests for read_review.

Run from the repository folder:
    python3 team_tests/test_read_review.py

Test 1 (failure case): call read_review on the search screen.
    It must report "review not ready".
Test 2 (success case): a person moves the Playwright browser to the
    Review screen by hand, then read_review reads it. The test checks
    the returned values against what the browser really shows.
"""

import os
import sys

# Let Python find browser_tools.py and team_tools/ in the folder above.
REPO_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_FOLDER)

import browser_tools as tools
from team_tools import read_review

# The values the person types in the browser during Test 2.
EXPECTED_NAME = "Alex Student"
EXPECTED_EMAIL = "alex@example.com"
EXPECTED_SEAT = "1A"


def test_not_ready():
    print("=== Test 1 (failure case): read_review on the search screen ===")

    # Setup (not the graded tool): open the site. It starts on the search screen.
    tools.open_site()

    # Check the argument first, the same way the agent will.
    argument = {}
    valid, note = read_review.validate(argument)
    print("validate({}) ->", valid, note)

    # Call the tool.
    print("Call: read_review.run(page, {}, {})")
    result = read_review.run(tools.page, argument, {})
    print("Returned observation:", result)

    # Independent check: ask the browser if the Review screen is visible.
    review_visible = tools.page.locator("#reviewStage").is_visible()
    print("Browser evidence: #reviewStage visible =", review_visible)

    # Pass only if the tool said "not ready" AND the browser agrees.
    if result["ok"] is False and "not ready" in result["message"] and not review_visible:
        print("PASS: the tool correctly reported that the review is not ready")
        passed = True
    else:
        print("FAIL: the tool did not report 'review not ready' correctly")
        passed = False
    print()
    return passed

def test_success():
    print("=== Test 2 (success case): read the Review screen ===")

    # Setup (not the graded tool): a person moves the browser by hand.
    print("In the Playwright browser window, do these steps by hand:")
    print("  1. Choose From and To, then click Search flights")
    print("  2. Choose any flight")
    print("  3. Choose seat " + EXPECTED_SEAT + ", then click Continue")
    print("  4. Full name: " + EXPECTED_NAME)
    print("  5. Email: " + EXPECTED_EMAIL)
    print("  6. Click Continue to review")
    input("When the Review screen is showing, press Enter here... ")

    # Check the argument, then call the tool.
    argument = {}
    valid, note = read_review.validate(argument)
    print("validate({}) ->", valid, note)
    print("Call: read_review.run(page, {}, {})")
    result = read_review.run(tools.page, argument, {})
    print("Returned observation:", result)

    if result["ok"] is not True:
        print("FAIL: the tool could not read the review:", result["message"])
        print()
        return False

    review = result["data"]["review"]

    # Independent check: read the review card text straight from the browser.
    card_text = tools.page.locator("#reviewCard").inner_text()
    print("Browser evidence (#reviewCard text):")
    print(card_text)

    # Compare each expected value with the tool's result AND the browser text.
    expected_values = {
        "Passenger": EXPECTED_NAME,
        "Email": EXPECTED_EMAIL,
        "Seat": EXPECTED_SEAT,
    }
    passed = True
    for field in expected_values:
        expected = expected_values[field]
        returned = review.get(field, "")
        in_browser = expected in card_text
        if returned == expected and in_browser:
            print("PASS:", field, "=", returned)
        else:
            print("FAIL:", field, "returned", repr(returned), "expected", repr(expected))
            passed = False
    print()
    return passed


def main():
    # Start the browser once, run both tests, then always close it.
    tools.start_browser()
    try:
        passed_1 = test_not_ready()
        passed_2 = test_success()
    finally:
        tools.close_browser()

    print("=== Summary ===")
    if passed_1:
        print("Test 1 failure case (review not ready): PASS")
    else:
        print("Test 1 failure case (review not ready): FAIL")
    if passed_2:
        print("Test 2 success case (read Review screen): PASS")
    else:
        print("Test 2 success case (read Review screen): FAIL")

    # Exit with an error code if any test failed.
    if not (passed_1 and passed_2):
        sys.exit(1)


if __name__ == "__main__":
    main()