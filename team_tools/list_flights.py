def validate(argument):
    """Only an empty dictionary is allowed for this read-only tool."""
    if argument != {}:
        return False, "Use an empty dictionary: {}"

    return True, "Valid argument"


def run(page, argument, context):
    """Read visible flight IDs, stop text, and prices without changing the page."""
    valid, message = validate(argument)

    if not valid:
        return {
            "ok": False,
            "message": message,
            "data": {}
        }

    results_stage = page.locator("#resultsStage")

    if results_stage.count() != 1 or not results_stage.is_visible():
        return {
            "ok": False,
            "message": "Flight results are not ready. Search for flights first.",
            "data": {"flights": []}
        }

    cards = results_stage.locator(".flight-card:visible")

    if cards.count() == 0:
        return {
            "ok": False,
            "message": "Flight results are not ready. Search for flights first.",
            "data": {"flights": []}
        }

    flights = []

    for i in range(cards.count()):
        card = cards.nth(i)
        flight_id = card.get_attribute("data-flight-id")
        details = card.locator("div").nth(1).locator("p")

        if not flight_id or details.count() < 2:
            return {
                "ok": False,
                "message": "A visible flight card is missing required information.",
                "data": {"flights": flights}
            }

        flights.append({
            "flight_id": flight_id,
            "stops": details.nth(0).inner_text().strip(),
            "price": details.nth(1).inner_text().strip()
        })

    return {
        "ok": True,
        "message": "Read " + str(len(flights)) + " visible flight cards.",
        "data": {"flights": flights}
    }






