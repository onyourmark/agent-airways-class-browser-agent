
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"


def validate(argument):
    """Check the proposed timeout before using the browser."""

    if type(argument) is not dict:
        return False, "Argument must be a dictionary."

    if set(argument.keys()) != {"timeout_seconds"}:
        return False, "Only timeout_seconds is required."

    timeout = argument["timeout_seconds"]

    if type(timeout) is not int:
        return False, "timeout_seconds must be an integer."

    if timeout < 1 or timeout > 10:
        return False, "Timeout must be between 1 and 10 seconds."

    return True, "Valid timeout."


def run(page, argument, context):
    """Wait for real, visible flight results and report the observation."""

    # Validate before interacting with the browser.
    valid, reason = validate(argument)

    if not valid:
        return {
            "ok": False,
            "message": reason,
            "data": {}
        }

    # Only the approved Agent Airways practice site is allowed.
    if page.url.split("#")[0] != SITE_URL:
        return {
            "ok": False,
            "message": "Not on the approved Agent Airways website.",
            "data": {}
        }

    timeout = argument["timeout_seconds"]
    start_time = time.monotonic()

    # Locate flight cards that are actually visible.
    cards = page.locator(".flight-card:visible")

    try:
        # Wait until the first flight result appears.
        cards.first.wait_for(
            state="visible",
            timeout=timeout * 1000
        )

        # Read the real number of visible cards.
        count = cards.count()
        elapsed = round(time.monotonic() - start_time, 3)

        return {
            "ok": count > 0,
            "message": "Flight results are visible." if count > 0
                       else "No visible flight results.",
            "data": {
                "visible_flight_count": count,
                "elapsed_seconds": elapsed,
                "timeout_seconds": timeout
            }
        }

    except PlaywrightTimeoutError:
        elapsed = round(time.monotonic() - start_time, 3)
        count = cards.count()

        return {
            "ok": False,
            "message": "Timed out waiting for flight results.",
            "data": {
                "visible_flight_count": count,
                "elapsed_seconds": elapsed,
                "timeout_seconds": timeout
            }
        }
