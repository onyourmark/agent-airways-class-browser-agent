"""Step 5: observe passenger, review, and confirmation on the practice site."""

import json
from pathlib import Path
from playwright.sync_api import expect
import browser_tools
from team_tools.detect_stage import run


def read_form_values(page):
    """Read live values, which page.content() alone does not always capture."""
    values = {}
    for field in ["fromAirport", "toAirport", "departureDate", "passengers",
                  "passengerName", "passengerEmail"]:
        values[field] = page.locator("#" + field).input_value()
    for field in ["checkedBag", "priorityBoarding", "confirmDetails"]:
        values[field] = page.locator("#" + field).is_checked()
    return values


def check_stage(page, stage, expected_heading, case):
    before_url = page.url
    before_html = page.content()
    before_values = read_form_values(page)
    result = run(page, {}, {})

    # Find the visible section independently of the tool's six-ID loop.
    visible_section = page.locator("section.stage:visible")
    visible_count = visible_section.count()
    assert visible_count == 1
    actual_id = visible_section.get_attribute("id")
    heading = visible_section.locator("h2").inner_text()
    actual_loading = page.locator("#loadingFlights").is_visible()
    assert actual_id == stage + "Stage"
    assert heading == expected_heading
    assert actual_loading is False
    assert result["ok"] is True
    assert result["data"] == {"stage": stage, "loading": False}

    # Observation must leave the URL, DOM, field values, and checkboxes unchanged.
    after_values = read_form_values(page)
    assert page.url == before_url and page.content() == before_html
    assert after_values == before_values
    evidence = {"visible_stage_count": visible_count, "visible_stage_id": actual_id,
                "heading": heading, "visible_text": visible_section.inner_text(),
                "loading_indicator_visible": actual_loading, "url": page.url,
                "form_values": after_values, "page_unchanged": True}
    record = {"case": case, "call": "run(page, {}, {})", "returned": result,
              "browser_evidence": evidence, "result": "PASS"}
    print("PASS:", case, json.dumps(record), flush=True)
    return record


def main():
    records = []
    browser_tools.start_browser()
    try:
        browser_tools.open_site()
        page = browser_tools.page
        page.wait_for_load_state("load")

        # These are test setup actions on the fictional site, not new team tools.
        page.locator("#fromAirport").select_option("DCA")
        page.locator("#toAirport").select_option("BOS")
        page.locator("#passengers").select_option("1")
        assert page.locator("#departureDate").input_value() != ""
        page.locator("#searchFlights").click()
        choose = page.get_by_role("button", name="Choose AA101", exact=True)
        expect(choose).to_be_visible()
        choose.click()
        page.locator('#seatMap button[data-seat="1A"]').click()
        page.locator("#continueFromSeat").click()
        expect(page.locator("#passengerStage")).to_be_visible()

        # Synthetic passenger data also lets us check live form values are kept.
        page.locator("#passengerName").fill("Alex Student")
        page.locator("#passengerEmail").fill("alex@example.com")
        page.locator("#checkedBag").check()
        page.locator("#priorityBoarding").uncheck()
        records.append(check_stage(page, "passenger", "4. Passenger information",
                                   "passenger stage is visible and unchanged"))

        page.locator("#continueToReview").click()
        expect(page.locator("#reviewStage")).to_be_visible()
        expect(page.locator("#reviewCard")).to_contain_text("Alex Student")
        expect(page.locator("#confirmReservation")).to_be_disabled()
        records.append(check_stage(page, "review", "5. Review the reservation",
                                   "review stage is visible and unchanged"))

        # A misleading URL must not make the tool announce premature confirmation.
        page.evaluate("history.replaceState(history.state, '', '#confirmation')")
        assert page.url.endswith("#confirmation")
        assert not page.locator("#confirmationStage").is_visible()
        records.append(check_stage(page, "review", "5. Review the reservation",
                                   "review stays review despite confirmation hash"))
        page.evaluate("history.replaceState(history.state, '', '#review')")

        # Complete only the practice site's pretend reservation using its controls.
        page.locator("#confirmDetails").check()
        page.locator("#confirmReservation").click()
        expect(page.locator("#confirmationStage")).to_be_visible()
        expect(page.locator("#confirmationCode")).to_have_text("LAB2026")
        expect(page.locator("#confirmationDetails")).to_contain_text("Alex Student")
        records.append(check_stage(page, "confirmation", "RESERVATION CONFIRMED",
                                   "confirmation stage is visible and unchanged"))
    finally:
        browser_tools.close_browser()

    # An assertion failure exits before a successful report can be written.
    destination = Path(__file__).resolve().parents[1] / "artifacts"
    destination.mkdir(exist_ok=True)
    report = {"step": 5, "result": "PASS", "cases": records}
    (destination / "later-stages-step5.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("All 4 later-stage browser checks passed.")


if __name__ == "__main__":
    main()
