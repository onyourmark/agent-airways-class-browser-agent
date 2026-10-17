"""Team 10 tool: list_seats
Team members: Julio Sepulveda, Manna Zachariah

Read-only tool. Reports which seats on the seat map are available,
unavailable, or selected. It never clicks a seat.
"""


def validate(argument):
    if type(argument) != dict:
        return False, "The argument must be a dictionary."
    
    if len(argument) != 0:
            return False, "The argument must be an empty dictionary."
   
    return True, "Argument is acceptable."


def run(page, argument, context):
    """Read the seat map and return real seat statuses.

    Must return a dictionary. Two possible shapes:

      Not ready: {"ready": False, "reason": "why the tool could not read seats"}
      Ready:     {"ready": True, "seats": [{"seat": "1A", "status": "available"}, ...]}

    Each seat's status is "available", "unavailable", or "selected".
    """
    # Part 1 - the not-ready check (our required failure behavior):
    if page.locator("#seatStage").is_visible() == False:
        return {"ready": False, "reason": "The seat selection stage is not visible."}

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

    # Part 3 - return {"ready": True, "seats": the_list}
    return {"ready": True, "seats": seat_list}


def main():
    """Manual test harness. Not part of the tool itself.

    Runs both required tests in one session:
      Failure test: call the tool on the opening page (before any
                    flight is chosen) and expect a not-ready result.
      Success test: a human navigates to the seat map, then the tool
                    should report 1A available and 1B unavailable.
    """
    import sys
    from pathlib import Path

    # Allow "python team_tools/list_seats.py" to find browser_tools.py
    # in the repository root.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import browser_tools

    browser_tools.start_browser()
    try:
        browser_tools.open_site()

        print("\n--- FAILURE TEST: before reaching the seat map ---")
        result = run(browser_tools.page, {}, {})
        print("Result:", result)
        if result.get("ready") is False:
            print("PASS: tool reported not-ready instead of inventing seats.")
        else:
            print("FAIL: tool should have reported not-ready.")

        print("\nNow use the browser window to search for a flight,")
        print("choose one, and continue until the seat map is visible.")
        input("Press Enter when you can see the seat map...")

        print("\n--- SUCCESS TEST: seat map visible ---")
        result = run(browser_tools.page, {}, {})
        print("Result:", result)

        statuses = {}
        for seat in result.get("seats", []):
            statuses[seat["seat"]] = seat["status"]

        if statuses.get("1A") in ("available", "selected") and statuses.get("1B") == "unavailable":
            print("PASS: 1A is choosable and 1B is unavailable, as on the demo site.")
        else:
            print("FAIL: expected 1A available and 1B unavailable. Check the output above.")

        input("Press Enter to close the browser...")
    finally:
        browser_tools.close_browser()


if __name__ == "__main__":
    main()
