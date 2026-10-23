"""Team 14: verify the displayed Agent Airways confirmation.

The model supplies only an empty ``argument`` dictionary. Trusted Python
supplies the expected trip in ``context["goal"]``. This module must read the
browser page; it must never click, type, or trust a model success claim.

ASSUMED context schema for Team 14 (the assignment does not specify one):
    {"goal": {
        "route": "DCA → BOS", "date": "2026-10-24", "flight": "AA101",
        "seat": "1A", "name": "Alex Student", "email": "alex@example.com",
        "checked_bag": "No", "priority_boarding": "No", "mock_total": "$129"
    }}
All nine goal values are required, nonempty display strings. The trusted
Python caller constructs this dictionary; the model must not supply it.
Coordinate these keys with the TA when the tool is integrated.
"""

def validate(argument):
    """Return ``(is_valid, reason)``; accept only an empty dictionary."""
    if not isinstance(argument, dict):
        return False, "Argument must be a dictionary."
    if argument:
        return False, "Argument must be an empty dictionary."
    return True, "Argument is valid."


def run(page, argument, context):
    """Compare the real confirmation page with trusted ``context["goal"]``.

    Return exactly ``{"ok": bool, "message": str, "data": {"checks": {...}}}``.
    Each check records the expected value, actual value, and whether it passed.
    The confirmation code is checked for presence; its value is not predetermined.
    """
    checks = {}
    data = {"checks": checks}

    if not isinstance(context, dict) or not isinstance(context.get("goal"), dict):
        return {
            "ok": False,
            "message": "Trusted context must contain a goal dictionary.",
            "data": data,
        }

    goal = context["goal"]
    fields = {
        "route": "Route",
        "date": "Date",
        "flight": "Flight",
        "seat": "Seat",
        "name": "Passenger",
        "email": "Email",
        "checked_bag": "Checked bag",
        "priority_boarding": "Priority boarding",
        "mock_total": "Mock total",
    }
    for field in fields:
        if not isinstance(goal.get(field), str) or not goal[field].strip():
            return {
                "ok": False,
                "message": "Trusted goal is missing a nonempty " + field + " value.",
                "data": data,
            }

    if page is None:
        return {"ok": False, "message": "No browser page was supplied.", "data": data}

    if not page.locator("#confirmationStage").is_visible():
        return {"ok": False, "message": "Final confirmation stage is not visible.", "data": data}

    heading = page.locator("#confirmationStage h2").inner_text().strip()
    code = page.locator("#confirmationCode").inner_text().strip()
    checks["heading"] = {
        "expected": "RESERVATION CONFIRMED",
        "actual": heading,
        "passed": heading == "RESERVATION CONFIRMED",
    }
    checks["code"] = {"expected": "nonempty code", "actual": code, "passed": bool(code)}

    labels = page.locator("#confirmationDetails dt").all_inner_texts()
    values = page.locator("#confirmationDetails dd").all_inner_texts()

    displayed = {}
    for label, value in zip(labels, values):
        displayed[label.strip()] = value.strip()

    failed = []
    for field, label in fields.items():
        actual = displayed.get(label)
        expected = goal[field]
        passed = actual == expected
        checks[field] = {"expected": expected, "actual": actual, "passed": passed}
        if not passed:
            failed.append(field)

    if not checks["heading"]["passed"]:
        failed.append("heading")
    if not checks["code"]["passed"]:
        failed.append("code")
    if failed:
        return {
            "ok": False,
            "message": "Confirmation checks failed: " + ", ".join(failed) + ".",
            "data": data,
        }

    return {"ok": True, "message": "All confirmation details match the trusted goal.", "data": data}
