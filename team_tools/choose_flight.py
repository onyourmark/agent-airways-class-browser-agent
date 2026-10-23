"""Team 08 - choose_flight

Picks one of the flights shown on the Agent Airways results screen and then
checks that the seat-selection screen really opened for that flight.
Used between "2. Choose a flight" and "3. Choose a seat".

Example proposal from the model:
    {"action": "choose_flight", "argument": {"flight_id": "AA101"}}

validate(argument)           -> (True/False, reason)
run(page, argument, context) -> {"ok": True/False, "message": "...", "data": {...}}

One call clicks at most one Choose button. The tool does not search for
flights, wait for slow results, or pick a seat; other team tools do those.
"""

import re

from playwright.sync_api import Error as PlaywrightError


# The only site this tool may act on (same value as browser_tools.SITE_URL).
SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"

# Flight numbers on the site look like AA101: two capital letters, three digits.
FLIGHT_ID_PATTERN = r"[A-Z]{2}[0-9]{3}"

# Each booking step is its own <section>, and the site shows one at a time.
STAGES = {
    "search": "#searchStage",
    "results": "#resultsStage",
    "seat": "#seatStage",
    "passenger": "#passengerStage",
    "review": "#reviewStage",
    "confirmation": "#confirmationStage",
}


def visible_stage(page):
    """Return the name of the stage currently on screen, or "unknown"."""
    for name in STAGES:
        if page.locator(STAGES[name]).is_visible():
            return name
    return "unknown"


def validate(argument):
    """Check the proposed argument without touching the browser.

    Only the shape of the argument is checked here. Whether the flight is
    actually offered can only be seen on the page, so run() checks that part.
    """
    if not isinstance(argument, dict):
        return False, 'argument must be a dictionary, for example {"flight_id": "AA101"}.'

    if "flight_id" not in argument:
        return False, 'argument is missing "flight_id".'

    # One flight per call, and nothing else (seat, name, ...) on the side.
    for key in argument:
        if key != "flight_id":
            return False, "unexpected key " + repr(key) + "; choose_flight only takes flight_id."

    flight_id = argument["flight_id"]
    if not isinstance(flight_id, str):
        return False, "flight_id must be a string, not " + type(flight_id).__name__ + "."

    if flight_id.strip() == "":
        return False, "flight_id is empty."

    # No auto-correcting: "aa101" or " AA101" are refused, not fixed.
    # This also keeps quotes out of the CSS selector that run() builds.
    if re.fullmatch(FLIGHT_ID_PATTERN, flight_id) is None:
        return False, "flight_id must look like AA101 (two capital letters, then three digits)."

    return True, "flight_id " + flight_id + " has the right format; run() still checks the page."


