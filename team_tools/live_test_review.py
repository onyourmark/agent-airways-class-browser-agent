"""Live test in a real Playwright browser (run from the project folder).

    python team_tools/live_test_review.py

1. Edit GOAL below so it matches what you will enter on the site.
   Use a FUTURE date and pretend details only.
2. A browser opens. Search, pick a flight, pick a seat, enter the passenger
   details and continue to the REVIEW screen. Do NOT click Confirm reservation.
3. Come back to the terminal and press Enter.
"""

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import browser_tools
from check_review_against_goal import run

GOAL = {
    "from": "DCA", "to": "BOS", "date": "2026-11-04",
    "flight_id": "AA101", "seat": "1A",
    "passenger": "Alex Student", "email": "alex@example.com",
    "checked_bag": False, "priority_boarding": False,
}


def show(title, result):
    print("\n==", title, "==")
    print("ok:", result["ok"], "|", result["message"])
    print("checks:", result["data"].get("checks"))
    print("mismatches:", result["data"].get("mismatches"))


browser_tools.start_browser()
try:
    browser_tools.open_site()

    # Extra failure case: before the review stage
    show("Before review stage (should be ok=False)",
         run(browser_tools.page, {}, {"goal": GOAL}))

    input("\nGo to the REVIEW screen in the browser, then press Enter here...")
    before = browser_tools.page.locator("#reviewCard").inner_text()

    show("Normal (should be ok=True)",
         run(browser_tools.page, {}, {"goal": GOAL}))

    bad_seat = copy.deepcopy(GOAL); bad_seat["seat"] = "9F"
    show("Wrong seat (seat should be False)",
         run(browser_tools.page, {}, {"goal": bad_seat}))

    bad_email = copy.deepcopy(GOAL); bad_email["email"] = "wrong@example.com"
    show("Wrong email (email should be False)",
         run(browser_tools.page, {}, {"goal": bad_email}))

    incomplete = copy.deepcopy(GOAL); del incomplete["seat"]
    show("Incomplete goal (should explain why)",
         run(browser_tools.page, {}, {"goal": incomplete}))

    after = browser_tools.page.locator("#reviewCard").inner_text()
    print("\nPage unchanged by the tool:", before == after)
    input("\nPress Enter to close the browser (nothing was confirmed)...")
finally:
    browser_tools.close_browser()
