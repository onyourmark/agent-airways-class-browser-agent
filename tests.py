"""Fast offline checks for the small public starter.

No model, Internet, or browser is required. The later evaluation
laboratory will add live browser tests and end-to-end task cases.
"""

from browser_agent import parse_model_reply, validate_proposal, check_goal
from browser_tools import SITE_URL
from team_tools.test_compare_logic import test_review_checker_all


def run_test(name, test_function):
    test_function()
    print("PASS:", name)


def test_good_json():
    parsed, note = parse_model_reply('{"action": "open_site", "argument": ""}')
    assert parsed["action"] == "open_site"
    assert note == "Parsing succeeded."


def test_bad_json():
    parsed, note = parse_model_reply("{action: open_site}")
    assert parsed is None
    assert "PARSER ERROR" in note


def test_disallowed_action():
    valid, note = validate_proposal({"action": "delete_files", "argument": ""})
    assert valid is False


def test_missing_argument():
    valid, note = validate_proposal({"action": "open_site"})
    assert valid is False


def test_good_action():
    valid, note = validate_proposal({"action": "read_page", "argument": ""})
    assert valid is True


def test_bad_argument():
    valid, note = validate_proposal({"action": "open_site", "argument": "https://example.com"})
    assert valid is False


def test_good_goal_evidence():
    observed = {
        "url": SITE_URL,
        "title": "Agent Airways Lab",
        "heading": "Agent Airways",
    }
    valid, note = check_goal(observed)
    assert valid is True


def test_premature_done_rejected():
    observed = {
        "url": "about:blank",
        "title": "",
        "heading": "",
    }
    valid, note = check_goal(observed)
    assert valid is False


def test_misleading_title_rejected():
    observed = {
        "url": "https://example.com/",
        "title": "Agent Airways Lab",
        "heading": "Agent Airways",
    }
    valid, note = check_goal(observed)
    assert valid is False


if __name__ == "__main__":
    run_test("valid JSON", test_good_json)
    run_test("bad JSON", test_bad_json)
    run_test("unknown tool rejected", test_disallowed_action)
    run_test("missing argument rejected", test_missing_argument)
    run_test("valid tool accepted", test_good_action)
    run_test("bad tool argument rejected", test_bad_argument)
    run_test("goal accepts exact browser evidence", test_good_goal_evidence)
    run_test("premature done rejected", test_premature_done_rejected)
    run_test("misleading title rejected", test_misleading_title_rejected)
    run_test("check_review_against_goal (16 checks)", test_review_checker_all)
    print("All 10 offline checks passed.")
