"""
Team 02 tool: set_checkbox

Checks or unchecks one checkbox on the Agent Airways practice site.
Allowed checkboxes: checked_bag, priority_boarding, confirm_details.

Example argument: {"field": "checked_bag", "checked": True}
"""

# Maps the field names the agent is allowed to use
# to the real HTML ids on the practice website.
ALLOWED_FIELDS = {
    "checked_bag": "checkedBag",
    "priority_boarding": "priorityBoarding",
    "confirm_details": "confirmDetails",
}


def validate(argument):
    # The argument must be a dictionary, like {"field": "checked_bag", "checked": True}
    if not isinstance(argument, dict):
        return False, "Argument must be a dictionary."

    # Only "field" and "checked" are allowed. Anything extra is rejected.
    for key in argument:
        if key != "field" and key != "checked":
            return False, "Unexpected key: " + str(key)

    # Both keys must be present.
    if "field" not in argument:
        return False, "Missing 'field'."
    if "checked" not in argument:
        return False, "Missing 'checked'."

    # The field must be one of the three allowed checkboxes.
    field = argument["field"]
    if field not in ALLOWED_FIELDS:
        return False, "Unknown checkbox: " + str(field) + ". Allowed: checked_bag, priority_boarding, confirm_details."

    # checked must be a real True or False, not text like "true" or "yes".
    if not isinstance(argument["checked"], bool):
        return False, "'checked' must be True or False, not " + repr(argument["checked"]) + "."

    return True, "Argument is valid."


def run(page, argument, context):
    # Safety first: never touch the browser if the argument is bad.
    is_valid, reason = validate(argument)
    if not is_valid:
        return {"ok": False, "message": "Rejected before acting: " + reason, "data": {}}

    field = argument["field"]
    wanted = argument["checked"]
    html_id = ALLOWED_FIELDS[field]

    # Note: confirm_details is just a checkbox on the review page.
    # Checking it does NOT mean a person approved the reservation.
    # The context argument is not used by this tool.

    box = page.locator("#" + html_id)

    # 1. Make sure the checkbox is actually on the current screen.
    if box.count() == 0:
        return {
            "ok": False,
            "message": "Checkbox '" + field + "' is not on this page. You may be on the wrong screen.",
            "data": {"field": field},
        }
    if not box.is_visible():
        return {
            "ok": False,
            "message": "Checkbox '" + field + "' exists but is not visible on this screen.",
            "data": {"field": field},
        }
    if not box.is_enabled():
        return {
            "ok": False,
            "message": "Checkbox '" + field + "' is disabled and cannot be changed.",
            "data": {"field": field},
        }

    # 2. Remember what it looked like before we act.
    before = box.is_checked()

    # 3. Change it only if it is not already in the wanted state.
    try:
        if wanted and not before:
            box.check()
        elif not wanted and before:
            box.uncheck()
    except Exception as error:
        return {
            "ok": False,
            "message": "Playwright could not change '" + field + "': " + str(error),
            "data": {"field": field, "before": before},
        }

    # 4. Read the real state from the browser afterwards.
    after = box.is_checked()

    # 5. Success only if the browser shows what was requested.
    data = {"field": field, "requested": wanted, "before": before, "after": after}
    if after == wanted:
        return {
            "ok": True,
            "message": "Checkbox '" + field + "' is now " + str(after) + " (read back from the page).",
            "data": data,
        }
    return {
        "ok": False,
        "message": "Checkbox '" + field + "' should be " + str(wanted) + " but the page shows " + str(after) + ".",
        "data": data,
    }
