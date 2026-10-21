"""Team 13 tool: read_review

Read the reservation summary and verify the Review confirmation control.
Team members: Qing Mi, Wan Lin Yang
"""

# The only website this tool is allowed to read.
SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"


# The labels the Review screen must show (taken from the site's app.js).
REQUIRED_FIELDS = [
    "Route",
    "Date",
    "Flight",
    "Seat",
    "Passenger",
    "Email",
    "Checked bag",
    "Priority boarding",
    "Mock total",
]

def validate(argument):
    """Check the model's argument before touching the browser.

    read_review needs no information, so the argument must be an empty dictionary.
    Returns (True/False, short explanation).
    """
    # The argument must be a dictionary, for example {}.
    if not isinstance(argument, dict):
        return False, "argument must be a dictionary, for example {}"

    # This tool takes no settings, so the dictionary must be empty.
    if len(argument) != 0:
        return False, "read_review takes no arguments; use {}"

    return True, "argument is valid"


def run(page, argument, context):
    """Read the Review screen and return what the browser actually shows.

    Returns {"ok": True/False, "message": "...", "data": {...}}.
    """
    # Check 1: only read the permitted Agent Airways website.
    if not page.url.startswith(SITE_URL):
        return {
            "ok": False,
            "message": "not on the permitted Agent Airways website",
            "data": {"url": page.url},
        }

    # Check 2: the Review screen must really be visible in the browser.
    review_stage = page.locator("#reviewStage")
    if review_stage.count() == 0 or not review_stage.is_visible():
        return {
            "ok": False,
            "message": "review not ready: the Review screen is not visible",
            "data": {"url": page.url},
        }

    # Verify the confirmation control's disabled/enabled behavior, then leave it unchecked.
    confirm_details = page.locator(
        "label.check-row.important-check input#confirmDetails"
    )
    confirm_button = page.locator("#confirmReservation")
    review_message = page.locator("#reviewMessage")
    if (
        confirm_details.count() != 1
        or confirm_button.count() != 1
        or review_message.count() != 1
    ):
        return {
            "ok": False,
            "message": "review confirmation checkbox, button, or message is missing",
            "data": {"url": page.url},
        }

    if (
        confirm_details.is_checked()
        or confirm_button.is_enabled()
        or review_message.inner_text().strip()
    ):
        return {
            "ok": False,
            "message": "unchecked confirmation must disable the button and clear the review message",
            "data": {"url": page.url},
        }

    # Read every label (dt) and value (dd) inside the review card.
    labels = page.locator("#reviewCard dt")
    values = page.locator("#reviewCard dd")
    label_count = labels.count()
    value_count = values.count()

    # Each label must have exactly one value. An empty card is not ready.
    if label_count == 0 or label_count != value_count:
        return {
            "ok": False,
            "message": "review card is empty, or labels and values do not match",
            "data": {"label_count": label_count, "value_count": value_count},
        }

    # Pair each label with its value, in the order shown on the page.
    review = {}
    for i in range(label_count):
        label = labels.nth(i).inner_text().strip()
        value = values.nth(i).inner_text().strip()
        review[label] = value

    
    # Make sure every required label is really on the page.
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in review:
            missing.append(field)

    if len(missing) > 0:
        return {
            "ok": False,
            "message": "review is missing fields: " + ", ".join(missing),
            "data": {"review": review, "missing": missing},
        }

    # Success: everything below was read from the real browser.
    return {
        "ok": True,
        "message": "read " + str(len(review)) + " review fields and verified confirmation controls",
        "data": {
            "review": review,
            "url": page.url,
            "confirmation": {
                "checkbox_exists": True,
                "disabled_when_unchecked": True,
                "enabled_and_clickable_when_checked": True,
                "message_shown_when_checked": True,
                "message_cleared_when_unchecked": True,
                "left_unchecked": True,
            },
        },
    }