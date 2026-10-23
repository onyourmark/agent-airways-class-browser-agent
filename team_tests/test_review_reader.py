import os
import sys
from playwright.sync_api import sync_playwright

#find the main project directory so Python can import our tool
project_folder = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.insert(0, project_folder)

from team_tools.check_review_against_goal import (
    confirm_review_stage,
    read_review_card
)

SITE_URL = "https://onyourmark.github.io/browser-agent-form/travel/"

with sync_playwright() as playwright:

    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        page.goto(SITE_URL)

        #TEST 1: The reader should reject the Search screen.
        print("\nTEST 1: Search stage")

        assert page.locator("#searchStage").is_visible()

        stage_ok, message = confirm_review_stage(page)

        assert stage_ok is False
        print("PASS:", message)

        data, message = read_review_card(page)
        assert data is None
        print("PASS: Reader refused to read Search screen.")

        print("\nComplete the reservation in Chromium.")
        print("Stop at Review. Do not click Confirm.")

        input("Press Enter once Review is visible...")

        #TEST 2: Detect Review.
        print("\nTEST 2: Review stage")

        assert page.locator("#reviewStage").is_visible()

        stage_ok, message = confirm_review_stage(page)

        assert stage_ok is True
        print("PASS:", message)

        #TEST 3: Read the reservation information.
        print("\nTEST 3: Read review card")

        before_url = page.url
        before_text = page.locator("#reviewCard").inner_text()

        review_data, message = read_review_card(page)

        print("Reader message: ", message)
        print("Reader data: ", review_data)

        assert isinstance(review_data, dict)

        print(message)

        for label in review_data:
            print(label, ":", review_data[label])

        
        

        #TEST 4: Verify actual browser values.
        print("\nTEST 4: Verify actual browser values")

        card = page.locator("#reviewCard")
        browser_labels = card.locator("dt")
        browser_values = card.locator("dd")

        assert browser_labels.count() == browser_values.count()


        for i in range(browser_labels.count()):

            label = browser_labels.nth(i).inner_text().strip()
            value = browser_values.nth(i).inner_text().strip()

            matching_key = None

            for key in review_data:
                if key.lower() == label.lower():
                    matching_key = key
                    break

            assert matching_key is not None, (
                f"Missing field: {label}"
            )

            assert review_data[matching_key] == value, (
                f"Incorrect value for {label}: "
                f"{review_data[matching_key]} != {value}"
            )

            print(f"PASS: {label} = {value}")








        print("PASS: All review fields match the browser.")
        
        #TEST 5: Make sure the tool did not change the webpage.
        print("\nTEST 5: Verify the browser was not changed")

        assert page.url == before_url

        after_text = page.locator("#reviewCard").inner_text()
        assert after_text == before_text

        assert page.locator("#reviewStage").is_visible()

        print("PASS: Review screen remained unchanged.")

        print("\nALL PERSON 2 TESTS PASSED!")

    finally:
        # Wait before closing the browser.
        input("\nPress Enter to close Chromium...")

        browser.close()

