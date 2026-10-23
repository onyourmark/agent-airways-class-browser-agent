"""Team 12 tool: confirm_demo_reservation

Clicks the final pretend "Confirm reservation" button on Agent Airways,
but ONLY when all of these are true:

1. The model's argument is an empty dictionary: {}
2. Trusted Python context says a real person approved: context["human_approved"] is True
3. The browser is on the fixed Agent Airways practice site, on the review screen
4. Every value on the review card matches the user's goal in context["goal"]
5. The page's own "I confirm" checkbox is checked (the website requires it)
6. No confirmation attempt has been made before in this Python program

The page's "I confirm" checkbox is NOT human approval. Human approval only
comes from trusted Python (for example, a terminal prompt), never from the
model's argument.

Example model proposal:
    {"action": "confirm_demo_reservation", "argument": {}}

Example trusted context (built by Python, not by the model):
    {
        "human_approved": True,
        "goal": {
            "from": "DCA",
            "to": "BOS",
            "date": "2026-10-26",
            "flight_id": "AA101",
            "seat": "1A",
            "passenger_name": "Test Traveler",
            "email": "traveler@example.com",
            "checked_bag": False,
            "priority_boarding": False
        }
    }
"""

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

ALLOWED_SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"

# Goal fields that must be present, and the review-card label each one is shown under.
REQUIRED_GOAL_FIELDS = {
    "date": "Date",
    "flight_id": "Flight",
    "seat": "Seat",
    "passenger_name": "Passenger",
    "email": "Email",
}

# Optional yes/no goal fields. If the goal includes them, they are checked too.
OPTIONAL_YES_NO_FIELDS = {
    "checked_bag": "Checked bag",
    "priority_boarding": "Priority boarding",
}

# Only one final confirmation attempt is allowed per Python program.
# This lives in Python, so the model cannot reset it.
confirmation_attempted = False


def reset_attempt_for_tests():
    """Allow a new attempt. Only test programs should call this, never the model."""
    global confirmation_attempted
    confirmation_attempted = False


def validate(argument):
    """Check the model's argument before anything touches the browser."""
    if type(argument) != dict:
        return False, "The argument must be a dictionary. Use {} for this tool."

    if "human_approved" in argument or "approved" in argument:
        return False, (
            "The model cannot approve the reservation itself. "
            "Human approval comes only from trusted Python context."
        )

    if len(argument) != 0:
        return False, "confirm_demo_reservation takes no arguments. The argument must be {}."

    return True, "The argument is an empty dictionary."


def result(ok, message, data):
    """Build the common return shape used by every team tool."""
    return {"ok": ok, "message": message, "data": data}


def read_card(page, card_selector):
    """Read the label/value pairs (dt/dd) from a review card on the page."""
    labels = page.locator(card_selector + " dt")
    values = page.locator(card_selector + " dd")
    card = {}

    count = labels.count()
    if values.count() < count:
        count = values.count()

    for index in range(count):
        label = labels.nth(index).inner_text().strip()
        value = values.nth(index).inner_text().strip()
        card[label] = value

    return card


def check_goal_shape(goal):
    """Make sure trusted Python supplied a complete goal. Returns a list of problems."""
    problems = []

    if type(goal) != dict:
        problems.append("context['goal'] must be a dictionary of the user's requested details.")
        return problems

    for field in ["from", "to"]:
        if type(goal.get(field)) != str or goal.get(field).strip() == "":
            problems.append("context['goal'] is missing '" + field + "'.")

    for field in REQUIRED_GOAL_FIELDS:
        if type(goal.get(field)) != str or goal.get(field).strip() == "":
            problems.append("context['goal'] is missing '" + field + "'.")

    for field in OPTIONAL_YES_NO_FIELDS:
        if field in goal and type(goal[field]) != bool:
            problems.append("context['goal']['" + field + "'] must be True or False.")

    return problems


def compare_card_to_goal(card, goal):
    """Compare what the browser shows with what the user asked for.

    Returns a list of mismatches. An empty list means everything matched.
    """
    mismatches = []

    # The site shows the route as "DCA → BOS".
    expected_route = goal["from"].strip() + " → " + goal["to"].strip()
    shown_route = card.get("Route", "")
    if shown_route != expected_route:
        mismatches.append("Route: expected '" + expected_route + "' but page shows '" + shown_route + "'.")

    for field in REQUIRED_GOAL_FIELDS:
        label = REQUIRED_GOAL_FIELDS[field]
        expected = goal[field].strip()
        shown = card.get(label, "")

        # Email addresses are compared without caring about upper/lower case.
        if field == "email":
            same = shown.lower() == expected.lower()
        else:
            same = shown == expected

        if not same:
            mismatches.append(label + ": expected '" + expected + "' but page shows '" + shown + "'.")

    for field in OPTIONAL_YES_NO_FIELDS:
        if field in goal:
            label = OPTIONAL_YES_NO_FIELDS[field]
            if goal[field]:
                expected = "Yes"
            else:
                expected = "No"
            shown = card.get(label, "")
            if shown != expected:
                mismatches.append(label + ": expected '" + expected + "' but page shows '" + shown + "'.")

    return mismatches


