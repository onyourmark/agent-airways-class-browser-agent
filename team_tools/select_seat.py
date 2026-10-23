"""Team 11: select one available seat and report browser evidence."""

import re
from urllib.parse import urlsplit

from playwright.sync_api import Error


def validate(argument):
    """Check model input without reading or changing the browser."""
    if type(argument) != dict:
        return False, "Argument must be a dictionary containing only seat."
    if set(argument) != {"seat"}:
        return False, "Argument must contain exactly one key: seat."
    seat = argument["seat"]
    if type(seat) != str:
        return False, "Seat must be text, for example 1A."
    if re.fullmatch(r"[1-9][0-9]*[A-Z]", seat) is None:
        return False, "Seat must be a positive row number and one uppercase letter, such as 1A."
    return True, "Seat argument is valid; availability must be checked in the browser."


def run(page, argument, context):
    """Select one seat, without continuing to the passenger stage.

    context is supplied by trusted Python for the common team interface.
    This tool needs no context values. Call validate before dispatching;
    checking again here also protects direct Python callers.
    """
    valid, note = validate(argument)
    if not valid:
        return {"ok": False, "message": note, "data": {}}

    seat = argument["seat"]
    data = {"seat": seat}
    try:
        # The site changes the URL fragment as the user moves between stages.
        url = urlsplit(page.url)
        if (url.scheme != "https" or url.netloc != "onyourmark.github.io"
                or url.path != "/browser-agent-form/travel/"):
            return {"ok": False, "message": "Only the Agent Airways practice page is allowed.", "data": data}

        stage = page.locator("#seatStage:visible")
        if stage.count() != 1:
            return {"ok": False, "message": "The seat-selection stage is not ready or is ambiguous.", "data": data}

        # Validation restricts seat to letters/digits, so it is safe in this selector.
        button = stage.locator('#seatMap button.seat[data-seat="' + seat + '"]:visible')
        if button.count() == 0:
            return {"ok": False, "message": "No visible button matches seat " + seat + ".", "data": data}
        if button.count() != 1:
            return {"ok": False, "message": "More than one visible button matches seat " + seat + ".", "data": data}

        classes = (button.get_attribute("class") or "").split()
        label = button.get_attribute("aria-label") or ""
        if (not button.is_enabled() or button.get_attribute("aria-disabled") == "true"
                or "unavailable" in classes or "unavailable" in label.lower()):
            return {"ok": False, "message": "Seat " + seat + " is disabled or unavailable.", "data": data}

        # Refuse incomplete/ambiguous screens before making a selection.
        message = stage.locator("#seatMessage:visible")
        continue_button = stage.locator("#continueFromSeat:visible")
        if message.count() != 1 or continue_button.count() != 1:
            return {"ok": False, "message": "The seat message or Continue control is missing or ambiguous.", "data": data}

        button.click(timeout=5000)

        # A click alone is not success. Read three separate browser facts.
        selected = stage.locator("#seatMap button.seat[data-seat].selected:visible")
        selected_seat = ""
        if selected.count() == 1:
            selected_seat = selected.get_attribute("data-seat")
        actual_message = message.inner_text().strip()
        continue_enabled = continue_button.is_enabled()
        data["selected_seat"] = selected_seat
        data["seat_message"] = actual_message
        data["continue_enabled"] = continue_enabled

        ok = (selected_seat == seat
              and actual_message == "Selected seat " + seat + "."
              and continue_enabled)
        if ok:
            return {"ok": True, "message": "The browser confirms seat " + seat + " is selected and Continue is enabled.", "data": data}
        return {"ok": False, "message": "The browser did not confirm the requested seat and enabled Continue.", "data": data}
    except Error as error:
        # Timeouts, closed pages and other Playwright errors are honest failures.
        return {"ok": False, "message": "Could not select or verify the seat: " + str(error), "data": data}
