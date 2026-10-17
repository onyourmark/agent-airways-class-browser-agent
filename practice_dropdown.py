"""First classroom programming exercise: work with a real browser dropdown.

You do NOT need Ollama or a language model for this exercise.
Write the missing Python function below and run this file in VS Code.
"""

import browser_tools


def select_dropdown(field_id, choice):
    """Find a dropdown by its ID, select a choice, and return its actual value."""
    menu = browser_tools.page.locator("#" + field_id)
    menu.select_option(choice)
    return menu.input_value()


def main():
    # The starter already knows how to open a browser and the practice site.
    browser_tools.start_browser()

    try:
        browser_tools.open_site()
        print("Agent Airways is open in Chromium.")
        print("The three dropdowns are From, To, and Passengers.")

        # These are real IDs and option values on the practice website.
        from_result = select_dropdown("fromAirport", "DCA")
        to_result = select_dropdown("toAirport", "BOS")
        passengers_result = select_dropdown("passengers", "3")

        # These checks read the function's returned browser values.
        print("From:", from_result)
        print("To:", to_result)
        print("Passengers:", passengers_result)

        if from_result == "DCA" and to_result == "BOS" and passengers_result == "3":
            print("SUCCESS: The three dropdowns contain the requested values.")
        else:
            print("NOT YET CORRECT: Look at the dropdown values and try again.")

        input("Press Enter when you have finished looking at the browser...")

    finally:
        browser_tools.close_browser()


if __name__ == "__main__":
    main()
