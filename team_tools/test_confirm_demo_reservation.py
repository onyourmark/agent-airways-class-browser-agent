"""Team 12 tests for confirm_demo_reservation.

Run from the repository folder:

    python team_tools/test_confirm_demo_reservation.py           (offline checks, no browser)
    python team_tools/test_confirm_demo_reservation.py success   (live browser: should confirm)
    python team_tools/test_confirm_demo_reservation.py failure   (live browser: must NOT confirm)

On some Macs, use python3 instead of python.

The live tests open Agent Airways in a Playwright browser. While Python waits,
you fill in the earlier screens by hand in THAT browser window, then press Enter.
Each live test saves what Python returned and a screenshot in team_tools/team12_evidence/.
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Let this file import browser_tools.py from the repository folder.
REPO_FOLDER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_FOLDER))
sys.path.insert(0, str(REPO_FOLDER / "team_tools"))

import confirm_demo_reservation as tool

EVIDENCE_FOLDER = REPO_FOLDER / "team_tools" / "team12_evidence"


def make_goal():
    """The user's requested trip. In the real agent, trusted Python supplies this.

    The website's default departure date is 7 days from today (UTC),
    so the goal uses the same date.
    """
    date = datetime.now(timezone.utc).date() + timedelta(days=7)
    return {
        "from": "DCA",
        "to": "BOS",
        "date": date.isoformat(),
        "flight_id": "AA101",
        "seat": "1A",
        "passenger_name": "Test Traveler",
        "email": "traveler@example.com",
        "checked_bag": False,
        "priority_boarding": False,
    }


# ---------------------------------------------------------------------------
# Offline checks: no browser needed. Each one proves a request is blocked
# before the tool touches the page (page is None).
# ---------------------------------------------------------------------------

def check(name, condition):
    if condition:
        print("PASS:", name)
    else:
        print("FAIL:", name)
        raise AssertionError(name)


def run_offline_checks():
    goal = make_goal()

    valid, note = tool.validate({})
    check("empty argument is accepted", valid is True)

    valid, note = tool.validate("")
    check("text argument is rejected", valid is False)

    valid, note = tool.validate({"flight_id": "AA101"})
    check("non-empty argument is rejected", valid is False)

    valid, note = tool.validate({"human_approved": True})
    check("model cannot approve itself in the argument", valid is False)

    tool.reset_attempt_for_tests()
    output = tool.run(None, {}, {"human_approved": False, "goal": goal})
    check("human_approved=False is rejected", output["ok"] is False and output["data"]["clicked"] is False)

    output = tool.run(None, {}, {"human_approved": "yes", "goal": goal})
    check("human_approved='yes' (text) is rejected", output["ok"] is False)

    output = tool.run(None, {}, {"goal": goal})
    check("missing approval is rejected", output["ok"] is False)

    output = tool.run(None, {}, {"human_approved": True})
    check("missing goal is rejected", output["ok"] is False)

    output = tool.run(None, {"human_approved": True}, {"human_approved": False, "goal": goal})
    check("approval inside the argument is rejected", output["ok"] is False)

    # Compare a pretend review card with the goal.
    good_card = {
        "Route": "DCA → BOS",
        "Date": goal["date"],
        "Flight": "AA101",
        "Seat": "1A",
        "Passenger": "Test Traveler",
        "Email": "traveler@example.com",
        "Checked bag": "No",
        "Priority boarding": "No",
    }
    check("matching review card has no mismatches", len(tool.compare_card_to_goal(good_card, goal)) == 0)

    wrong_card = dict(good_card)
    wrong_card["Seat"] = "2A"
    check("wrong seat on review card is caught", len(tool.compare_card_to_goal(wrong_card, goal)) == 1)

    print()
    print("All offline checks passed.")


# ---------------------------------------------------------------------------
# Live browser tests
# ---------------------------------------------------------------------------

def print_instructions(goal):
    print()
    print("In the Playwright browser window, fill in the trip EXACTLY like this:")
    print("  From:", goal["from"], "  To:", goal["to"], "  Date:", goal["date"], "(the default)")
    print("  Passengers: 1   Flight:", goal["flight_id"], "  Seat:", goal["seat"])
    print("  Full name:", goal["passenger_name"], "  Email:", goal["email"])
    print("  Leave both optional extras unchecked.")
    print("On the review screen, tick 'I confirm that the reservation details above are correct'.")
    print("Do NOT click Confirm reservation yourself.")
    print()


def ask_human_for_approval(page):
    """Show the review to a real person in the terminal and ask for approval.

    This is the trusted approval. The model never sets this value.
    """
    review = tool.read_card(page, "#reviewCard")
    print()
    print("The browser's review screen shows:")
    for label in review:
        print("  " + label + ": " + review[label])
    print()
    answer = input("Type YES to approve this PRETEND reservation (anything else = no): ")
    return answer.strip() == "YES"


def read_browser_state(page):
    """Independent read of the browser after the tool ran (not from the tool's result)."""
    return {
        "url": page.url,
        "review_screen_visible": page.locator("#reviewStage").is_visible(),
        "confirmation_screen_visible": page.locator("#confirmationStage").is_visible(),
        "page_checkbox_checked": page.locator("#confirmDetails").is_checked(),
    }


def save_evidence(name, page, proposal, context, validation, output, browser_state):
    EVIDENCE_FOLDER.mkdir(exist_ok=True)
    record = {
        "test": name,
        "model_proposal": proposal,
        "trusted_context": context,
        "validation": {"valid": validation[0], "note": validation[1]},
        "tool_returned": output,
        "browser_checked_afterward": browser_state,
    }
    json_path = EVIDENCE_FOLDER / (name + "_result.json")
    json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    screenshot_path = EVIDENCE_FOLDER / (name + "_screenshot.png")
    page.screenshot(path=str(screenshot_path), full_page=True)
    print("Saved", json_path)
    print("Saved", screenshot_path)


def run_live_test(name):
    import browser_tools

    goal = make_goal()
    proposal = {"action": "confirm_demo_reservation", "argument": {}}

    browser_tools.start_browser()
    try:
        browser_tools.open_site()
        page = browser_tools.page
        print_instructions(goal)
        input("Move to the review screen in this Playwright browser, then press Enter.")

        if name == "success":
            approved = ask_human_for_approval(page)
        else:
            # Failure test: approval is False even though the page checkbox is ticked.
            approved = False
            print("Failure test: trusted context has human_approved=False.")

        context = {"human_approved": approved, "goal": goal}

        # The agent would validate first and only call run() when valid.
        validation = tool.validate(proposal["argument"])
        print("validate() returned:", validation)
        tool.reset_attempt_for_tests()
        if validation[0]:
            output = tool.run(page, proposal["argument"], context)
        else:
            output = {"ok": False, "message": "Not run: " + validation[1], "data": {}}

        print()
        print("run() returned:")
        print(json.dumps(output, indent=2, ensure_ascii=False))

        # Check the browser ourselves, separately from what the tool said.
        browser_state = read_browser_state(page)
        print()
        print("Browser checked afterward:", browser_state)

        if name == "success":
            passed = output["ok"] is True and browser_state["confirmation_screen_visible"]
        else:
            passed = (
                output["ok"] is False
                and output["data"].get("clicked") is False
                and browser_state["review_screen_visible"]
                and not browser_state["confirmation_screen_visible"]
            )

        print()
        if passed:
            print("TEST PASSED:", name)
        else:
            print("TEST FAILED:", name)

        save_evidence(name, page, proposal, context, validation, output, browser_state)
        input("Press Enter to close the browser...")
    finally:
        browser_tools.close_browser()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["success", "failure"]:
        run_live_test(sys.argv[1])
    else:
        run_offline_checks()
