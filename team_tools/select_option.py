"""Team 09 tool: select_option

Choose one value in one of the three dropdowns on the Agent Airways search
page, then read the real selection back from the browser.

Example model proposal:
    {"action": "select_option", "argument": {"field": "from", "value": "DCA"}}

Allowed fields and the page element each one controls:
    from        ->  #fromAirport   (departure airport)
    to          ->  #toAirport     (destination airport)
    passengers  ->  #passengers    (number of passengers)

The tool changes at most one dropdown per call. It never clicks Search.
"""

# The only field names the model may use, and the page ID for each one.
FIELD_IDS = {
    "from": "fromAirport",
    "to": "toAirport",
    "passengers": "passengers",
}


def validate(argument):
    """Check the proposed argument before the browser is touched.

    Returns (True, reason) when the argument has the right shape,
    or (False, reason) explaining what is wrong.
    """
    # The argument must be a dictionary, for example {"field": "from", "value": "DCA"}.
    if type(argument) != dict:
        return False, "The argument must be a dictionary with 'field' and 'value'."

    # Both keys must be present.
    if "field" not in argument:
        return False, "The argument is missing 'field'."
    if "value" not in argument:
        return False, "The argument is missing 'value'."

    # No extra keys are allowed, so the model cannot sneak in other instructions.
    for key in argument:
        if key != "field" and key != "value":
            return False, "Unexpected key in the argument: " + str(key)

    field = argument["field"]
    value = argument["value"]

    # Only the three known dropdowns may be changed.
    if field not in FIELD_IDS:
        return False, "Unknown field '" + str(field) + "'. Allowed fields: from, to, passengers."

    # The value must be non-empty text, such as "DCA" or "1".
    if type(value) != str:
        return False, "The value must be text, for example \"DCA\" or \"1\"."
    if value.strip() == "":
        return False, "The value must not be empty."

    # Whether the value is a real option is checked in run(), because only
    # the page knows which options the dropdown actually contains.
    return True, "The argument has an allowed field and a text value."


def run(page, argument, context):
    """Select one dropdown value and report what the browser actually shows.

    page:     the Playwright page
    argument: {"field": ..., "value": ...} proposed by the model
    context:  trusted information from Python (not needed by this tool)

    Always returns {"ok": True/False, "message": "...", "data": {...}}.
    "ok" is True only when the browser's selected value equals the request.
    """
    # Never act on an argument that fails validation.
    valid, reason = validate(argument)
    if valid == False:
        return {"ok": False, "message": "Rejected before acting: " + reason, "data": {}}

    field = argument["field"]
    requested = argument["value"]
    element_id = FIELD_IDS[field]
    menu = page.locator("#" + element_id)

    # The data dictionary is filled in as we learn more about the page.
    data = {"field": field, "requested": requested}

    try:
        # Exactly one matching dropdown must exist. Do not guess between matches.
        if menu.count() != 1:
            return {
                "ok": False,
                "message": "Expected one #" + element_id + " dropdown but found " + str(menu.count()) + ".",
                "data": data,
            }

        # The dropdown must be on the current screen and usable.
        if menu.is_visible() == False:
            return {
                "ok": False,
                "message": "The " + field + " dropdown is not visible on this screen. Open the search page first.",
                "data": data,
            }
        if menu.is_enabled() == False:
            return {"ok": False, "message": "The " + field + " dropdown is disabled.", "data": data}

        # Remember the selection before acting, so we can show it did not change on failure.
        before = menu.input_value()
        data["before"] = before

        # Read the option values the page really offers, skipping the empty placeholder.
        options = []
        option_items = menu.locator("option")
        for i in range(option_items.count()):
            option_value = option_items.nth(i).get_attribute("value")
            if option_value is not None and option_value != "":
                options.append(option_value)
        data["allowed_values"] = options

        # Refuse a value the dropdown does not contain, without changing anything.
        if requested not in options:
            data["actual"] = menu.input_value()
            return {
                "ok": False,
                "message": "'" + requested + "' is not an option in the " + field
                + " dropdown. Allowed: " + ", ".join(options) + ". Nothing was changed.",
                "data": data,
            }

        # The one action: choose the requested option.
        menu.select_option(value=requested)

        # Read the real selection back from the browser.
        actual = menu.input_value()
        data["actual"] = actual

    except Exception as error:
        # A Playwright problem (for example a timeout) is reported, not hidden.
        return {"ok": False, "message": "Browser error: " + str(error), "data": data}

    # Success depends only on what the browser shows, not on the command having run.
    if actual == requested:
        return {
            "ok": True,
            "message": "The " + field + " dropdown now shows " + actual + " (read back from the page).",
            "data": data,
        }
    return {
        "ok": False,
        "message": "Requested " + requested + " but the " + field + " dropdown shows " + actual + ".",
        "data": data,
    }
