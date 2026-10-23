# list_interactive_elements test results

```text

=== Part 1: validation (no browser) ===
PASS: {} is accepted
       validate() said: Validation succeeded.
PASS: {'x': 1} is rejected
       validate() said: This tool takes no arguments. Unexpected keys: x
PASS: '' is rejected
       validate() said: The argument must be a dictionary, such as {}.
PASS: None is rejected
       validate() said: The argument must be a dictionary, such as {}.

=== Failure test: bad argument never reaches run() ===
PASS: {"selector": "#x"} is rejected
       VALIDATION ERROR: This tool takes no arguments. Unexpected keys: selector
PASS: run() was never called
       run() calls recorded: 0
PASS: run() refuses the bad argument on its own too
       This tool takes no arguments. Unexpected keys: selector

=== Part 2: search screen ===
PASS: run() returns ok: True
       Found 6 visible controls.
       stage: searchStage | url: https://onyourmark.github.io/browser-agent-form/travel/#search
PASS: fromAirport (select) is listed
       reported: {'id': 'fromAirport', 'kind': 'select', 'label': 'From', 'value': '', 'enabled': True, 'selected_text': 'Choose an airport'}
PASS: toAirport (select) is listed
       reported: {'id': 'toAirport', 'kind': 'select', 'label': 'To', 'value': '', 'enabled': True, 'selected_text': 'Choose an airport'}
PASS: departureDate (date) is listed
       reported: {'id': 'departureDate', 'kind': 'date', 'label': 'Departure date', 'value': '2026-10-24', 'enabled': True}
PASS: passengers (select) is listed
       reported: {'id': 'passengers', 'kind': 'select', 'label': 'Passengers', 'value': '1', 'enabled': True, 'selected_text': '1 passenger'}
PASS: searchFlights (button) is listed
       reported: {'id': 'searchFlights', 'kind': 'button', 'label': 'Search flights', 'value': None, 'enabled': True}

--- Independent check: tool value vs page.locator(...).input_value() ---
PASS: fromAirport value matches the page
       tool: '' | page: ''
PASS: toAirport value matches the page
       tool: '' | page: ''
PASS: departureDate value matches the page
       tool: '2026-10-24' | page: '2026-10-24'
PASS: passengers value matches the page
       tool: '1' | page: '1'
PASS: searchFlights has no value (buttons hold none)
       tool: None

--- Independent check: read-only (values before and after run()) ---
PASS: fromAirport unchanged by run()
       before: '' | after: ''
PASS: toAirport unchanged by run()
       before: '' | after: ''
PASS: departureDate unchanged by run()
       before: '2026-10-24' | after: '2026-10-24'
PASS: passengers unchanged by run()
       before: '1' | after: '1'
PASS: still on the search screen after run()
       url: https://onyourmark.github.io/browser-agent-form/travel/#search

=== Part 3: later screen (seat map) ===
In the open browser window, by hand:
  1. Choose From and To airports (different ones), then Search flights.
  2. Choose any flight.
  3. Stop on the seat map. Do NOT pick a seat.
Press Enter here when the seat map is showing... PASS: run() returns ok: True
       Found 32 visible controls.
       stage: seatStage | url: https://onyourmark.github.io/browser-agent-form/travel/#search
PASS: tool reports the seat stage
       stage: 'seatStage'
PASS: seat 1B is listed
       reported: {'id': '', 'kind': 'button', 'label': 'Seat 1B unavailable', 'value': None, 'enabled': False, 'seat': '1B'}
PASS: seat 1B shows as disabled
       tool enabled: False | page is_enabled(): False
PASS: Continue button is listed
       reported: {'id': 'continueFromSeat', 'kind': 'button', 'label': 'Continue', 'value': None, 'enabled': False}
PASS: Continue button shows as disabled
       tool enabled: False | page is_enabled(): False
PASS: no search-screen controls are listed
       search controls found: []

=== Failure test: off-site page (about:blank) ===
PASS: run() on about:blank returns ok: False
       url: about:blank | message: The browser is not on the permitted Agent Airways page.
PASS: no controls are reported
       elements: []

=== Summary ===
Passed: 32 | Failed: 0
```
