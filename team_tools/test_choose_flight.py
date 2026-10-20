"""Team 08 tests. Save in team_tools/ beside choose_flight.py.
Run from the repository root: python team_tools/test_choose_flight.py
"""
from datetime import date, timedelta
from pathlib import Path
import json

from playwright.sync_api import sync_playwright
import choose_flight


# Screenshots and the text log are saved here as evidence for the pull request.
EVIDENCE = Path(__file__).resolve().parent / "evidence_choose_flight"


def prepare_results(page):
    # Browser setup only: submit a real search and wait for loaded results.
    page.goto(choose_flight.SITE_URL, wait_until="domcontentloaded")
    page.locator("#fromAirport").select_option("DCA")
    page.locator("#toAirport").select_option("BOS")
    # Search one week ahead so the date is always in the future.
    departure = (date.today() + timedelta(days=7)).isoformat()
    page.locator("#departureDate").fill(departure)
    page.locator("#searchFlights").click()
    # Wait until the flight cards are shown and "Loading flights..." is gone.
    page.locator("#resultsStage").wait_for(state="visible")
    page.locator('button.choose[data-flight="AA101"]').wait_for(state="visible")
    page.locator("#loadingFlights").wait_for(state="hidden")


def record(log, text):
    # Print each line and also save it to test_results.txt.
    print(text, flush=True)
    log.write(text + "\n")
    log.flush()


def check_rejection(page, argument, name, log):
    # Call the tool with an argument it should refuse, then check nothing changed.
    record(log, "CALL choose_flight.run: " + json.dumps(argument))
    result = choose_flight.run(page, argument, {})
    record(log, "RETURN: " + json.dumps(result))
    # Inspect the browser independently of the returned dictionary.
    results_visible = page.locator("#resultsStage").is_visible()
    seat_visible = page.locator("#seatStage").is_visible()
    record(log, f"BROWSER: results_visible={results_visible}, seat_visible={seat_visible}")
    page.screenshot(path=str(EVIDENCE / (name + ".png")), full_page=True)
    # The tool must report failure, must not click, and the page must stay on the results stage.
    assert result["ok"] is False
    assert result["data"]["clicked"] is False
    assert results_visible is True
    assert seat_visible is False
    record(log, "PASS: " + name)


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with (EVIDENCE / "test_results.txt").open("w", encoding="utf-8") as log:
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": 1280, "height": 900})
                    page.set_default_timeout(15000)
                    prepare_results(page)

                    # A correctly formatted ID that is absent from the live results.
                    assert page.locator('[data-flight-id="ZZ999"]').count() == 0
                    valid, reason = choose_flight.validate({"flight_id": "ZZ999"})
                    assert valid is True, reason
                    check_rejection(page, {"flight_id": "ZZ999"}, "unavailable_flight", log)

                    # Invalid input must fail both validation and direct execution.
                    for flight_id in ["aa101", " AA101 ", ""]:
                        argument = {"flight_id": flight_id}
                        valid, reason = choose_flight.validate(argument)
                        record(log, f"VALIDATE {argument!r}: {valid}, {reason}")
                        assert valid is False
                        check_rejection(page, argument, "invalid_" + str(len(flight_id)), log)

                    # Controlled failure fixture: disable an otherwise available button.
                    button = page.locator('button.choose[data-flight="AA101"]')
                    button.evaluate("button => { button.disabled = true; }")
                    try:
                        assert button.is_disabled()
                        check_rejection(page, {"flight_id": "AA101"}, "disabled_button", log)
                    finally:
                        # Re-enable the button so the success test below can use it.
                        button.evaluate("button => { button.disabled = false; }")

                    # Success case: choose AA101 for real.
                    argument = {"flight_id": "AA101"}
                    valid, reason = choose_flight.validate(argument)
                    assert valid is True, reason
                    record(log, "CALL choose_flight.run: " + json.dumps(argument))
                    result = choose_flight.run(page, argument, {})
                    record(log, "RETURN: " + json.dumps(result))
                    # Read the page ourselves instead of trusting the returned dictionary.
                    seat_visible = page.locator("#seatStage").is_visible()
                    results_visible = page.locator("#resultsStage").is_visible()
                    summary = page.locator("#selectedFlightSummary").inner_text().strip()
                    seat_count = page.locator("#seatMap button.seat").count()
                    record(log, f"BROWSER: seat_visible={seat_visible}, results_visible={results_visible}, seats={seat_count}, summary={summary!r}")
                    page.screenshot(path=str(EVIDENCE / "success_AA101.png"), full_page=True)
                    # The seat screen must be open for AA101, with seats loaded.
                    assert result["ok"] is True
                    assert result["data"]["clicked"] is True
                    assert seat_visible is True
                    assert results_visible is False
                    assert seat_count > 0
                    assert summary == "Selected AA101: DCA to BOS, departing 8:10 AM."
                    record(log, "PASS: selecting AA101 opens its seat-selection screen")
                finally:
                    browser.close()
            record(log, "ALL TESTS PASSED")
        except Exception as error:
            record(log, "FAIL: " + repr(error))
            raise  # Keep a nonzero exit status; never disguise a failed test.


if __name__ == "__main__":
    main()
