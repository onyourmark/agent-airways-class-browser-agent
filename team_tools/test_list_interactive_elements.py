"""Team 04 tests: list_interactive_elements

Success and failure tests for the read-only list_interactive_elements tool.

Part 1 needs no browser. Parts 2 to 4 open a visible Chromium window on the
Agent Airways practice site. Part 3 pauses so you can move to the seat map
by hand in that same window.

Run from the repository folder:
    python team_tools/test_list_interactive_elements.py
(on some Macs, use python3)
"""

import sys
from pathlib import Path

# Let this file import browser_tools.py from the repository folder.
REPO_FOLDER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_FOLDER))
sys.path.insert(0, str(REPO_FOLDER / "team_tools"))

import browser_tools
import list_interactive_elements as tool


# The search-screen controls the tool must report, with their expected kind.
SEARCH_CONTROLS = {
    "fromAirport": "select",
    "toAirport": "select",
    "departureDate": "date",
    "passengers": "select",
    "searchFlights": "button",
}

# The search-screen fields that hold a value Python can read directly.
SEARCH_FIELDS = ["fromAirport", "toAirport", "departureDate", "passengers"]

passed = 0
failed = 0


def check(name, condition, detail=""):
    """Print PASS or FAIL for one check and keep a running count."""
    global passed, failed
    if condition:
        passed = passed + 1
        print("PASS:", name)
    else:
        failed = failed + 1
        print("FAIL:", name)
    if detail != "":
        print("      ", detail)


def find_by_id(elements, element_id):
    """Return the reported control with this id, or None."""
    for element in elements:
        if element["id"] == element_id:
            return element
    return None


def find_by_seat(elements, seat):
    """Return the reported seat button for this seat, such as '1B', or None."""
    for element in elements:
        if element.get("seat") == seat:
            return element
    return None


def read_field_values(page):
    """Read every search-field value directly from the page, not from the tool."""
    values = {}
    for field_id in SEARCH_FIELDS:
        values[field_id] = page.locator("#" + field_id).input_value()
    return values


# A stand-in for the agent's dispatcher: validate first, run only if valid.
run_calls = []


def spy_run(page, argument, context):
    """Record that run() was called. Used to prove it is NOT called."""
    run_calls.append(argument)
    return {"ok": True, "message": "spy", "data": {}}


def dispatch(page, argument, run_function):
    valid, reason = tool.validate(argument)
    if not valid:
        return {"ok": False, "message": "VALIDATION ERROR: " + reason, "data": {}}
    return run_function(page, argument, {})


def test_validation():
    print("\n=== Part 1: validation (no browser) ===")
    cases = [
        ({}, True),
        ({"x": 1}, False),
        ("", False),
        (None, False),
    ]
    for argument, expected in cases:
        valid, reason = tool.validate(argument)
        if expected:
            name = repr(argument) + " is accepted"
        else:
            name = repr(argument) + " is rejected"
        check(name, valid == expected, "validate() said: " + reason)


def test_bad_argument_never_runs():
    print("\n=== Failure test: bad argument never reaches run() ===")
    run_calls.clear()
    result = dispatch(None, {"selector": "#x"}, spy_run)
    check('{"selector": "#x"} is rejected', result["ok"] is False, result["message"])
    check("run() was never called", len(run_calls) == 0,
          "run() calls recorded: " + str(len(run_calls)))

    # run() also re-checks the argument itself, as a safety net.
    result = tool.run(None, {"selector": "#x"}, {})
    check("run() refuses the bad argument on its own too", result["ok"] is False,
          result["message"])