def run(page, argument, context):
    """Confirm the pretend reservation, only after every safety check passes."""
    global confirmation_attempted

    data = {"clicked": False}

    # --- Checks that do not need the browser -------------------------------

    # 1. Re-check the model's argument, in case run() is called without validate().
    valid, note = validate(argument)
    if not valid:
        return result(False, "Rejected argument: " + note, data)

    # 2. Trusted context must be a dictionary supplied by Python.
    if type(context) != dict:
        return result(False, "Missing trusted context. Python must supply a context dictionary.", data)

    # 3. A real person must have approved. Only the exact value True counts,
    #    so strings like "yes" or "True" are not accepted.
    if context.get("human_approved") is not True:
        return result(False, (
            "No human approval in trusted context (human_approved is not True). "
            "Confirm reservation was NOT clicked."
        ), data)

    # 4. Trusted Python must say what the user actually asked for.
    goal = context.get("goal")
    problems = check_goal_shape(goal)
    if len(problems) > 0:
        data["problems"] = problems
        return result(False, "The trusted goal is incomplete: " + " ".join(problems), data)

    # 5. Only one final confirmation attempt is allowed.
    if confirmation_attempted:
        return result(False, (
            "A confirmation attempt was already made in this program. "
            "Only one final confirmation attempt is allowed."
        ), data)

    # --- Checks that read the browser (nothing is changed yet) -------------

    if page is None:
        return result(False, "There is no browser page to work with.", data)

    # 6. Only the fixed, fake Agent Airways site is allowed.
    current_url = page.url
    data["url"] = current_url
    base_url = current_url.split("#")[0]
    if base_url != ALLOWED_SITE_URL:
        return result(False, "Wrong website. This tool only works on " + ALLOWED_SITE_URL, data)

    # 7. The reservation must not already be confirmed.
    if page.locator("#confirmationStage").is_visible():
        return result(False, "The confirmation page is already showing. Nothing was clicked.", data)

    # 8. The review screen must be the screen currently showing.
    if not page.locator("#reviewStage").is_visible():
        return result(False, "The review screen is not showing, so there is nothing to confirm yet.", data)

    # 9. Every value on the review card must match the user's goal.
    review = read_card(page, "#reviewCard")
    data["review"] = review
    if len(review) == 0:
        return result(False, "The review card is empty. Cannot check the reservation details.", data)

    mismatches = compare_card_to_goal(review, goal)
    if len(mismatches) > 0:
        data["mismatches"] = mismatches
        return result(False, (
            "The review does not match the user's request, so Confirm was NOT clicked. "
            + " ".join(mismatches)
        ), data)

    # 10. The website's own checkbox must be checked, or its button stays disabled.
    #     (This checkbox is part of the web form. It is NOT human approval.)
    checkbox = page.locator("#confirmDetails")
    if checkbox.count() != 1:
        return result(False, "Could not find exactly one 'I confirm' checkbox on the review screen.", data)
    if not checkbox.is_checked():
        return result(False, "The page's 'I confirm' checkbox is not checked yet. Nothing was clicked.", data)

    # 11. There must be exactly one visible, enabled Confirm reservation button.
    button = page.locator("#confirmReservation")
    if button.count() != 1:
        return result(False, "Expected exactly one Confirm reservation button, found " + str(button.count()) + ".", data)
    if not button.is_visible():
        return result(False, "The Confirm reservation button is not visible.", data)
    if not button.is_enabled():
        return result(False, "The Confirm reservation button is disabled.", data)

    # --- The one action: click Confirm reservation -------------------------

    # Record the attempt BEFORE clicking, so a crash during the click
    # still counts as the one allowed attempt.
    confirmation_attempted = True
    button.click()
    data["clicked"] = True

    # --- Read the browser afterward to see what really happened ------------

    try:
        page.locator("#confirmationStage").wait_for(state="visible", timeout=5000)
    except PlaywrightTimeoutError:
        return result(False, "Clicked Confirm, but the confirmation screen did not appear.", data)

    heading = page.locator("#confirmationStage h2").inner_text().strip()
    code = page.locator("#confirmationCode").inner_text().strip()
    details = read_card(page, "#confirmationDetails")

    data["url"] = page.url
    data["heading"] = heading
    data["confirmation_code"] = code
    data["confirmation_details"] = details

    if heading != "RESERVATION CONFIRMED":
        return result(False, "Clicked Confirm, but the page heading is '" + heading + "'.", data)

    if code == "":
        return result(False, "The confirmation screen appeared, but there is no confirmation code.", data)

    return result(True, "Browser shows '" + heading + "' with confirmation code " + code + ".", data)
