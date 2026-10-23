# Manual detect_stage demonstration

This demonstration checks all six stages while you operate the Chromium window
opened by Python. It opens the fixed Agent Airways practice site, then waits for
you to navigate. Each check calls `run(page, {}, {})` and independently reads the
visible section, heading, and loading indicator. No language model is required.

## Install and run

Open a terminal in the repository root, the folder containing `browser_tools.py`.
Use Python 3.10 or newer. If dependencies and Chromium are already installed in
your active Python environment, skip the installation commands.

Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m team_tests.demo_detect_stage
```

macOS or Linux with a desktop:

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m team_tests.demo_detect_stage
```

Keep the terminal and the script's Chromium window open. Perform every click in
that window. A separately opened Chrome tab is not connected to this script.
Return to the terminal and press Enter when each requested screen is ready.
The script checks the screen; it does not click the next button for you.

## Six checkpoints

| Expected stage | What to do in the Playwright browser before pressing Enter |
| --- | --- |
| `search` | Leave the opening Search for a flight screen visible. |
| `results` | Choose From **DCA**, To **BOS**, keep the supplied date and one passenger, then click **Search flights**. Wait for flight cards. Do not choose a flight yet. |
| `seat` | Click **Choose AA101**. Leave the seat map visible. |
| `passenger` | Select available seat **1A** and click **Continue**. Leave Passenger information visible. |
| `review` | Enter **Alex Student** and **alex@example.com**, then click **Continue to review**. Stop before confirmation. |
| `confirmation` | Check the details box and click **Confirm reservation** on this practice site. Leave **RESERVATION CONFIRMED** visible. |

Use the synthetic name and email above. The final button completes only the
practice page's pretend reservation. Stage detection does not establish that
every reservation detail is correct.

## Read the results and retry

For each attempt, the terminal prints the expected stage, tool call, returned
dictionary, independent browser evidence, and `PASS` or `FAIL`.

A passing attempt requires exactly one visible stage section, its ID matching
the expected stage, agreement between the tool and browser loading state, and
unchanged URL and HTML during the observation. The heading is also recorded.
The expected stage is used only by this demonstration's check; the tool always
receives the empty argument dictionary `{}`.

To try a recovery case, press Enter at the `results` prompt while the search
screen is still visible. The script should print `FAIL`, record that attempt,
and remain at the `results` checkpoint. Perform the search, wait for the cards,
then press Enter again. The next attempt should pass.

If a page changes while it is being checked, wait for it to settle and retry.
Results loading usually lasts only about 1.2 seconds, so a manual run may miss
`loading=True`. Use `python -m team_tests.test_detect_stage_loading` for the
existing controlled loading-state tests.

Enter `q` to stop early. Ctrl+C or end-of-input also leaves the demonstration
incomplete. If Chromium was closed, enter `q` and restart the script. A failed
check never advances to the next checkpoint.

## Saved report

The script closes its browser and writes `artifacts/manual-stage-demo.json`.
`completed: true` means all six checkpoints were eventually verified. Earlier
failed attempts remain in `attempts`; completion does not erase them.
An interrupted or early-exit run has `completed: false` and exits with status 1.
A completed run exits with status 0.

Each run replaces this file. Copy it elsewhere if you want to keep an earlier
run. The `artifacts/` directory is ignored by Git; review the contents before
choosing any evidence for submission. Record each student's actual participation
separately in the final pull request.

## Automated script verification

Run `python -m team_tests.test_detect_stage_demo` to check the demonstration's
retry, completion, early-exit, input-ending, and closed-page behavior. This test
uses real Chromium with scripted actions and prompt responses. Its report at
`artifacts/manual-demo-smoke-step6.json` is automated test evidence, not a record
of students performing the manual demonstration.
