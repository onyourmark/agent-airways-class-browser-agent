"""Step 1: test argument validation without a browser or language model."""

from team_tools.detect_stage import validate


def main():
    cases = [
        ("empty dictionary accepted", {}, True),
        ("caller cannot announce its own stage", {"stage": "seat"}, False),
        ("unexpected argument rejected", {"unexpected": True}, False),
        ("None rejected", None, False),
        ("empty list rejected", [], False),
        ("empty string rejected", "", False),
        ("Boolean rejected", False, False),
        ("number rejected", 0, False),
    ]

    for name, argument, expected in cases:
        result = validate(argument)
        # Check the shared interface as well as the expected validation outcome.
        assert type(result) == tuple and len(result) == 2, name
        valid, message = result
        assert type(valid) == bool and valid is expected, name
        assert type(message) == str and message.strip() != "", name
        print("PASS:", name, "->", result)

    print("All 8 detect_stage validation checks passed.")


if __name__ == "__main__":
    main()