def test_search_screen(page):
    print("\n=== Part 2: search screen ===")
    browser_tools.open_site()

    before = read_field_values(page)
    result = tool.run(page, {}, {})
    after = read_field_values(page)

    check("run() returns ok: True", result["ok"] is True, result["message"])
    data = result["data"]
    elements = data.get("elements", [])
    print("       stage:", data.get("stage"), "| url:", data.get("url"))

    for element_id in SEARCH_CONTROLS:
        expected_kind = SEARCH_CONTROLS[element_id]
        element = find_by_id(elements, element_id)
        if element is None:
            check(element_id + " (" + expected_kind + ") is listed", False, "missing")
            continue
        check(element_id + " (" + expected_kind + ") is listed",
              element["kind"] == expected_kind,
              "reported: " + str(element))

    print("\n--- Independent check: tool value vs page.locator(...).input_value() ---")
    for field_id in SEARCH_FIELDS:
        element = find_by_id(elements, field_id)
        if element is None:
            check(field_id + " value matches the page", False, "not listed")
            continue
        direct = page.locator("#" + field_id).input_value()
        check(field_id + " value matches the page", element["value"] == direct,
              "tool: " + repr(element["value"]) + " | page: " + repr(direct))

    button = find_by_id(elements, "searchFlights")
    if button is not None:
        check("searchFlights has no value (buttons hold none)", button["value"] is None,
              "tool: " + repr(button["value"]))

    print("\n--- Independent check: read-only (values before and after run()) ---")
    for field_id in SEARCH_FIELDS:
        check(field_id + " unchanged by run()", before[field_id] == after[field_id],
              "before: " + repr(before[field_id]) + " | after: " + repr(after[field_id]))
    check("still on the search screen after run()", page.url.endswith("#search"),
          "url: " + page.url)


def test_seat_screen(page):
    print("\n=== Part 3: later screen (seat map) ===")
    print("In the open browser window, by hand:")
    print("  1. Choose From and To airports (different ones), then Search flights.")
    print("  2. Choose any flight.")
    print("  3. Stop on the seat map. Do NOT pick a seat.")
    input("Press Enter here when the seat map is showing... ")

    result = tool.run(page, {}, {})
    check("run() returns ok: True", result["ok"] is True, result["message"])
    data = result["data"]
    elements = data.get("elements", [])
    print("       stage:", data.get("stage"), "| url:", data.get("url"))
    check("tool reports the seat stage", data.get("stage") == "seatStage",
          "stage: " + repr(data.get("stage")))

    seat = find_by_seat(elements, "1B")
    check("seat 1B is listed", seat is not None, "reported: " + str(seat))
    if seat is not None:
        direct = page.locator("button[data-seat='1B']").is_enabled()
        check("seat 1B shows as disabled", seat["enabled"] is False,
              "tool enabled: " + str(seat["enabled"]) + " | page is_enabled(): " + str(direct))

    button = find_by_id(elements, "continueFromSeat")
    check("Continue button is listed", button is not None, "reported: " + str(button))
    if button is not None:
        direct = page.locator("#continueFromSeat").is_enabled()
        check("Continue button shows as disabled", button["enabled"] is False,
              "tool enabled: " + str(button["enabled"]) + " | page is_enabled(): " + str(direct))

    leaked = []
    for element_id in SEARCH_CONTROLS:
        if find_by_id(elements, element_id) is not None:
            leaked.append(element_id)
    check("no search-screen controls are listed", len(leaked) == 0,
          "search controls found: " + str(leaked))


def test_blank_page():
    print("\n=== Failure test: off-site page (about:blank) ===")
    # A new tab starts on about:blank, so no other website is visited.
    blank_page = browser_tools.browser.new_page()
    try:
        result = tool.run(blank_page, {}, {})
        check("run() on about:blank returns ok: False", result["ok"] is False,
              "url: " + blank_page.url + " | message: " + result["message"])
        check("no controls are reported", result["data"].get("elements") == [],
              "elements: " + str(result["data"].get("elements")))
    finally:
        blank_page.close()


def main():
    test_validation()
    test_bad_argument_never_runs()

    browser_tools.start_browser()
    try:
        page = browser_tools.page
        test_search_screen(page)
        test_seat_screen(page)
        test_blank_page()
    finally:
        browser_tools.close_browser()

    print("\n=== Summary ===")
    print("Passed:", passed, "| Failed:", failed)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
