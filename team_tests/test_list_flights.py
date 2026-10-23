from playwright.sync_api import sync_playwright
from team_tools.list_flights import run, validate

SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"


def invalid_argument_test():
    invalid_arguments = [
        {"flight_id": "AA101"},
        {"unexpected": "value"},
        None,
        "AA101",
        [],
    ]

    for argument in invalid_arguments:
        valid, message = validate(argument)

        print("Invalid validate test:", argument, valid, message)

        assert valid is False
        assert message == "Use an empty dictionary: {}"


def invalid_argument_does_not_change_browser_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SITE_URL, wait_until="domcontentloaded")

        url_before = page.url
        search_visible_before = page.locator("#searchStage").is_visible()

        result = run(page, {"flight_id": "AA101"}, {})

        url_after = page.url
        search_visible_after = page.locator("#searchStage").is_visible()

        print("Invalid run test:", result)

        assert result["ok"] is False
        assert result["data"] == {}
        assert url_before == url_after
        assert search_visible_before == search_visible_after

        browser.close()


def before_search_failure_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SITE_URL, wait_until="domcontentloaded")

        result = run(page, {}, {})

        print("Before-search failure test:", result)

        assert result["ok"] is False
        assert result["data"]["flights"] == []
        assert "not ready" in result["message"].lower()

        browser.close()


def success_and_independent_verification_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(6000)
        page.goto(SITE_URL, wait_until="domcontentloaded")

        page.locator("#fromAirport").select_option("DCA")
        page.locator("#toAirport").select_option("BOS")
        page.locator("#departureDate").fill("2026-11-15")
        page.locator("#searchFlights").click()

        page.locator(".flight-card").first.wait_for()

        cards_before = page.locator(".flight-card:visible")
        card_text_before = cards_before.all_inner_texts()
        url_before = page.url

        result = run(page, {}, {})

        actual_cards = page.locator(".flight-card:visible")
        card_text_after = actual_cards.all_inner_texts()
        url_after = page.url

        assert result["ok"] is True
        assert len(result["data"]["flights"]) == actual_cards.count()
        assert actual_cards.count() > 0

        for i in range(actual_cards.count()):
            actual_card = actual_cards.nth(i)
            actual_id = actual_card.get_attribute("data-flight-id")
            actual_card_text = actual_card.inner_text()

            returned_flight = result["data"]["flights"][i]

            # Independent check: use the card's full visible text,
            # not the tool's div and paragraph layout assumptions.
            assert returned_flight["flight_id"] == actual_id
            assert returned_flight["flight_id"] in actual_card_text
            assert returned_flight["stops"] in actual_card_text
            assert returned_flight["price"] in actual_card_text

        # list_flights is read-only and must not change the browser.
        assert url_before == url_after
        assert card_text_before == card_text_after

        print("Success and independent verification test:", result)

        browser.close()


if __name__ == "__main__":
    invalid_argument_test()
    invalid_argument_does_not_change_browser_test()
    before_search_failure_test()
    success_and_independent_verification_test()
    print("All Team 05 tests passed.")