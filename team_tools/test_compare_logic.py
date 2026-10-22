"""Offline tests for check_review_against_goal (no browser needed).

Run from the project folder:  python tests.py
(or just these:  python -m team_tools.test_compare_logic)
"""

import copy
from team_tools.check_review_against_goal import (
    SITE_URL, build_result, validate, evaluate_review, pair_review_values,
)

GOAL = {
    "from": "DCA", "to": "BOS", "date": "2026-11-04",
    "flight_id": "AA101", "seat": "1A",
    "passenger": "Alex Student", "email": "alex@example.com",
    "checked_bag": False, "priority_boarding": False,
}

ROWS = [
    ("Route", "DCA → BOS"), ("Date", "2026-11-04"), ("Flight", "AA101"),
    ("Seat", "1A"), ("Passenger", "Alex Student"),
    ("Email", "alex@example.com"), ("Checked bag", "No"),
    ("Priority boarding", "No"), ("Mock total", "$123.00"),
]

CHECK_NAMES = ["route", "date", "flight_id", "seat", "passenger",
               "email", "checked_bag", "priority_boarding"]


def make_facts(rows=ROWS, url=SITE_URL, stage_visible=True):
    """Build the same facts read_page_facts() reads from the browser."""
    labels = []
    values = []
    for label, value in rows:
        labels.append(label)
        values.append(value)
    if not stage_visible:
        labels = []
        values = []
    return {"url": url, "stage_visible": stage_visible,
            "labels": labels, "values": values}


def actual_values():
    return pair_review_values(make_facts()["labels"], make_facts()["values"])


# --- reading ----------------------------------------------------------------
def test_review_pairing_reads_all_fields():
    actual = actual_values()
    assert actual["route"] == "DCA → BOS"
    assert actual["checked_bag"] == "No"
    assert actual["mock_total"] == "$123.00"


# --- comparison -------------------------------------------------------------
def test_review_exact_match():
    r = build_result(actual_values(), GOAL)
    assert r["ok"] is True, r
    for name in CHECK_NAMES:
        assert r["data"]["checks"][name] is True
    assert r["data"]["mismatches"] == []
    assert r["data"]["mock_total_observed"] == "$123.00"


def test_review_wrong_seat():
    goal = copy.deepcopy(GOAL)
    goal["seat"] = "9F"
    r = build_result(actual_values(), goal)
    assert r["ok"] is False
    assert r["data"]["checks"]["seat"] is False
    assert r["data"]["mismatches"] == ["seat"]
    assert r["data"]["actual"]["seat"] == "1A"


def test_review_wrong_email():
    goal = copy.deepcopy(GOAL)
    goal["email"] = "other@example.com"
    r = build_result(actual_values(), goal)
    assert r["ok"] is False
    assert r["data"]["mismatches"] == ["email"]


def test_review_bag_mismatch_and_unreadable_value():
    goal = copy.deepcopy(GOAL)
    goal["checked_bag"] = True
    assert build_result(actual_values(), goal)["data"]["mismatches"] == ["checked_bag"]
    bad = actual_values()
    bad["priority_boarding"] = "Maybe"
    assert build_result(bad, GOAL)["data"]["mismatches"] == ["priority_boarding"]


def test_review_missing_field_is_mismatch_not_guess():
    partial = actual_values()
    del partial["seat"]
    r = build_result(partial, GOAL)
    assert r["ok"] is False
    assert r["data"]["mismatches"] == ["seat"]


def test_review_formatting_differences_tolerated():
    a = actual_values()
    a["route"] = "dca -> bos"
    a["email"] = "Alex@Example.com "
    assert build_result(a, GOAL)["ok"] is True


# --- validate ---------------------------------------------------------------
def test_review_validate():
    assert validate({})[0] is True
    assert validate({"seat": "1A"})[0] is False
    assert validate(None)[0] is False
    assert validate("x")[0] is False


# --- full decision (everything run() does after reading the page) -----------
def test_review_evaluate_normal():
    r = evaluate_review({}, {"goal": GOAL}, make_facts())
    assert r["ok"] is True, r


def test_review_evaluate_wrong_seat():
    goal = copy.deepcopy(GOAL)
    goal["seat"] = "9F"
    r = evaluate_review({}, {"goal": goal}, make_facts())
    assert r["ok"] is False
    assert r["data"]["mismatches"] == ["seat"]


def test_review_evaluate_rejects_model_argument():
    r = evaluate_review({"goal": GOAL}, {"goal": GOAL}, make_facts())
    assert r["ok"] is False
    assert r["data"]["checks"] == {}


def test_review_evaluate_incomplete_goal():
    goal = copy.deepcopy(GOAL)
    del goal["seat"]
    r = evaluate_review({}, {"goal": goal}, make_facts())
    assert r["ok"] is False
    assert "seat" in r["message"]


def test_review_evaluate_no_goal():
    assert evaluate_review({}, {}, make_facts())["ok"] is False
    assert evaluate_review({}, None, make_facts())["ok"] is False


def test_review_evaluate_before_review_stage():
    r = evaluate_review({}, {"goal": GOAL}, make_facts(stage_visible=False))
    assert r["ok"] is False
    assert "review" in r["message"].lower()


def test_review_evaluate_wrong_site():
    r = evaluate_review({}, {"goal": GOAL}, make_facts(url="https://example.com/"))
    assert r["ok"] is False
    assert "approved" in r["message"]


def test_review_evaluate_unreadable_summary():
    r = evaluate_review({}, {"goal": GOAL}, make_facts(rows=[]))
    assert r["ok"] is False


REVIEW_TESTS = [
    test_review_pairing_reads_all_fields,
    test_review_exact_match,
    test_review_wrong_seat,
    test_review_wrong_email,
    test_review_bag_mismatch_and_unreadable_value,
    test_review_missing_field_is_mismatch_not_guess,
    test_review_formatting_differences_tolerated,
    test_review_validate,
    test_review_evaluate_normal,
    test_review_evaluate_wrong_seat,
    test_review_evaluate_rejects_model_argument,
    test_review_evaluate_incomplete_goal,
    test_review_evaluate_no_goal,
    test_review_evaluate_before_review_stage,
    test_review_evaluate_wrong_site,
    test_review_evaluate_unreadable_summary,
]


def test_review_checker_all():
    """One entry for tests.py: runs every check_review_against_goal test."""
    for test_function in REVIEW_TESTS:
        test_function()


if __name__ == "__main__":
    for test_function in REVIEW_TESTS:
        test_function()
        print("PASS:", test_function.__name__)
