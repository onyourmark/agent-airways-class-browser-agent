## Assigned capability

Section 06, Team 11: `select_seat`, assigned to Mingyu Gao and Mengyu Wu in the
companion team assignment. No separate Team 11 issue was provided.

## Behavior and integration

Select one available seat on the Agent Airways practice page without advancing
to passenger information. `team_tools/select_seat.py` exports
`validate(argument)` and `run(page, argument, context)`; every result contains
`ok`, `message`, and `data`. The common agent and other teams' tools are unchanged;
the assignment reserves central dispatcher integration for the TA.

```json
{"action": "select_seat", "argument": {"seat": "1A"}}
```

Validation requires exactly one `seat` key, a positive row number followed by one
uppercase letter. Direct calls to `run` are validated too. The runner checks the
permitted URL, visible seat stage, and unique available match using
`#seatMap button.seat[data-seat]`. Missing, hidden, duplicate, disabled, or
unavailable targets are refused rather than selecting the first match.

After a click, Python reads the selected button's `data-seat`, actual seat
message, and Continue's enabled state. All three must agree before success.
Missing or ambiguous verification controls are refused before the click.
Playwright errors and inconsistent read-back produce explicit failed results.

## Tests and evidence

- [x] Existing nine offline checks passed.
- [x] Required 1A success and 1B failure demonstrated on the live practice site.
- [x] Independent Python verification and recorded JSON evidence included.
- [x] Only one assigned tool implemented, using simple synchronous Python.
- [x] No credentials, student contact details, payment data, or real bookings added.

Run from the repository directory:

```sh
python -m pip install -r requirements.txt
python -m playwright install chromium
python tests.py
python -m team_tests.test_select_seat --evidence evidence/team11_select_seat.json
```

For a visible browser, add `--headed`. The direct entry point also works:
`python team_tests/test_select_seat.py --headed`. No model service is needed.

The repaired suite passed all 14 browser cases, eight malformed validation
inputs, and the existing nine offline checks. Evidence was regenerated on
2026-10-20 with Python 3.10.7, Playwright 1.64.0, and Chromium 156.0.8078.4.
See `team_tests/README_select_seat.md` and `evidence/team11_select_seat.json`.

- Required success: select 1A; separate DOM reads must find only 1A selected,
  `Selected seat 1A.`, enabled Continue, and the seat stage still visible.
- Required failure: request unavailable 1B; independent before/after reads must
  confirm the previous 1A selection, message, Continue, and stage are unchanged.
- Additional cases cover malformed input, stage readiness, missing seats,
  reselection, repeated selection, duplicate/hidden/disabled seats, missing
  Continue, a click without actual selection, and an unapproved URL.

The required 1A/1B cases use the unmodified live page. Controlled robustness cases
alter the test browser DOM or change its same-origin path using browser history;
no other website is contacted. Blocking the seat click handler leaves 2A
selected and requires `ok: false` for the requested 1A.
Evidence records proposals, actual returns, independent DOM snapshots, versions,
and timestamps. The existing CI runs the starter's offline checks only.

## Team participation

- Mingyu Gao (`coldhac`): initial tool implementation, tests, and evidence;
  coordinated the corrections addressing the TA's six review points.
- Mengyu Wu (`Abigalemy`, commit author `mengyu0102`): subsequent implementation,
  test, and README revisions.

## Known limitations

One seat per call; the seat stage must already be prepared. The tool depends on
the practice site's current IDs, selected CSS class, and English seat message.
It never clicks Continue. Failed verification after a click does not guarantee
rollback. Live tests require network access and installed Playwright Chromium.
No credentials, payment data, or real reservation activity are involved.
