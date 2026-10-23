"""
Test program for Team 02's set_checkbox tool.
Run it from the main repository folder with:  python3 -m team_tools.test_set_checkbox
(on some computers, use python instead of python3)
"""

import json
import browser_tools
from team_tools import set_checkbox

passed = 0
failed = 0


def check(description, condition):
    # Records one test result as PASS or FAIL.
    global passed, failed
    if condition:
        passed = passed + 1
        print("PASS:", description)
    else:
        failed = failed + 1
        print("FAIL:", description)


def try_tool(argument):
    # Does what the agent will do: validate first, run only if valid.
    print()
    print("PROPOSAL:  ", json.dumps({"action": "set_checkbox", "argument": argument}))
    is_valid, reason = set_checkbox.validate(argument)
    print("VALIDATION:", is_valid, "-", reason)
    if not is_valid:
        print("ACTION:     none (blocked before touching the browser)")
        return {"ok": False, "message": reason, "data": {}}
    result = set_checkbox.run(browser_tools.page, argument, {})
    print("RESULT:    ", json.dumps(result))
    return result


def main():
    browser_tools.start_browser()
    page = browser_tools.page
    page.goto(browser_tools.SITE_URL)

    # Test 1: wrong screen. The bag checkbox is not usable on the search screen.
    print("\n=== Test 1: calling the tool on the search screen (should fail safely) ===")
    result = try_tool({"field": "checked_bag", "checked": True})
    check("Tool reports failure when the checkbox is not on the current screen", result["ok"] == False)

    # Pause so a person can click through the site in the Playwright window.
    print()
    input("In the Playwright browser window, search for a flight, choose AA101 and seat 1A, "
          "and continue to the passenger details screen. Do not tick any boxes. "
          "Then press Enter here... ")

    bag = page.locator("#checkedBag")
    priority = page.locator("#priorityBoarding")

    # Test 2: check the bag box, then confirm with our own separate read of the page.
    print("\n=== Test 2: set checked_bag to True ===")
    result = try_tool({"field": "checked_bag", "checked": True})
    actual = bag.is_checked()
    print("INDEPENDENT CHECK: the browser says checkedBag is", actual)
    check("checked_bag is True on the page", result["ok"] == True and actual == True)
    page.screenshot(path="evidence_bag_checked.png")
    page.wait_for_timeout(2000)

    # Test 3: uncheck it again and confirm.
    print("\n=== Test 3: set checked_bag to False ===")
    result = try_tool({"field": "checked_bag", "checked": False})
    actual = bag.is_checked()
    print("INDEPENDENT CHECK: the browser says checkedBag is", actual)
    check("checked_bag is False on the page", result["ok"] == True and actual == False)
    page.screenshot(path="evidence_bag_unchecked.png")
    page.wait_for_timeout(2000)

    # Test 4: unknown checkbox name must be refused, and nothing on the page changes.
    print("\n=== Test 4: unknown checkbox name (should be refused) ===")
    before = bag.is_checked()
    result = try_tool({"field": "credit_card", "checked": True})
    after = bag.is_checked()
    print("INDEPENDENT CHECK: checkedBag before =", before, ", after =", after)
    check("Unknown name is refused and the page is unchanged", result["ok"] == False and before == after)

    # Test 5: checked='yes' (text, not a Boolean) must be refused.
    print("\n=== Test 5: checked='yes' instead of True (should be refused) ===")
    before = bag.is_checked()
    result = try_tool({"field": "checked_bag", "checked": "yes"})
    after = bag.is_checked()
    print("INDEPENDENT CHECK: checkedBag before =", before, ", after =", after)
    check("Text 'yes' is refused and the page is unchanged", result["ok"] == False and before == after)

    # Test 6: priority boarding, on then off.
    print("\n=== Test 6: set priority_boarding to True, then False ===")
    result = try_tool({"field": "priority_boarding", "checked": True})
    actual = priority.is_checked()
    print("INDEPENDENT CHECK: the browser says priorityBoarding is", actual)
    check("priority_boarding is True on the page", result["ok"] == True and actual == True)
    page.wait_for_timeout(1500)
    result = try_tool({"field": "priority_boarding", "checked": False})
    actual = priority.is_checked()
    print("INDEPENDENT CHECK: the browser says priorityBoarding is", actual)
    check("priority_boarding is False on the page", result["ok"] == True and actual == False)

    # Pause again so a person can move to the review screen.
    print()
    input("Now type a pretend name (Alex Student) and email (alex@example.com), "
          "click 'Continue to review', and stop on the review screen. "
          "Do not tick the confirm box or click Confirm. Then press Enter here... ")

    confirm = page.locator("#confirmDetails")

    # Test 7: the confirm box on the review screen. Ticking it must NOT submit the reservation.
    print("\n=== Test 7: set confirm_details to True, then False (must not submit) ===")
    result = try_tool({"field": "confirm_details", "checked": True})
    actual = confirm.is_checked()
    still_on_review = "#confirmation" not in page.url
    print("INDEPENDENT CHECK: confirmDetails is", actual, ", page URL is", page.url)
    check("confirm_details is True and the reservation was not submitted",
          result["ok"] == True and actual == True and still_on_review)
    page.screenshot(path="evidence_confirm_checked.png")
    page.wait_for_timeout(2000)
    result = try_tool({"field": "confirm_details", "checked": False})
    actual = confirm.is_checked()
    print("INDEPENDENT CHECK: the browser says confirmDetails is", actual)
    check("confirm_details is False on the page", result["ok"] == True and actual == False)

    print("\n=== Summary:", passed, "passed,", failed, "failed ===")
    input("Press Enter to close the browser... ")


try:
    main()
finally:
    browser_tools.close_browser()
