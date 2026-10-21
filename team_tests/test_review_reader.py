import os
import sys

from playwright.sync_api import sync_playwright

project_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(0, project_folder)

from team_tools.check_review_against_goal import check_review_against_goal

