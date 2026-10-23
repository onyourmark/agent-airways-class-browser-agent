"""Tests for the select_option tool (Team 09).

Run from the MAIN project folder (not inside team_tests):
    python -m team_tests.test_select_option
    (on some Macs: python3 -m team_tests.test_select_option)

What happens:
  * Part A checks validate() with bad arguments. No browser is needed.
  * Part B opens Agent Airways in a visible Chromium window and calls
    select_option.run(page, argument, context) directly. No language model is used.
  * After every call, the test reads the real dropdown itself with Playwright,
    so we do not just trust what the tool says about itself.
"""

import sys
import browser_tools
from team_tools import select_option

# Every check is saved here as (name, passed).
results = []


def record(name, passed):
    """Save and print one PASS/FAIL line."""
    results.append((name, passed))
    if passed:
        print("   PASS:", name)
    else:
        print("   FAIL:", name)


def read_dropdown(page, element_id):
    """Independent check: read the dropdown's value straight from the browser."""
    return page.locator("#" + element_id).input_value()


# ---------------------------------------------------------------------------
# Part A: validate() rejects bad arguments before the browser is touched
# ---------------------------------------------------------------------------
print("=== PART A: validate() checks ===")

argument = {"field": "from", "value": "DCA"}
valid, reason = select_option.validate(argument)
print("validate(", argument, ") ->", valid, "|", reason)
record("validate accepts a correct argument", valid == True)

argument = {"field": "credit_card", "value": "1234"}
valid, reason = select_option.validate(argument)
print("validate(", argument, ") ->", valid, "|", reason)
record("validate rejects an unknown field", valid == False)

argument = {"field": "from"}
valid, reason = select_option.validate(argument)
print("validate(", argument, ") ->", valid, "|", reason)
record("validate rejects a missing value", valid == False)

argument = {"field": "passengers", "value": 1}
valid, reason = select_option.validate(argument)
print("validate(", argument, ") ->", valid, "|", reason)
record("validate rejects a value that is not text", valid == False)

argument = "from=DCA"
valid, reason = select_option.validate(argument)
print("validate(", argument, ") ->", valid, "|", reason)
record("validate rejects an argument that is not a dictionary", valid == False)


# ---------------------------------------------------------------------------
# Part B: browser tests on the real Agent Airways search page
# ---------------------------------------------------------------------------
browser_tools.start_browser()
try:
    browser_tools.open_site()
    page = browser_tools.page
    context = {}   # this tool does not need trusted context

    # ===== TEST 1: SUCCESS - From=DCA, To=BOS, Passengers=1 =================
    print("\n=== TEST 1 (success): From=DCA, To=BOS, Passengers=1 ===")

    # The page starts with Passengers already set to 1, so the test first
    # chooses 2 and then 1. That shows the tool really changes the dropdown.
    requests_to_make = [
        ({"field": "from", "value": "DCA"}, "fromAirport"),
        ({"field": "to", "value": "BOS"}, "toAirport"),
        ({"field": "passengers", "value": "2"}, "passengers"),
        ({"field": "passengers", "value": "1"}, "passengers"),
    ]

    for pair in requests_to_make:
        argument = pair[0]
        element_id = pair[1]

        print("\nCALL: select_option.run(page,", argument, ", {})")
        result = select_option.run(page, argument, context)
        print("RETURNED:", result)

        # Independent check: what does the real dropdown contain?
        browser_value = read_dropdown(page, element_id)
        print("BROWSER EVIDENCE: #" + element_id + " =", browser_value)

        record("tool reports ok for " + argument["field"] + "=" + argument["value"], result["ok"] == True)
        record("browser #" + element_id + " really shows " + argument["value"], browser_value == argument["value"])

    # ===== TEST 2: FAILURE - From=ZZZ must be refused, DCA must stay ========
    print("\n=== TEST 2 (failure): From=ZZZ is not a real airport ===")

    before = read_dropdown(page, "fromAirport")
    argument = {"field": "from", "value": "ZZZ"}
    print("BROWSER BEFORE: #fromAirport =", before)
    print("CALL: select_option.run(page,", argument, ", {})")
    result = select_option.run(page, argument, context)
    print("RETURNED:", result)

    after = read_dropdown(page, "fromAirport")
    print("BROWSER EVIDENCE: #fromAirport =", after)

    record("tool reports ok=False for From=ZZZ", result["ok"] == False)
    record("From is unchanged after the refused request", after == before)

    # ===== TEST 3: FAILURE - Passengers=99 must be refused, 1 must stay =====
    print("\n=== TEST 3 (failure): Passengers=99 is not an option ===")

    before = read_dropdown(page, "passengers")
    argument = {"field": "passengers", "value": "99"}
    print("BROWSER BEFORE: #passengers =", before)
    print("CALL: select_option.run(page,", argument, ", {})")
    result = select_option.run(page, argument, context)
    print("RETURNED:", result)

    after = read_dropdown(page, "passengers")
    print("BROWSER EVIDENCE: #passengers =", after)

    record("tool reports ok=False for Passengers=99", result["ok"] == False)
    record("Passengers is unchanged after the refused request", after == before)

    # ===== TEST 4: FAILURE - an unknown field is rejected by run() too ======
    print("\n=== TEST 4 (failure): unknown field credit_card ===")

    argument = {"field": "credit_card", "value": "1234"}
    print("CALL: select_option.run(page,", argument, ", {})")
    result = select_option.run(page, argument, context)
    print("RETURNED:", result)

    record("tool reports ok=False for an unknown field", result["ok"] == False)
    record("all three dropdowns still show DCA / BOS / 1",
           read_dropdown(page, "fromAirport") == "DCA"
           and read_dropdown(page, "toAirport") == "BOS"
           and read_dropdown(page, "passengers") == "1")

finally:
    browser_tools.close_browser()


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
passed_count = 0
for item in results:
    if item[1]:
        passed_count = passed_count + 1

print("\n=== SUMMARY:", passed_count, "of", len(results), "checks passed ===")

if passed_count != len(results):
    sys.exit(1)
