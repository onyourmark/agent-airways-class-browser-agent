"""Step 2: independently check stage observations in a real Chromium browser."""

import json
from pathlib import Path
from playwright.sync_api import expect
import browser_tools
from team_tools.detect_stage import run

records = []


def record(case, result, evidence):
    records.append({"case": case, "returned": result, "browser_evidence": evidence, "result": "PASS"})
    print("PASS:", case, json.dumps(result), flush=True)


def check_stage(stage, selector):
    page = browser_tools.page
    before_url = page.url
    before_html = page.content()
    result = run(page, {}, {})
    # Read the real page separately; do not accept only the tool's own answer.
    assert page.locator(selector).is_visible()
    heading = page.locator(selector + " h2").inner_text()
    assert result["ok"] is True and result["data"] == {"stage": stage, "loading": False}
    assert page.url == before_url and page.content() == before_html
    record(stage + " is visible; observation is read-only", result, {"selector": selector, "heading": heading, "url": page.url})


def main():
    browser_tools.start_browser()
    try:
        browser_tools.open_site()
        page = browser_tools.page
        page.wait_for_load_state("load")
        check_stage("search", "#searchStage")

        # Test setup deliberately changes the hash without changing the screen.
        page.evaluate("history.replaceState({}, '', '#review')")
        check_stage("search", "#searchStage")
        assert page.url.endswith("#review")

        page.locator("#fromAirport").select_option("DCA")
        page.locator("#toAirport").select_option("BOS")
        page.locator("#searchFlights").click()
        choose = page.get_by_role("button", name="Choose AA101", exact=True)
        expect(choose).to_be_visible()
        choose.click()
        check_stage("seat", "#seatStage")

        # Setup creates an ambiguous page. The tool must not guess a stage.
        page.locator("#searchStage").evaluate("element => element.classList.remove('hidden')")
        result = run(page, {}, {})
        assert page.locator("#searchStage").is_visible() and page.locator("#seatStage").is_visible()
        assert result["ok"] is False and result["data"] == {}
        record("two visible stages rejected", result, {"search_visible": True, "seat_visible": True})

        page.locator("#searchStage").evaluate("element => element.classList.add('hidden')")
        page.locator("#seatStage").evaluate("element => element.classList.add('hidden')")
        result = run(page, {}, {})
        visible_count = page.locator("section.stage").filter(visible=True).count()
        assert visible_count == 0 and result["ok"] is False and result["data"] == {}
        record("no visible stage rejected", result, {"visible_stage_count": visible_count})

        page.goto("about:blank")
        result = run(page, {}, {})
        assert page.url == "about:blank" and result["ok"] is False and result["data"] == {}
        record("wrong site rejected", result, {"url": page.url})

        result = run(None, {"stage": "seat"}, {})
        assert result["ok"] is False and "empty dictionary" in result["message"]
        record("invalid argument rejected before inspecting a page", result, {"page": None})
        result = run(None, {}, {})
        assert result["ok"] is False and result["data"] == {}
        record("missing page rejected", result, {"page": None})
    finally:
        browser_tools.close_browser()

    # This is evidence from this run. An assertion failure exits before saving PASS.
    destination = Path(__file__).resolve().parents[1] / "artifacts"
    destination.mkdir(exist_ok=True)
    report = {"step": 2, "result": "PASS", "cases": records}
    (destination / "stage-detection-step2.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("All 8 stage-detection browser checks passed.")


if __name__ == "__main__":
    main()
