import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from team_tools.check_review_against_goal import check_goal

# A complete goal example (given in github issue)
good_goal = {
    "from": "DCA", "to": "BOS", "date": "2026-11-04",
    "flight_id": "AA101", "seat": "1A",
    "passenger": "Alex Student", "email": "alex@example.com",
    "checked_bag": False, "priority_boarding": False
}

# Test 1
print("Test 1: ", check_goal({"goal":good_goal}))

# Test 2
print("Test 2: ", check_goal({}))

# Test 3
del(good_goal["checked_bag"])
print("Test 3: " , check_goal({"goal":good_goal}))



