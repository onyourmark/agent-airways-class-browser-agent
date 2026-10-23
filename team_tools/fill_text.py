"""Team 01: fill a permitted field and verify its value."""

from datetime import date
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError


FIELD_IDS = {
    "departure_date": "departureDate",
    "full_name": "passengerName",
    "email": "passengerEmail",
}


def validate(argument):
    """Check arguments before accessing the browser."""
    if not isinstance(argument, dict):
        return False, "Argument must be a dictionary."

    if set(argument) != {"field", "value"}:
        return False, "Provide exactly field and value."

    field = argument["field"]
    value = argument["value"]

    if not isinstance(field, str) or field not in FIELD_IDS:
        return False, "Allowed fields: departure_date, full_name, email."

    if not isinstance(value, str) or not value.strip():
        return False, "Value must be nonempty text."

    if field == "departure_date":
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError:
            return False, "Date must be a valid date in YYYY-MM-DD format."

        if parsed_date.isoformat() != value:
            return False, "Date must use exactly YYYY-MM-DD format."

    return True, "Argument is valid."


def run(page, argument, context):
    """Fill one field; context is reserved for the shared agent."""
    allowed, message = validate(argument)
    if not allowed:
        return {"ok": False, "message": message, "data": {}}

    field = argument["field"]
    requested_value = argument["value"]

    data = {
        "field": field,
        "requested_value": requested_value,
        "action_attempted": False,
    }

    control = None

    try:
        # Restrict the tool to the practice website.
        data["url"] = page.url
        url = urlsplit(data["url"])

        if (
            url.scheme != "https"
            or url.netloc != "onyourmark.github.io"
            or url.path != "/browser-agent-form/travel/"
        ):
            return {
                "ok": False,
                "message": "Open the Agent Airways practice page first.",
                "data": data,
            }

        control = page.locator("#" + FIELD_IDS[field])
        count = control.count()

        if count != 1:
            return {
                "ok": False,
                "message": "Expected exactly one field; found " + str(count) + ".",
                "data": data,
            }

        if not control.is_visible():
            return {
                "ok": False,
                "message": "Field is hidden. Manually reach the correct screen.",
                "data": data,
            }

        if not control.is_enabled() or not control.is_editable():
            return {
                "ok": False,
                "message": "Field is disabled or not editable.",
                "data": data,
            }

        data["before_value"] = control.input_value(timeout=5000)

        data["action_attempted"] = True
        control.fill(requested_value, timeout=5000)

        # Read the actual browser value before reporting success.
        actual_value = control.input_value(timeout=5000)
        data["actual_value"] = actual_value

        if actual_value != requested_value:
            return {
                "ok": False,
                "message": "Read-back value does not match the requested value.",
                "data": data,
            }

        return {
            "ok": True,
            "message": "Field filled and exact value verified.",
            "data": data,
        }

    except PlaywrightError as error:
        # An error does not guarantee that the field stayed unchanged.
        if data["action_attempted"] and control is not None:
            try:
                data["actual_value"] = control.input_value(timeout=1000)
            except PlaywrightError:
                data["read_back_error"] = (
                    "Could not read the field after the browser error."
                )

        return {
            "ok": False,
            "message": "Browser operation failed: " + str(error),
            "data": data,
        }