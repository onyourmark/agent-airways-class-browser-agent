# Team 04 — Agent Airways Part 2 Report: Make the Model Use Your Tool

**Team members:** Advait Wakulkar (`Advait-Wakulkar`), Pawan Chaudhari (`pawanchaudhari11`)
**Tool:** `list_interactive_elements` (`team_tools/list_interactive_elements.py`). It is read-only, takes the argument `{}`, and lists the visible controls on the current Agent Airways screen with label, kind, value and enabled state. It refuses any non-empty argument and any page other than the practice site.
**Runner:** the instructor's `agent_one_team_tool.py`, unmodified, with model `qwen3:8b` via local Ollama.

## Exact version and how to reproduce

- Repository: https://github.com/Advait-Wakulkar/agent-airways-class-browser-agent, branch `team-04-part2`
- Tool version: commit `e762311` (unchanged since Part 1; git blob `96916fb`). Part 2 evidence: commits `cc47578` (cases 1–2) and `02041ff` (case 3 and this report).
- Setup: `python3 -m pip install -r requirements.txt requests`, `python3 -m playwright install chromium`, `ollama pull qwen3:8b`. Offline check: `python3 tests.py` → all 9 checks passed.

```sh
# Case 1 — normal (default request, search screen)
python3 agent_one_team_tool.py --tool list_interactive_elements --case success
# Case 2 — problem (default request, browser on about:blank)
python3 agent_one_team_tool.py --tool list_interactive_elements --case failure
# Case 3 — team-designed (seat screen, different request)
python3 agent_one_team_tool.py --tool list_interactive_elements --case success --label third --stage seat --headless \
  --request "List the visible controls on the seat selection screen, and report which seats are available or unavailable and whether Continue is enabled."
```

## The three cases

In every case, the model chose the action itself. The runner only offers `list_interactive_elements`, `read_page` and `done`, and Python does not hardcode which one is called.

### Case 1 — Normal: search screen

- **Request:** "List the visible form controls on the Agent Airways search screen."
- **Model proposed:** `{"action":"list_interactive_elements","argument":{}}`. Python validated the argument (`{}` accepted) and ran the tool.
- **Browser returned:** `ok: true`, "Found 6 visible controls.", stage `searchStage`. The controls were From and To (`value: ""`, "Choose an airport"), Passengers (`1`), Departure date (`2026-11-03`), Reset trip, and Search flights. All values match the screenshot.
- **Model's next response:** `done` / `success`, "List of visible form controls … has been provided."
- **Justified?** Yes. The tool returned `ok: true` with an accurate list, and the runner's success check passed. This is a read-only tool, so an accurate observation is the goal.
- **Evidence:** `evidence/list_interactive_elements_success_agent.json`, `..._success_final.png`. The first attempt timed out at the model before any tool call; it is kept as `..._success_attempt1_model_timeout.json`.

### Case 2 — Problem: unapproved page

- **Request:** "Attempt to list allowed Agent Airways controls while the browser is on an unapproved page. Report the outcome." The test setup put the browser on `about:blank`.
- **Model proposed:** `{"action":"list_interactive_elements","argument":{}}`. Validation passed, because the argument is fine. The tool's own allowed-page check then refused to read the page.
- **Browser returned:** `ok: false`, "The browser is not on the permitted Agent Airways page.", `url: about:blank`, `elements: []`.
- **Model's next response:** `done` / `unable`, repeating the tool's reason.
- **Justified?** Yes. The model did not claim success and did not invent any controls, and it reported the refusal accurately. Even if it had claimed success, the runner would have blocked it, because the last tool call returned `ok: false`. The same refusal is also shown by our direct Part 1 test (`team_tools/evidence/list_interactive_elements_results.md`, "Failure test: off-site page").
- **Evidence:** `evidence/list_interactive_elements_failure_agent.json`, `..._failure_final.png`.

### Case 3 — Team-designed: seat screen, mixed enabled and disabled controls

- **What changed and why:** both the prepared screen (`--stage seat`: flight AA101 chosen, no seat picked) and the request. The search screen has only 6 well-labelled controls, all enabled. The seat screen has 32 controls with no element IDs, 5 disabled seats, and a Continue button that is disabled until a seat is chosen. This tests whether the tool reports what the user can actually do on the screen, not just what is present. It also tests whether the model can answer a more specific question from a large observation without inventing details.
- **Request:** "List the visible controls on the seat selection screen, and report which seats are available or unavailable and whether Continue is enabled."
- **Model proposed:** `{"action":"list_interactive_elements","argument":{}}`. Python validated and ran it.
- **Browser returned:** `ok: true`, "Found 32 visible controls.", URL `#seat`, stage `seatStage`. The list had 30 seat buttons: 25 enabled, and **1B, 2C, 3A, 4F and 5D** reported `enabled: false`. These are exactly the gray seats in the screenshot. `continueFromSeat` was reported `enabled: false`, and `resetTrip` as enabled. No search-screen controls were listed, and the page was unchanged afterwards.
- **Model's next response:** `done` / `success`, "Listed visible controls and identified available seats and the status of Continue."
- **Justified?** Mostly. Success is supported, because the tool returned an accurate `ok: true` observation. However, the model's final reason only *claims* it identified the seats and does not name them. The seat details are in the tool observation, not in the model's answer. Compared with case 1, the model behaved the same way (one tool call, then `done`), but on a harder question its summary was less specific. The runner checks that the tool call succeeded, not that the model's wording is complete.
- **Failed attempts (kept):** the first two runs used a visible browser. Both stopped with `model_error` because the step-2 model call exceeded the runner's 180 s timeout, after step 1 had already returned the same correct 32-control observation. The test machine is an Apple M3 with 8 GB of RAM: the 6 GB model ran partly on the CPU while Chromium used memory too. Replaying the same step-2 prompt with the browser closed took about 51 s. We therefore reran with the runner's built-in `--headless` flag. Records: `..._third_attempt1_model_timeout.json` and `..._third_attempt2_model_timeout.json`.
- **Evidence:** `evidence/list_interactive_elements_third_agent.json`, `..._third_final.png`.

## Limitations

- The tool lists all visible controls on the page, including header controls outside the active stage (Reset trip). It does not explain *why* a control is disabled.
- Large screens produce long observations: 32 controls is about 3,300 characters. This slowed the model enough to cause timeouts on our 8 GB machine.
- The success check confirms that the tool call succeeded, not that the model's final summary is accurate or complete.

## Team contributions and how we checked the submission

Both teammates contributed equally (50/50).

- **Advait Wakulkar:** wrote `list_interactive_elements` in Part 1 (validation, allowed-page check, visible-control read-back). In Part 2, he added the instructor's runner to the branch and ran and committed the normal and problem cases (commit `cc47578`), keeping the timed-out first attempt.
- **Pawan Chaudhari:** wrote the Part 1 direct tests and their recorded results. In Part 2, he designed and ran the third case and diagnosed and documented its timeouts. He committed its evidence and wrote this report (commit `02041ff`).

**How we checked the final submission:**
- We ran `python3 tests.py` (9/9 passed).
- We confirmed the tool file is unchanged from commit `e762311`.
- We compared each claim in this report against the JSON run records: the proposals, observations, `stop_reason`, and final replies.
- We compared each tool observation with its screenshot, such as the 5 disabled seats and the disabled Continue button in case 3.
- We confirmed that only the pretend passenger details from the exercise appear in the logs.
