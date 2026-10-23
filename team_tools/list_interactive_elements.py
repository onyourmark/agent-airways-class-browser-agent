"""Team 04 tool: list_interactive_elements

Read the visible buttons, inputs, dropdowns, and checkboxes on the current
Agent Airways screen so the model knows what it can act on.

This tool is READ-ONLY. It never clicks, types, or selects anything.

Example model proposal:
    {"action": "list_interactive_elements", "argument": {}}
"""

# The only page this tool is allowed to observe.
ALLOWED_URL = "https://onyourmark.github.io/browser-agent-form/travel/"

# The kinds of HTML controls we look for, in the order we report them.
CONTROL_TAGS = ["select", "input", "textarea", "button"]


def validate(argument):
    """Check the model's argument before touching the browser.

    Returns (True/False, short explanation).
    """
    # The shared format says the argument is always a dictionary.
    if type(argument) != dict:
        return False, "The argument must be a dictionary, such as {}."

    # This tool takes no options, so the dictionary must be empty.
    if len(argument) > 0:
        unexpected = ", ".join(argument.keys())
        return False, "This tool takes no arguments. Unexpected keys: " + unexpected

    return True, "Validation succeeded."


def is_allowed_page(url):
    """Return True only for the Agent Airways practice page.

    The site adds a stage name after '#' (for example #search or #seat),
    so we remove that part before comparing.
    """
    url_without_hash = url.split("#")[0]
    return url_without_hash == ALLOWED_URL


def find_current_stage(page):
    """Return the id of the visible stage section, such as 'searchStage'."""
    sections = page.locator("section.stage")
    for i in range(sections.count()):
        section = sections.nth(i)
        if section.is_visible():
            return section.get_attribute("id")
    return ""


def read_label(element, tag):
    """Find a human-readable name for one control."""
    # 1. Some controls (like seat buttons) have an aria-label.
    aria_label = element.get_attribute("aria-label")
    if aria_label:
        return aria_label.strip()

    # 2. Buttons show their own text, such as "Search flights".
    if tag == "button":
        return element.inner_text().strip()

    # 3. On this site, inputs and dropdowns sit inside a <label>.
    #    The first non-empty line of that label is its name, e.g. "From".
    labels = element.locator("xpath=ancestor::label[1]")
    if labels.count() > 0:
        lines = labels.first.inner_text().split("\n")
        for line in lines:
            if line.strip() != "":
                return line.strip()

    # 4. Last resort: use the element's id so it is never blank.
    element_id = element.get_attribute("id")
    if element_id:
        return element_id
    return ""


def read_control(element, tag):
    """Read one visible control and return a dictionary describing it."""
    # Work out the kind of control: "button", "select", "textarea",
    # or the input's type, such as "text", "date", "email", or "checkbox".
    kind = tag
    if tag == "input":
        input_type = element.get_attribute("type")
        if input_type:
            kind = input_type
        else:
            kind = "text"

    control = {
        "id": element.get_attribute("id") or "",
        "kind": kind,
        "label": read_label(element, tag),
        "value": None,
        "enabled": element.is_enabled(),
    }

    # Flight-card and seat buttons have no id, and several share the same
    # text ("Flight details"). Report which flight or seat each one is for.
    flight = element.get_attribute("data-flight")
    if flight:
        control["flight"] = flight
    seat = element.get_attribute("data-seat")
    if seat:
        control["seat"] = seat

    # Read the current value straight from the browser.
    if kind == "checkbox":
        control["value"] = element.is_checked()
    elif tag == "select":
        control["value"] = element.input_value()
        # Also report the visible text of the chosen option.
        chosen = element.locator("option:checked")
        if chosen.count() > 0:
            control["selected_text"] = chosen.first.inner_text().strip()
    elif tag == "input" or tag == "textarea":
        control["value"] = element.input_value()

    return control


def run(page, argument, context):
    """List the visible controls on the current page.

    Returns {"ok": True/False, "message": "...", "data": {...}}.
    context is not needed by this tool, but is kept for the shared format.
    """
    # Safety net: never act on an argument that fails validation.
    valid, reason = validate(argument)
    if not valid:
        return {"ok": False, "message": reason, "data": {}}

    # Only observe the permitted practice site.
    current_url = page.url
    if not is_allowed_page(current_url):
        return {
            "ok": False,
            "message": "The browser is not on the permitted Agent Airways page.",
            "data": {"url": current_url, "elements": []},
        }

    elements = []
    try:
        # Look at every control of each kind, keeping only visible ones.
        for tag in CONTROL_TAGS:
            matches = page.locator(tag)
            for i in range(matches.count()):
                element = matches.nth(i)
                if not element.is_visible():
                    continue
                elements.append(read_control(element, tag))

        stage = find_current_stage(page)
    except Exception as error:
        # The page changed or a read failed; report it instead of guessing.
        return {
            "ok": False,
            "message": "Could not read the page controls: " + str(error),
            "data": {"url": current_url, "elements": []},
        }

    # Every Agent Airways screen has at least one control, so finding none
    # means the page is not what we expect. Do not report an empty success.
    if len(elements) == 0:
        return {
            "ok": False,
            "message": "No visible controls were found on this page.",
            "data": {"url": current_url, "stage": stage, "count": 0, "elements": []},
        }

    return {
        "ok": True,
        "message": "Found " + str(len(elements)) + " visible controls.",
        "data": {
            "url": current_url,
            "stage": stage,
            "count": len(elements),
            "elements": elements,
        },
    }
