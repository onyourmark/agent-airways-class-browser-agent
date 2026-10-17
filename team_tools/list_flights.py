def validate(argument):
    if argument != {}:
        return False, "Use an empty dictionary: {}"
    return True, "Valid argument"


def run(page, argument, context):
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

    cards = page.locator(".flight-card:visible")

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

        flights.append({
            "flight_id": flight_id,
            "stops": details.nth(0).inner_text().strip(),
             "price": details.nth(1).inner_text().strip()
        })

    return {
        "ok": True,
        "message": "Flights were read successfully.",
        "data": {"flights": flights}
    }