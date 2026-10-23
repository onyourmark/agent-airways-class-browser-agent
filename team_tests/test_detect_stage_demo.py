"""Automated smoke checks for the manual script; these are not student demos."""

import json
import subprocess
import sys
from pathlib import Path
from playwright.sync_api import expect
import browser_tools
from team_tests.demo_detect_stage import demonstrate

prompt_number = 0


def navigate_and_continue(prompt):
    """Prepare real browser stages and simulate Enter only for this test."""
    global prompt_number
    page = browser_tools.page
    number = prompt_number
    prompt_number += 1
    if number == 0 or number == 1:
        # First verify search, then deliberately fail the results checkpoint.
        return ""
    if number == 2:
        page.locator("#fromAirport").select_option("DCA")
        page.locator("#toAirport").select_option("BOS")
        page.locator("#searchFlights").click()
        expect(page.get_by_role("button", name="Choose AA101", exact=True)).to_be_visible()
    elif number == 3:
        page.get_by_role("button", name="Choose AA101", exact=True).click()
    elif number == 4:
        page.locator('#seatMap button[data-seat="1A"]').click()
        page.locator("#continueFromSeat").click()
    elif number == 5:
        page.locator("#passengerName").fill("Alex Student")
        page.locator("#passengerEmail").fill("alex@example.com")
        page.locator("#continueToReview").click()
    elif number == 6:
        page.locator("#confirmDetails").check()
        page.locator("#confirmReservation").click()
    else:
        raise AssertionError("Unexpected extra prompt: " + str(number))
    return ""


def quit_input(prompt):
    return "q"


def main():
    global prompt_number
    prompt_number = 0
    records = []
    browser_tools.start_browser()
    try:
        browser_tools.open_site()
        page = browser_tools.page
        page.wait_for_load_state("load")
        report = demonstrate(page, navigate_and_continue)
        assert report["completed"] is True and len(report["attempts"]) == 7
        assert report["attempts"][1]["passed"] is False
        assert report["attempts"][1]["expected_stage"] == "results"
        assert report["attempts"][1]["returned"]["data"]["stage"] == "search"
        passed_stages = []
        for attempt in report["attempts"]:
            if attempt["passed"]:
                passed_stages.append(attempt["expected_stage"])
        assert passed_stages == ["search", "results", "seat", "passenger", "review", "confirmation"]
        assert page.locator("#confirmationStage").is_visible()
        records.append({"case": "six stages complete after a wrong-stage retry", "result": "PASS",
                        "passed_stages": passed_stages, "attempts": 7, "retained_failed_attempts": 1})

        report = demonstrate(page, quit_input)
        assert report == {"completed": False, "attempts": []}
        records.append({"case": "q stops without false completion", "result": "PASS"})

        page.locator("#resetTrip").click()
        expect(page.locator("#searchStage")).to_be_visible()
        first_answer = [""]

        def end_after_search(prompt):
            if first_answer:
                return first_answer.pop()
            raise EOFError

        report = demonstrate(page, end_after_search)
        assert report["completed"] is False and len(report["attempts"]) == 1
        assert report["attempts"][0]["passed"] is True
        records.append({"case": "end-of-input preserves the completed search attempt", "result": "PASS"})

        closed_page = browser_tools.browser.new_page()
        closed_page.close()
        answers = ["", "q"]

        def try_closed_page(prompt):
            return answers.pop(0)

        report = demonstrate(closed_page, try_closed_page)
        assert report["completed"] is False and len(report["attempts"]) == 1
        attempt = report["attempts"][0]
        assert attempt["passed"] is False and attempt["browser_error"] != ""
        assert attempt["call"] is None and attempt["returned"] is None
        records.append({"case": "closed page records the read failure and allows q", "result": "PASS"})
    finally:
        browser_tools.close_browser()

    # Exercise the actual startup, terminal input, cleanup, and report-writing path.
    # Use a separate filename so this test cannot replace a student's report.
    root = Path(__file__).resolve().parents[1]
    command = "from team_tests.demo_detect_stage import main\nraise SystemExit(0 if main('manual-demo-smoke-cli-step6.json') else 1)"
    completed = subprocess.run([sys.executable, "-c", command], input="q\n",
                               capture_output=True, text=True, cwd=root, timeout=45)
    assert completed.returncode == 1, completed.stdout + completed.stderr
    saved = json.loads((root / "artifacts/manual-demo-smoke-cli-step6.json").read_text(encoding="utf-8"))
    assert saved == {"step": 6, "interaction": "terminal prompts", "completed": False, "attempts": []}
    assert "Stopped early" in completed.stdout and "Report saved to:" in completed.stdout
    records.append({"case": "startup and q save an incomplete report and exit 1", "result": "PASS"})

    evidence = {"step": 6, "kind": "automated smoke test with scripted input",
                "student_manual_demonstration": False, "result": "PASS", "cases": records}
    (root / "artifacts/manual-demo-smoke-step6.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    print("All 5 manual-script smoke checks passed (automated, not a student demonstration).")


if __name__ == "__main__":
    main()