def run(page, argument, context):
    """Click the Choose button of one visible flight, then read the seat screen.

    context is not used: choosing a flight needs no goal or approval from
    trusted Python. The parameter is kept so all team tools look the same.
    Playwright errors (for example a closed window) come back as ok=False
    instead of being raised.
    """
    # Same keys in every return, so callers never have to check whether a key exists.
    # stage_after, selected_flight_* and seat_stage_checks are only filled in after a click.
    data = {
        "requested_flight_id": "",
        "offered_flights": [],
        "stage_before": "",
        "clicked": False,
        "stage_after": "",
        "selected_flight_id": "",
        "selected_flight_summary": "",
        "seat_stage_checks": {},
        "url": "",
    }

    # run() could be called without validate() first, so check again here.
    is_valid, reason = validate(argument)
    if not is_valid:
        return {
            "ok": False,
            "message": "Refused: " + reason + " Nothing was clicked.",
            "data": data,
        }

    flight_id = argument["flight_id"]
    data["requested_flight_id"] = flight_id

    if page is None:
        return {
            "ok": False,
            "message": "No browser page was passed to run(). Nothing was clicked.",
            "data": data,
        }

    data["url"] = page.url
    if not page.url.startswith(SITE_URL):
        return {
            "ok": False,
            "message": "Refused: the browser is not on the Agent Airways practice site. "
            + "Nothing was clicked.",
            "data": data,
        }

    # From here on the code talks to the live page. If Playwright itself fails
    # (window closed, an element vanishes in the middle of a check), the except
    # at the end turns that into a normal failure result instead of an exception.
    try:
        # Checks before clicking. If any of them fails, nothing has been clicked.
        data["stage_before"] = visible_stage(page)
        if data["stage_before"] != "results":
            return {
                "ok": False,
                "message": "Flight results are not on screen (current stage: "
                + data["stage_before"] + "). Nothing was clicked.",
                "data": data,
            }

        # After a search the site shows "Loading flights..." for about 1.2 seconds.
        if page.locator("#loadingFlights").is_visible():
            return {
                "ok": False,
                "message": "Flights are still loading. Wait for the flight cards first. "
                + "Nothing was clicked.",
                "data": data,
            }

        # The Flight details dialog is modal, so a click behind it would just time out.
        if page.locator("#flightDialog").is_visible():
            return {
                "ok": False,
                "message": "The Flight details dialog is open. Close it before choosing a flight."
                + " Nothing was clicked.",
                "data": data,
            }

        # Read the visible flight cards and keep the ones whose ID matches.
        # Hidden cards (for example a hidden duplicate) are not counted as offered.
        cards = page.locator("#flightResults .flight-card")
        matching_cards = []
        for i in range(cards.count()):
            card = cards.nth(i)
            if not card.is_visible():
                continue
            card_id = card.get_attribute("data-flight-id")
            if card_id is None:
                continue
            data["offered_flights"].append(card_id)
            if card_id == flight_id:
                matching_cards.append(card)

        if len(data["offered_flights"]) == 0:
            return {
                "ok": False,
                "message": "No flight cards are visible, so there is nothing to choose. "
                + "Nothing was clicked.",
                "data": data,
            }

        if len(matching_cards) == 0:
            return {
                "ok": False,
                "message": flight_id + " is not one of the offered flights ("
                + ", ".join(data["offered_flights"]) + "). Nothing was clicked.",
                "data": data,
            }

        # Two cards with the same ID would be ambiguous, so refuse instead of guessing.
        if len(matching_cards) > 1:
            return {
                "ok": False,
                "message": flight_id + " appears on " + str(len(matching_cards))
                + " flight cards, so the choice is ambiguous. Nothing was clicked.",
                "data": data,
            }

        # The Choose button inside that card, found by data-flight instead of by position.
        button = matching_cards[0].locator('button.choose[data-flight="' + flight_id + '"]')
        button_count = button.count()
        if button_count != 1:
            return {
                "ok": False,
                "message": "Expected one Choose button for " + flight_id + " but found "
                + str(button_count) + ". Nothing was clicked.",
                "data": data,
            }

        if not button.is_visible():
            return {
                "ok": False,
                "message": "The Choose button for " + flight_id + " is not visible. "
                + "Nothing was clicked.",
                "data": data,
            }

        if not button.is_enabled():
            return {
                "ok": False,
                "message": "The Choose button for " + flight_id + " is disabled. "
                + "Nothing was clicked.",
                "data": data,
            }

        # The one action of this tool.
        button.click(timeout=5000)
        data["clicked"] = True

        # Read the result back from the page instead of trusting the click.

        # The site switches stages right away, but wait up to 3 seconds in case it is slow.
        try:
            page.locator("#seatStage").wait_for(state="visible", timeout=3000)
        except PlaywrightError:
            pass  # seat_stage_visible below will then be False

        # Only use the summary if it is actually shown on the seat screen.
        summary = ""
        if page.locator("#selectedFlightSummary").is_visible():
            summary = page.locator("#selectedFlightSummary").inner_text().strip()

        # The site writes e.g. "Selected AA101: DCA to BOS, departing 8:10 AM."
        shown_id = ""
        if summary.startswith("Selected "):
            shown_id = summary[len("Selected "):].split(":")[0].strip()

        checks = {
            "seat_stage_visible": page.locator("#seatStage").is_visible(),
            "results_stage_hidden": not page.locator("#resultsStage").is_visible(),
            "summary_names_flight": shown_id == flight_id,
            "seat_map_loaded": page.locator("#seatMap button.seat").count() > 0,
        }

        data["stage_after"] = visible_stage(page)
        data["selected_flight_id"] = shown_id
        data["selected_flight_summary"] = summary
        data["seat_stage_checks"] = checks
        data["url"] = page.url

    except PlaywrightError as error:
        # data["clicked"] still shows whether the click went through before the error.
        return {
            "ok": False,
            "message": "Browser error: " + str(error).split("\n")[0],
            "data": data,
        }

    failed_checks = []
    for name in checks:
        if not checks[name]:
            failed_checks.append(name)

    if len(failed_checks) > 0:
        return {
            "ok": False,
            "message": "Clicked Choose " + flight_id + ", but the seat screen did not confirm it. "
            + "Failed checks: " + ", ".join(failed_checks) + ".",
            "data": data,
        }

    return {
        "ok": True,
        "message": "Chose " + flight_id + ". Seat selection is open: " + summary,
        "data": data,
    }
