import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from team_tools.check_review_against_goal import validate

print(validate({}))     # Expect True
print(validate({"seat":"1C"}))     # Expect False
print(validate(None))     # Expect False
print(validate([]))     # Expect False