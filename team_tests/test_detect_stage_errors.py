"""Step 4: check normal reads, closed pages, and a stopped Playwright driver."""

import json
from pathlib import Path
from playwright.sync_api import Error as PlaywrightError
import browser_tools
from team_tools.detect_stage import run


def record(records, case, result, evidence):
    call = "run(page, {}, {})"
    records.append({"case": case, "call": call, "returned": result,
                    "browser_evidence": evidence, "result": "PASS"})
    print("PASS:", case, call, json.dumps(result), json.dumps(evidence), flush=True)


def main():
    records = []
    driver_stopped = False
    browser_tools.start_browser()
    try:
        browser_tools.open_site()
        page = browser_tools.page
        page.wait_for_load_state("load")
        before_url = page.url
        before_html = page.content()
        result = run(page, {}, {})
        # Independently read the real page and confirm the tool changed nothing.
        assert page.locator("#searchStage").is_visible()
        heading = page.locator("#searchStage h2").inner_text()
        assert result["ok"] is True
        assert result["data"] == {"stage": "search", "loading": False}
        assert page.url == before_url and page.content() == before_html
        record(records, "normal search observation", result,
               {"search_visible": True, "heading": heading, "url": page.url,
                "page_unchanged": True})

        # Close a separate tab so the original practice page remains available.
        closed_page = browser_tools.browser.new_page()
        closed_page.close()
        result = run(closed_page, {}, {})
        assert closed_page.is_closed()
        assert result["ok"] is False and result["data"] == {}
        assert "No open browser page" in result["message"]
        record(records, "closed page rejected", result, {"page_is_closed": True})

        # Stop the real driver, keeping the old Page object. Its cached URL and
        # is_closed flag do not guarantee that browser reads will still work.
        browser_tools.playwright.stop()
        driver_stopped = True
        browser_error = ""
        try:
            page.title()
        except PlaywrightError as error:
            browser_error = str(error)
        assert browser_error != "", "The independent browser read must fail."

        result = run(page, {}, {})
        assert result["ok"] is False and result["data"] == {}
        assert "Could not inspect the browser page:" in result["message"]
        record(records, "stopped driver returns a failure observation", result,
               {"driver_stopped": True, "page_is_closed": page.is_closed(),
                "independent_title_read_error": browser_error})
    finally:
        # close_browser() cannot send browser.close() to an already stopped driver.
        if not driver_stopped:
            browser_tools.close_browser()

    # Save PASS evidence only after every independent assertion has succeeded.
    destination = Path(__file__).resolve().parents[1] / "artifacts"
    destination.mkdir(exist_ok=True)
    report = {"step": 4, "result": "PASS", "cases": records}
    (destination / "browser-errors-step4.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print("All 3 browser-error checks passed.")


if __name__ == "__main__":
    main()
