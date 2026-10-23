"""Team 10 tool: list_seats
Team members: Julio Sepulveda, Manna Zachariah

Read-only tool. Reports which seats on the seat map are available,
unavailable, or selected. It never clicks a seat.

Tests for this tool are in team_tests/test_list_seats.py.
"""


def validate(argument):
    if type(argument) != dict:
        return False, "The argument must be a dictionary."
    
    if len(argument) != 0:
            return False, "The argument must be an empty dictionary."
   
    return True, "Argument is acceptable."


def run(page, argument, context):
    """Read the seat map and return real seat statuses.

    Returns the shared class format: {"ok": bool, "message": str, "data": dict}.
    Two possible shapes:

      Not ready: {"ok": False, "message": "The seat selection stage is not visible.", "data": {}}
      Ready:     {"ok": True, "message": "Read 30 seats.",
                  "data": {"seats": [{"seat": "1A", "status": "available"}, ...]}}

    Each seat's status is "available", "unavailable", or "selected".
    """
    # Part 0 - check the argument before touching the browser.
    # This tool takes no arguments, so anything other than {} is refused.
    # It reuses validate() so the rule lives in one place.
    is_valid, reason = validate(argument)
    if is_valid == False:
        return {"ok": False, "message": "Invalid argument: " + reason, "data": {}}

    # Part 1 - the not-ready check (our required failure behavior):
    if page.locator("#seatStage").is_visible() == False:
        return {"ok": False, "message": "The seat selection stage is not visible.", "data": {}}

    # Part 2 - read the seats:
    buttons = page.locator("#seatMap button.seat")
    seat_list = []

    for index in range(buttons.count()):
        button = buttons.nth(index)
        seat_name = button.get_attribute("data-seat")
        class_text = button.get_attribute("class")
        if class_text is None:
            class_text = ""

        if button.is_disabled():
            status = "unavailable"
        elif "selected" in class_text.split():
            status = "selected"
        else:
            status = "available"

        seat_list.append({"seat": seat_name, "status": status})

    # Part 3 - return the result in the shared format.
    # The message uses the real count, so nothing is hardcoded.
    message = "Read " + str(len(seat_list)) + " seats."
    return {"ok": True, "message": message, "data": {"seats": seat_list}}

