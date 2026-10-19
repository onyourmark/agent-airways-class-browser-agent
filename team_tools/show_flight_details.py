"""Team 07: show_flight_details tool.

Team members: Aravind Sundaravadivelu, Shubhi Singhal
Assigned tool: show_flight_details
File path: team_tools/show_flight_details.py

Job:
Open the Flight details dialog for one offered flight, read its details
(route, time, stops, price), confirm dialog closure, and leave the flight unselected.
"""


def validate(argument):
    """Validate the argument dictionary before touching the browser."""
    # The argument must be a Python dictionary
    if type(argument) != dict:
        return False, "The argument must be a dictionary."

    # The flight_id key must be present
    if "flight_id" not in argument:
        return False, "Missing required argument 'flight_id'."

    flight_id = argument["flight_id"]

    # flight_id must be text
    if type(flight_id) != str:
        return False, "The 'flight_id' argument must be text."

    # flight_id cannot be blank
    if flight_id.strip() == "":
        return False, "The 'flight_id' argument cannot be empty."

    return True, "Validation succeeded."


def run(page, argument, context):
    """Open flight details dialog, extract information, and close the dialog."""
    # Run argument validation before interacting with the browser
    valid, validation_note = validate(argument)
    if not valid:
        return {
            "ok": False,
            "message": "Validation failed: " + validation_note,
            "data": {},
        }

    flight_id = argument["flight_id"].strip()

    try:
        # Locate flight cards containing the requested flight_id
        cards = page.locator(".flight-card").filter(has_text=flight_id)

        if cards.count() == 0:
            cards = page.locator("[data-flight-id='" + flight_id + "']")

        if cards.count() == 0:
            cards = page.locator(".card").filter(has_text=flight_id)

        if cards.count() == 0:
            cards = page.locator(
                "xpath=//div[(contains(@class, 'flight') or contains(@class, 'card')) and contains(., '"
                + flight_id
                + "')]"
            )

        # Check before acting: The flight ID must identify exactly ONE visible card
        matching_count = cards.count()
        if matching_count == 0:
            return {
                "ok": False,
                "message": (
                    "Flight ID '"
                    + flight_id
                    + "' was not found among visible flight cards."
                ),
                "data": {},
            }

        if matching_count > 1:
            return {
                "ok": False,
                "message": (
                    "Ambiguous flight ID '"
                    + flight_id
                    + "': found "
                    + str(matching_count)
                    + " matching flight cards."
                ),
                "data": {},
            }

        target_card = cards.first
        if not target_card.is_visible():
            return {
                "ok": False,
                "message": "Flight card for '" + flight_id + "' is not visible.",
                "data": {},
            }

        # Find the card-specific Details button inside this specific card
        details_btn = target_card.locator("button:has-text('Detail')")
        if details_btn.count() == 0:
            details_btn = target_card.locator(
                "button.details-btn, button.details, [data-action='details']"
            )

        if details_btn.count() == 0 or not details_btn.first.is_visible():
            return {
                "ok": False,
                "message": (
                    "Could not locate a visible details button inside the card for "
                    + flight_id
                    + "."
                ),
                "data": {},
            }

        # Click the card-specific details button to open #flightDialog
        details_btn.first.click()

        # Wait for dialog elements to become visible
        dialog = page.locator("#flightDialog")
        dialog.wait_for(state="visible", timeout=4000)

        if not dialog.is_visible():
            return {
                "ok": False,
                "message": "Flight dialog '#flightDialog' failed to open.",
                "data": {},
            }

        # Read actual dialog title and body text
        dialog_title = ""
        if page.locator("#dialogTitle").count() > 0:
            dialog_title = page.locator("#dialogTitle").inner_text().strip()

        dialog_body = ""
        if page.locator("#dialogBody").count() > 0:
            dialog_body = page.locator("#dialogBody").inner_text().strip()

        # Parse specific details from the dialog body
        route = ""
        time_info = ""
        stops = ""
        price = ""

        if "," in dialog_body:
            parts = dialog_body.split(",")
            if len(parts) >= 1:
                route = parts[0].strip()
            if len(parts) >= 2:
                time_info = parts[1].strip()
            if len(parts) >= 3:
                stops = parts[2].strip()
            if len(parts) >= 4:
                price = parts[3].strip()
        else:
            lines = dialog_body.split("\n")
            for line in lines:
                clean_line = line.strip()
                lower_line = clean_line.lower()
                if "to" in lower_line or "->" in lower_line:
                    if route == "":
                        route = clean_line
                if ":" in clean_line or "am" in lower_line or "pm" in lower_line:
                    if time_info == "":
                        time_info = clean_line
                if "stop" in lower_line or "nonstop" in lower_line:
                    if stops == "":
                        stops = clean_line
                if "$" in clean_line or "price" in lower_line:
                    if price == "":
                        price = clean_line

        # Close the dialog using #closeDialog
        close_btn = page.locator("#closeDialog")
        if close_btn.count() == 0 or not close_btn.is_visible():
            return {
                "ok": False,
                "message": "Close button '#closeDialog' was not found or not visible.",
                "data": {
                    "flight_id": flight_id,
                    "title": dialog_title,
                    "details": dialog_body,
                },
            }

        close_btn.click()

        # Wait for the dialog to close and verify browser state independently
        dialog.wait_for(state="hidden", timeout=4000)
        dialog_is_still_visible = dialog.is_visible()

        if dialog_is_still_visible:
            return {
                "ok": False,
                "message": "Dialog failed to close after clicking #closeDialog.",
                "data": {
                    "flight_id": flight_id,
                    "title": dialog_title,
                    "details": dialog_body,
                },
            }

        # Success: Return structured details and confirm dialog closed
        return {
            "ok": True,
            "message": (
                "Successfully opened, read, and closed flight details for "
                + flight_id
                + "."
            ),
            "data": {
                "flight_id": flight_id,
                "dialog_title": dialog_title,
                "details": dialog_body,
                "route": route,
                "time": time_info,
                "stops": stops,
                "price": price,
                "dialog_closed": True,
            },
        }

    except Exception as error:
        return {
            "ok": False,
            "message": "Browser interaction error: " + str(error),
            "data": {},
        }