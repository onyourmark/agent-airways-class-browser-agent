# Team 11: select_seat

Members: Mingyu Gao (`coldhac`) and Mengyu Wu (`Abigalemy`; commit author `mengyu0102`).

## Interface and scope

`team_tools/select_seat.py` follows the shared team interface:

Example model proposal (the tests call Python directly):

```json
{"action": "select_seat", "argument": {"seat": "1A"}}
```

```python
from team_tools.select_seat import validate, run

argument = {"seat": "1A"}
valid, note = validate(argument)
if valid:
    result = run(page, argument, {})
else:
    print(note)
# result always contains ok (bool), message (str), and data (dict).
```

`validate(argument)` requires exactly one `seat` key containing a positive row
number and one uppercase letter. It rejects malformed values instead of silently
normalizing them. `run(page, argument, context)` repeats validation for direct
callers; this tool does not need any context values.

The caller must already be on the permitted Agent Airways practice URL with the
seat stage visible. The tool scopes its exact seat match to
`#seatMap button.seat[data-seat]` within that stage. Missing, hidden, ambiguous,
and unavailable targets are refused; it does not select the first of duplicates.
Missing or ambiguous verification controls also cause refusal before clicking.

After clicking, the tool reads the uniquely selected seat's actual `data-seat`,
`#seatMessage`, and Continue's enabled state. It returns success only when all
three confirm the requested seat. A click alone does not establish success.
It never clicks Continue or performs another team's browser action.

## Run the checks

From the repository directory, with Python 3.10 or newer:

```sh
python -m pip install -r requirements.txt
python -m playwright install chromium
python tests.py
python -m team_tests.test_select_seat --evidence evidence/team11_select_seat.json
```

Add `--headed` to show Chromium. The test file also has a runnable `main()`:

```sh
python team_tests/test_select_seat.py --headed
```

The tests navigate through flight search and selection only to prepare the real
seat stage. They call the tool directly; no model service is required.

## Independent evidence and expected results

The required normal case selects **1A**. Separate test code then reads the DOM:
one selected 1A button, `Selected seat 1A.`, Continue enabled, and the seat stage
still visible. The required failure case requests unavailable **1B** and checks
that 1A, its message, Continue, and the current stage remain unchanged.

The repaired suite passed all 14 browser cases: stage not ready; 1A success; 1B
unavailable; missing 99Z; reselection to 2A; repeated selection; non-dictionary
input; unexpected key; duplicate seat; hidden seat; disabled seat; missing
Continue; a click whose handler does not select the seat; and an unapproved URL.
It also checks eight malformed inputs through `validate`, alongside the starter's
nine offline checks in `tests.py`.

Robustness cases deliberately alter the test browser DOM or change the same-origin URL path through browser history. The required 1A/1B cases use the unmodified live practice page.
Rejected requests must preserve the independently observed browser state. The
post-click verification case blocks the site handler, independently confirms
that 2A remains selected, and requires `ok: false` for the requested 1A.

The optional JSON trace records each proposal, tool return, independent before
and after snapshots, environment versions, timestamps, and pass status. The
current repair passed 14 browser cases, eight malformed-input checks, and nine
offline checks. The regenerated evidence records the run on 2026-10-20 using
Python 3.10.7, Playwright 1.64.0, and Chromium 156.0.8078.4.
The existing GitHub workflow runs only the starter's offline checks.

## Limitations and participation

This tool handles one seat per call and depends on the practice site's current
IDs, selected CSS class, and English message. Live tests require network access
and Playwright Chromium. Central dispatcher integration remains for the TA.
If verification fails after a click, the tool reports the observed failure and
does not promise to roll back the selection.

Mingyu Gao (`coldhac`) prepared the initial tool, tests, and evidence and
coordinated the corrections addressing the TA's six review points. Mengyu Wu
(`Abigalemy`, commit author `mengyu0102`) contributed subsequent implementation,
test, and README revisions.
The contribution is submitted for TA review in
[PR #16](https://github.com/onyourmark/agent-airways-class-browser-agent/pull/16).
The complete [PR description](PR_select_seat.md) includes the model proposal,
run commands, actual results, team contributions, and limitations.
