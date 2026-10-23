"""Team 11: direct browser tests, without a model or a complete agent.

Run from the repository: python -m team_tests.test_select_seat
Optional: --headed --evidence evidence/team11_select_seat.json
"""

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys

from playwright.sync_api import sync_playwright

# Also support: python team_tests/test_select_seat.py
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from browser_tools import SITE_URL
from team_tools.select_seat import run, validate


def snapshot(page):
    """Read the DOM independently; never treat the tool's report as proof."""
    selected = []
    buttons = page.locator("#seatMap button.selected")
    for index in range(buttons.count()):
        selected.append(buttons.nth(index).get_attribute("data-seat"))
    message = page.locator("#seatMessage")
    continue_button = page.locator("#continueFromSeat")
    return {
        "selected_seats": selected,
        "seat_message": message.inner_text() if message.count() == 1 else None,
        "continue_enabled": continue_button.is_enabled() if continue_button.count() == 1 else None,
        "seat_stage_visible": page.locator("#seatStage").is_visible(),
        "passenger_stage_visible": page.locator("#passengerStage").is_visible(),
    }


def check_case(page, records, name, argument, expected_ok):
    before = snapshot(page)
    result = run(page, argument, {})
    after = snapshot(page)
    record = {
        "name": name,
        "proposal": {"action": "select_seat", "argument": argument},
        "before": before,
        "tool_return": result,
        "independent_check": after,
        "expected_ok": expected_ok,
        "passed": False,
    }
    records.append(record)
    print("CALL:", name, json.dumps(record["proposal"]))
    assert set(result) == {"ok", "message", "data"}, name
    assert type(result["ok"]) is bool, name
    assert type(result["message"]) is str and result["message"], name
    assert type(result["data"]) is dict, name
    assert result["ok"] is expected_ok, name
    if expected_ok:
        seat = argument["seat"]
        assert after["selected_seats"] == [seat], name
        assert after["seat_message"] == "Selected seat " + seat + ".", name
        assert after["continue_enabled"] is True, name
        assert after["seat_stage_visible"] is True, name
        assert after["passenger_stage_visible"] is False, name
        assert result["data"]["seat"] == seat, name
        assert result["data"]["selected_seat"] == after["selected_seats"][0], name
        assert result["data"]["seat_message"] == after["seat_message"], name
        assert result["data"]["continue_enabled"] is True, name
    else:
        assert after == before, name + ": rejected request changed the browser"
    record["passed"] = True
    print(json.dumps(record, ensure_ascii=False))
    print("PASS:", name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headed", action="store_true", help="Show Chromium")
    parser.add_argument("--evidence", type=Path, help="Write a reproducible JSON trace")
    args = parser.parse_args()
    records = []
    evidence = {
        "team": "Team 11",
        "tool": "select_seat",
        "site_url": SITE_URL,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "playwright_version": version("playwright"),
        "headless": not args.headed,
        "records": records,
        "passed": False,
    }
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not args.headed)
            evidence["browser_version"] = browser.version
            page = browser.new_page()
            page.set_default_timeout(5000)
            try:
                response = page.goto(SITE_URL, wait_until="load")
                assert response is not None and response.ok, "Practice site failed to load"
                check_case(page, records, "before seat stage", {"seat": "1A"}, False)

                # Test setup only: reach the assigned tool's real prerequisite stage.
                page.locator("#fromAirport").select_option("DCA")
                page.locator("#toAirport").select_option("BOS")
                page.locator("#searchFlights").click()
                # Playwright waits for the delayed flight button, not a fixed sleep.
                page.locator('button.choose[data-flight="AA101"]').click()
                page.locator("#seatStage").wait_for(state="visible")
                assert page.locator("#seatStage").is_visible()
                assert page.locator('#seatMap button.seat[data-seat="1A"]').is_visible()
                assert page.locator('#seatMap button.seat[data-seat="1B"]').is_disabled()

                check_case(page, records, "available seat 1A", {"seat": "1A"}, True)
                check_case(page, records, "unavailable seat 1B", {"seat": "1B"}, False)
                check_case(page, records, "missing seat 99Z", {"seat": "99Z"}, False)
                check_case(page, records, "reselect available seat 2A", {"seat": "2A"}, True)
                check_case(page, records, "same seat repeated", {"seat": "2A"}, True)

                # Malformed input must be rejected by both the validator and run().
                invalid = [None, "1A", {}, {"seat": 1}, {"seat": ""},
                           {"seat": "1a"}, {"seat": " 1A "}, {"seat": "1A", "extra": True}]
                for argument in invalid:
                    valid, note = validate(argument)
                    assert valid is False and type(note) is str and note
                    # No page object: a rejected argument must not access a browser.
                    assert run(None, argument, {})["ok"] is False
                evidence["invalid_arguments_rejected"] = invalid
                valid, note = validate({"seat": "1A"})
                assert valid is True and type(note) is str and note
                print("PASS: valid seat accepted; 8 malformed arguments rejected without browser access")
                check_case(page, records, "non-dictionary argument refused", None, False)
                check_case(page, records, "unexpected key refused", {"seat": "1A", "extra": True}, False)

                # Controlled DOM changes exercise problems absent from the normal site.
                seat = page.locator('#seatMap button[data-seat="1A"]')
                seat.evaluate("button => button.after(button.cloneNode(true))")
                check_case(page, records, "duplicate seat refused", {"seat": "1A"}, False)
                page.locator('#seatMap button[data-seat="1A"]').last.evaluate("button => button.remove()")

                seat.evaluate("button => button.style.display = 'none'")
                check_case(page, records, "hidden seat refused", {"seat": "1A"}, False)
                seat.evaluate("button => button.style.display = ''")

                seat.evaluate("button => button.disabled = true")
                check_case(page, records, "disabled seat refused", {"seat": "1A"}, False)
                seat.evaluate("button => button.disabled = false")

                # A successful Playwright click must not imply successful selection.
                # Temporarily block the site's handler, leaving 2A selected.
                page.locator("#seatMap").evaluate("""map => {
                    window.blockSeatClick = event => event.stopImmediatePropagation();
                    map.addEventListener('click', window.blockSeatClick, true);
                }""")
                check_case(page, records, "click without selection refused", {"seat": "1A"}, False)
                page.locator("#seatMap").evaluate("""map => {
                    map.removeEventListener('click', window.blockSeatClick, true);
                    delete window.blockSeatClick;
                }""")

                # Same-origin history change only; no other website is contacted.
                original_url = page.url
                page.evaluate("history.pushState({}, '', '/browser-agent-form/not-travel/')")
                check_case(page, records, "unapproved path refused", {"seat": "1A"}, False)
                page.evaluate("url => history.replaceState({}, '', url)", original_url)

                page.locator("#continueFromSeat").evaluate("button => button.remove()")
                check_case(page, records, "missing Continue refused", {"seat": "1A"}, False)
                evidence["passed"] = True
            finally:
                browser.close()
    finally:
        evidence["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        if args.evidence:
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print("Saved evidence:", args.evidence)
    print("All", len(records), "direct browser cases passed; no model was used.")


if __name__ == "__main__":
    main()
