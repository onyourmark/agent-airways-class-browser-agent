"""
this tool checks whether the reservation shown on the review screen 
matches the reservation that was made in the goal screen. It is used 
to verify that the correct reservation is being displayed to the user 
after they have made a reservation.

this tool only reads the screen and takes in the information that is
displayed.

"""

#constants and field names
#pieces of information from from goal (from, to, date, time, flight_id, seat, name)
REQUIRED_GOAL_KEYS = ["from", "to", "date", "flight_id", "seat", "passenger", "email", 
                      "checked_bag", "priority_boarding" ]



# The model must not pass any values to this tool
def validate(argument):
    if not isinstance(argument, dict):
        return False, "Argument must be a dictionary"
    if len(argument) > 0:
        return False, "This tool takes no argument. Send {} only."
    return True, "Argument is an empty dictionary."




#check context goal
#helps with checking the context goal and making sure that the informatiion is valid and that the context goal is 
# valid. It will return a failure result if the context goal is not valid or if the information is not valid.

def check_goal(context):
    # context must be a dictionary that hold goal as one of it's key-value pairs
    if not isinstance(context, dict):
        return False, "Context must be a dictionary"
    if "goal" not in context:
        return False, "Context does not have 'goal' entry"
    goal = context["goal"]

    # The goal itself must also be a dictionary
    if not isinstance(goal, dict):
        return False, "context['goal'] must be a dictionary"

    # Check is all key-value pairs are present
    for key in REQUIRED_GOAL_KEYS:
        if key not in goal:
            return False, "Goal is missing this required key: " + key

    return True, "Goal has all required fields"


#labels on the review card on the webpage
#dt/dt pairs (route, date, flight, seat, passenger, email, checked bag, priotity boarding, mock total)



#validate the reservation information on the review screen against the reservation information from the goal screen
#function
#returns true if the model supplied argument is valid or false if it is not valid



#build failure result
#builds a failure return dictionary so its all in the same format



#confirm review stage
#makes sure that the browser is on the review stage and and review card is visible. It will return a failure result
# if the browser is not on the review stage or if the review card is not visible.
def confirm_review_stage(page):
    if page is None:
        return False, "No browser page was provided."

    expected_url = "https://onyourmark.github.io/browser-agent-form/travel/"

    actual_url = page.url.split("#")[0].split("?")[0]

    if actual_url != expected_url:
        return False, f"Browser is not on the review stage. Expected URL: {expected_url}, but got: {actual_url}"

    review_stage = page.locator("#reviewStage")
    review_card = page.locator("#reviewCard")

    if not review_stage.is_visible():
        return False, "Review card is not visible on the page."

    if not review_stage.is_visible():
        return False, "Review stage is not visible on the page."

    return True, "Browser is on the review stage and review card is visible."



#read review card
#reads the review card and returns a dictionary of the information that is displayed on the review card. It will return
# a failure result if the review card is not visible.
def read_review_card(page):
    if page is None:
        return None, "No browser page was provided."

    card = page.locator("#reviewCard")

    if not card.is_visible():
        return None, "Review card is not visible on the page."

    labels = card.locator("dt")
    values = card.locator("dd")

    label_count = labels.count()
    value_count = values.count()

    if label_count == 0 or label_count != value_count:
        return None, "Mismatch in the number of labels and values on the review card."

    review_info = {}

    for i in range(label_count):
        label = labels.nth(i).inner_text().strip()
        value = values.nth(i).inner_text().strip()

        if label == "" or value == "":
            return None, f"Empty label or value found at index {i}."

        review_info[label] = value

    required_fields = [
        "Route",
        "Date",
        "Flight",
        "Seat",
        "Passenger",
        "Email",
        "Checked bag",
        "Priority boarding",
        "Mock total"
        ]

    for label in required_fields:
        if label not in review_info:
            return None, f"Missing required field '{label}' on the review card."

        if review_info[label] == "":
            return None, f"Required field '{label}' is empty on the review card."

    return review_info, "Successfully read the review card."
    


#compare review to goal
#compares the information on the review card to the information from the goal screen and returns a boolean indicating whether
# they match. It will return a failure result if the review card is not visible or if the information on the review card does 
# not match the information from the goal screen.



#run function
#main tool to validate the model argument and check the trusted goal in context and confirm that the review screen is visible.
#must be able to read the values from the review card and compare the actual values to the goal and then return the dictionary result.