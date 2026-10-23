"""Guide a person through six detect_stage checks in the Playwright browser."""

import json
from pathlib import Path
from playwright.sync_api import Error as PlaywrightError
import browser_tools
from team_tools.detect_stage import run


STEPS = [
    ("search", "Leave the opening Search for a flight screen visible."),
    ("results", "Choose From=DCA, To=BOS, keep the supplied date, and click Search flights. "
     "Wait for the flight cards. Do not choose a flight yet."),
    ("seat", "Click Choose AA101. Leave the seat map visible."),
    ("passenger", "Choose seat 1A and click Continue. Leave Passenger information visible."),
    ("review", "Enter Alex Student and alex@example.com, then click Continue to review. "
     "Stop before confirming the pretend reservation."),
    ("confirmation", "On this practice site, check the details box and click Confirm reservation. "
     "Leave RESERVATION CONFIRMED visible."),
]


def check_stage(page, expected_stage):
    """Call the tool and separately check the actual visible browser section."""
    attempt = {"expected_stage": expected_stage, "call": None, "returned": None,
               "browser_evidence": {}, "passed": False}
    try:
        # input() pauses Python. A browser read processes events from manual clicks.
        page.title()
        before_url = page.url
        before_html = page.content()
        attempt["call"] = "run(page, {}, {})"
        result = run(page, {}, {})
        attempt["returned"] = result

        visible = page.locator("section.stage:visible")
        count = visible.count()
        section_id = ""
        heading = ""
        if count == 1:
            section_id = visible.get_attribute("id")
            heading = visible.locator("h2").inner_text()
        loading = page.locator("#loadingFlights").is_visible()
        unchanged = page.url == before_url and page.content() == before_html
        attempt["browser_evidence"] = {
            "url": page.url, "visible_stage_count": count,
            "visible_stage_id": section_id, "heading": heading,
            "loading_indicator_visible": loading, "url_and_html_unchanged": unchanged,
        }
        attempt["passed"] = (
            result["ok"] is True and count == 1
            and section_id == expected_stage + "Stage"
            and result["data"] == {"stage": expected_stage, "loading": loading}
            and unchanged
        )
    except PlaywrightError as error:
        attempt["browser_error"] = str(error)
    return attempt


def demonstrate(page, read_input=input):
    """Use terminal input by default; automated tests supply scripted responses."""
    report = {"completed": False, "attempts": []}
    try:
        for stage, instructions in STEPS:
            print("\nNext stage:", stage, "\n" + instructions, flush=True)
            while True:
                response = read_input("Press Enter to check, or q to stop: ").strip().lower()
                if response == "q":
                    print("Stopped early. The demonstration is incomplete.")
                    return report
                if response != "":
                    print("Use Enter to check the page, or q to stop.")
                    continue
                attempt = check_stage(page, stage)
                report["attempts"].append(attempt)
                print(json.dumps(attempt, indent=2), flush=True)
                if attempt["passed"]:
                    print("PASS:", stage, flush=True)
                    break
                print("FAIL: expected", stage, "- check the browser and retry. "
                      "If the browser is closed, use q and restart.", flush=True)
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended. The demonstration is incomplete.")
        return report
    report["completed"] = True
    print("Verified all six stages. Any earlier failed attempts remain in the report.")
    return report


def main(report_name="manual-stage-demo.json"):
    report = {"step": 6, "interaction": "terminal prompts",
              "completed": False, "attempts": []}
    print("Use only the Chromium window opened by this script. Keep this terminal open.")
    try:
        browser_tools.start_browser()
        browser_tools.open_site()
        browser_tools.page.wait_for_load_state("load")
        report.update(demonstrate(browser_tools.page))
    except (EOFError, KeyboardInterrupt):
        print("\nStopped before the demonstration finished.")
    except PlaywrightError as error:
        report["browser_error"] = str(error)
        print("Browser error:", error)
    except ValueError as error:
        # open_site() reports an HTTP failure as ValueError.
        report["site_error"] = str(error)
        print("Site error:", error)
    finally:
        try:
            browser_tools.close_browser()
        except PlaywrightError as error:
            report["cleanup_error"] = str(error)

    destination = Path(__file__).resolve().parents[1] / "artifacts"
    destination.mkdir(exist_ok=True)
    path = destination / report_name
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Report saved to:", path)
    return report["completed"]


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
