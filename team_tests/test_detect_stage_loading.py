"""Step 3: read real loading visibility while controlling the website's timer."""

import json
from pathlib import Path
from time import time
from playwright.sync_api import expect
import browser_tools
from team_tools.detect_stage import run

records = []


def record(case, result, evidence):
    records.append({"case": case, "returned": result, "browser_evidence": evidence, "result": "PASS"})
    print("PASS:", case, json.dumps(result), flush=True)


def check_loading(expected):
    page = browser_tools.page
    before_html = page.content()
    before_url = page.url
    result = run(page, {}, {})
    # Independently inspect real DOM visibility, not just the tool's Boolean.
    assert page.locator("#resultsStage").is_visible()
    actual = page.locator("#loadingFlights").is_visible()
    assert actual is expected
    assert result["ok"] is True and result["data"]["stage"] == "results"
    assert result["data"]["loading"] is actual
    assert page.content() == before_html and page.url == before_url
    record("results loading=" + str(expected), result, {"loading_indicator_visible": actual, "url": page.url, "page_unchanged": True})


def main():
    browser_tools.start_browser()
    try:
        page = browser_tools.page
        # Freeze application time after load so the 1.2s loading state cannot
        # disappear halfway through a check on a slow machine.
        initial_time = time()
        page.clock.install(time=initial_time)
        browser_tools.open_site()
        page.wait_for_load_state("load")
        page.clock.pause_at(initial_time + 60)

        page.locator("#fromAirport").select_option("DCA")
        page.locator("#toAirport").select_option("BOS")
        page.locator("#searchFlights").click()
        check_loading(True)

        # Advance the site's own timer; its real callback renders the flights.
        page.clock.run_for(1500)
        expect(page.get_by_role("button", name="Choose AA101", exact=True)).to_be_visible()
        check_loading(False)

        # These two malformed-page fixtures must fail instead of inventing False.
        indicator = page.locator("#loadingFlights")
        indicator.evaluate("element => element.after(element.cloneNode(true))")
        result = run(page, {}, {})
        assert page.locator("#loadingFlights").count() == 2
        assert result["ok"] is False and result["data"] == {}
        record("duplicate loading indicators rejected", result, {"indicator_count": 2})

        page.locator("#loadingFlights").evaluate_all("elements => { for (const element of elements) element.remove(); }")
        result = run(page, {}, {})
        assert page.locator("#loadingFlights").count() == 0
        assert page.locator("#resultsStage").is_visible()
        assert result["ok"] is False and result["data"] == {}
        record("missing loading indicator rejected", result, {"indicator_count": 0, "results_visible": True})
    finally:
        browser_tools.close_browser()

    destination = Path(__file__).resolve().parents[1] / "artifacts"
    destination.mkdir(exist_ok=True)
    report = {"step": 3, "result": "PASS", "application_clock_controlled": True, "cases": records}
    (destination / "loading-step3.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("All 4 loading-state browser checks passed.")


if __name__ == "__main__":
    main()
