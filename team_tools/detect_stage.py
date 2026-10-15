"""Detect the one visible Agent Airways stage without changing the browser.

The tool accepts an empty dictionary. The caller cannot provide its own stage.
Results-stage observations also report whether the loading message is visible.
"""

SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"


def validate(argument):
    """Return (whether valid, a short explanation), without opening a browser."""
    if type(argument) != dict:
        return False, "argument must be an empty dictionary."
    if argument != {}:
        return False, "detect_stage accepts only an empty dictionary."
    return True, "The empty argument dictionary is valid."


def run(page, argument, context):
    """Read visible sections; context is reserved for later agent integration."""
    valid, message = validate(argument)
    if not valid:
        return {"ok": False, "message": message, "data": {}}
    if page is None or page.is_closed():
        return {"ok": False, "message": "No open browser page was supplied.", "data": {}}

    # The URL identifies the site. Its hash is never used to decide the stage.
    if page.url.split("#", 1)[0] != SITE_URL:
        return {"ok": False, "message": "The page is not the approved Agent Airways site.", "data": {}}

    stages = ["search", "results", "seat", "passenger", "review", "confirmation"]
    visible = []
    for stage in stages:
        section = page.locator("#" + stage + "Stage")
        if section.count() > 1:
            return {"ok": False, "message": "Duplicate stage elements: " + stage, "data": {}}
        if section.count() == 1 and section.is_visible():
            visible.append(stage)

    if len(visible) == 0:
        return {"ok": False, "message": "No known stage is visible.", "data": {}}
    if len(visible) > 1:
        return {"ok": False, "message": "More than one stage is visible.", "data": {}}

    stage = visible[0]
    loading = False
    if stage == "results":
        indicator = page.locator("#loadingFlights")
        if indicator.count() != 1:
            return {"ok": False, "message": "Expected exactly one results loading indicator.", "data": {}}
        loading = indicator.is_visible()

    return {"ok": True, "message": "The " + stage + " screen is visible.", "data": {"stage": stage, "loading": loading}}
