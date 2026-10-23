"""Team 03 tool: click_step_button

Clicks ONE approved "next step" button on the Agent Airways practice site,
then checks that the expected next screen really appeared.

Example model proposal:
    {"action": "click_step_button", "argument": {"button": "search_flights"}}

This tool ONLY clicks. It does not fill in fields, choose flights,
or pick seats. The test (or another team's tool) does that first.
It can never click "Confirm reservation" (that belongs to Team 12).
"""


# The only buttons this tool is allowed to click.
# For each one we store:
#   "button_id": the button's id on the page
#   "expected":  the element that should change after the click
#   "check":     "appear" means the element should become visible,
#                "disappear" means the element should become hidden
ALLOWED_BUTTONS = {
    "search_flights": {
        "button_id": "#searchFlights",
        "expected": "#resultsStage",
        "check": "appear",
    },
    "continue_from_seat": {
        "button_id": "#continueFromSeat",
        "expected": "#passengerStage",
        "check": "appear",
    },
    "continue_to_review": {
        "button_id": "#continueToReview",
        "expected": "#reviewStage",
        "check": "appear",
    },
    "close_details": {
        "button_id": "#closeDialog",
        "expected": "#flightDialog",
        "check": "disappear",
    },
}

# The screens (stages) of the site, in order. Only one is shown at a time.
STAGE_IDS = [
    "#searchStage",
    "#resultsStage",
    "#seatStage",
    "#passengerStage",
    "#reviewStage",
    "#confirmationStage",
]

# How long to wait (in milliseconds) for the next screen after a click.
WAIT_MS = 3000


def validate(argument):
    """Check the proposed argument BEFORE anything happens in the browser.

    Returns (True, message) if the proposal is acceptable,
    or (False, message) if it must be rejected.
    """
    # The argument must be a dictionary like {"button": "search_flights"}.
    if type(argument) != dict:
        return False, "The argument must be a dictionary like {\"button\": \"search_flights\"}."

    # It must contain exactly one key: "button".
    if "button" not in argument:
        return False, "The argument is missing \"button\"."

    if len(argument) != 1:
        return False, "The argument must contain only \"button\"."

    button = argument["button"]

    # The button name must be text.
    if type(button) != str:
        return False, "The button name must be text."

    # Confirm reservation is never allowed here. It belongs to another team.
    if button == "confirm_reservation":
        return False, "confirm_reservation is not allowed. This tool only clicks step buttons."

    # Only the four approved button names are accepted.
    if button not in ALLOWED_BUTTONS:
        return False, "Unknown button: " + button

    return True, "Validation succeeded."


def find_visible_stage(page):
    """Return the id of the screen that is visible right now, or "" if none."""
    for stage_id in STAGE_IDS:
        if page.locator(stage_id).is_visible():
            return stage_id
    return ""


def make_result(ok, message, data):
    """Build the result in the shared format: {"ok", "message", "data"}."""
    return {"ok": ok, "message": message, "data": data}


def run(page, argument, context):
    """Click one approved step button and check what really happened.

    page:     the Playwright page
    argument: a dictionary like {"button": "search_flights"}
    context:  not used by this tool (kept so all tools share one format)
    """
    # 1. Validate again here, so this tool is safe even if called directly.
    valid, note = validate(argument)
    if not valid:
        return make_result(False, note, {"clicked": False})

    button_name = argument["button"]
    info = ALLOWED_BUTTONS[button_name]
    button = page.locator(info["button_id"])

    # Evidence we will report back.
    data = {
        "button": button_name,
        "clicked": False,
        "stage_before": find_visible_stage(page),
        "url_before": page.url,
    }

    # 2. Check the button BEFORE clicking: it must exist, be visible, and be enabled.
    if button.count() == 0:
        return make_result(False, "The " + button_name + " button was not found on the page.", data)

    if not button.is_visible():
        return make_result(False, "The " + button_name + " button is not visible on this screen, so it was not clicked.", data)

    if not button.is_enabled():
        return make_result(False, "The " + button_name + " button is disabled, so it was not clicked.", data)

    # 3. Click the button.
    button.click()
    data["clicked"] = True

    # 4. Check what ACTUALLY happened. A click alone does not count as success.
    expected = page.locator(info["expected"])
    if info["check"] == "appear":
        wanted_state = "visible"
    else:
        wanted_state = "hidden"

    try:
        expected.wait_for(state=wanted_state, timeout=WAIT_MS)
        changed = True
    except Exception:
        changed = False

    data["stage_after"] = find_visible_stage(page)
    data["url_after"] = page.url

    if changed:
        if info["check"] == "appear":
            message = "Clicked " + button_name + ". The next screen " + info["expected"] + " is now visible."
        else:
            message = "Clicked " + button_name + ". The flight details popup is now closed."
        return make_result(True, message, data)

    # The click ran, but the expected change did not happen.
    message = "Clicked " + button_name + ", but " + info["expected"] + " did not " + info["check"] + "."

    # For search, the site explains why in #searchError (for example, a missing airport).
    if button_name == "search_flights":
        error_text = page.locator("#searchError").inner_text().strip()
        data["page_error"] = error_text
        if error_text != "":
            message = message + " The page says: " + error_text

    return make_result(False, message, data)