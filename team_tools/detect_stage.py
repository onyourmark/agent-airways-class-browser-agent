"""Step 1 of detect_stage: validate the caller's argument.

The tool accepts an empty dictionary. The caller cannot provide its own stage.
Browser observation through run(page, argument, context) comes in a later step.
"""


def validate(argument):
    """Return (whether valid, a short explanation), without opening a browser."""
    if type(argument) != dict:
        return False, "argument must be an empty dictionary."
    if argument != {}:
        return False, "detect_stage accepts only an empty dictionary."
    return True, "The empty argument dictionary is valid."
