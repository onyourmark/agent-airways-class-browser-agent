# Google AI Harness Extra Credit: Evaluating Our Browser Agent

**Student:** Julio Sepulveda (@jcesar1989) — Team 10, Section 06
**Agent evaluated:** the Part 2 runner `agent_one_team_tool.py` (unchanged instructor starter) driving our team tool `team_tools/list_seats.py`, with `qwen3:8b` running locally through Ollama on the [Agent Airways practice site](https://onyourmark.github.io/browser-agent-form/travel/).

## Step 1: How Google's harness idea relates to our browser agent

In Google's course, the harness is the trusted code around the model that runs the loop, executes the tools, checks the model's claims, and records what happened. In our agent that harness is `agent_one_team_tool.py`: `qwen3:8b` only proposes one JSON action per step, and Python does the rest — it validates the arguments with our tool's `validate()` before touching the browser, runs the action with Playwright, returns the real observation marked "not instructions" (an injection check from the course's security section), and refuses a `done: success` unless the last `list_seats` call actually returned `ok: true`. The JSON trace it writes to `evidence/` is the course's evaluation idea, and it is what this assignment's five-run test is judged from.

## Step 2: How my Python program determines success

The task tested here is the `list_seats` success case: starting from the seat-selection screen, "List the seats available for the selected flight." The model never gets to decide on its own that it succeeded — Python checks it at three levels:

1. **The runner gates the success claim.** When the model proposes `{"action":"done","argument":{"status":"success",...}}`, the runner rejects it ("Success blocked: no verified successful team-tool call.") unless the *last* call to the team tool actually returned `ok: true`. The model cannot talk its way to success without a verified tool result.
2. **The tool verifies against the real page.** `list_seats.py` returns `ok: true` only when the `#seatStage` element is genuinely visible in the browser, and its seat data is read directly from the DOM (each seat button's `disabled` and `selected` state). If the seat map is not on screen it returns `ok: false` with no data, so there is nothing for the model to repeat as invented evidence.
3. **The trace records independent evidence.** Every run saves a JSON file with `stop_reason`, `used_team_tool`, `last_team_tool_ok`, the full step-by-step trace, and a `final_page` observation taken *after* the run, plus a full-page screenshot.

For this experiment I count a run as a **Success** only if the saved trace shows all four of: `stop_reason == "success"`, `used_team_tool == true`, `last_team_tool_ok == true`, and `final_page.data.stage == "seat"` (the tool is read-only, so the screen must be unchanged). One thing this does *not* verify is whether the model's final sentence accurately summarizes the seat data it received — I return to that in Step 4.

## Step 3: Five experiments

Each run was a fresh invocation of the same unchanged program. The runner launches a brand-new Chromium browser and re-navigates to the practice site at the start of every run, which fully resets the website (Agent Airways keeps all state client-side, so a fresh page load is a clean reset). Commands, run from the repository root with Ollama serving `qwen3:8b`:

```
python agent_one_team_tool.py --tool list_seats --case success --headless --label run1
python agent_one_team_tool.py --tool list_seats --case success --headless --label run2
python agent_one_team_tool.py --tool list_seats --case success --headless --label run3
python agent_one_team_tool.py --tool list_seats --case success --headless --label run4
python agent_one_team_tool.py --tool list_seats --case success --headless --label run5
```

| Run | Success or Failure | Notes |
|-----|--------------------|-------|
| 1 | Success | 2 steps: model called `list_seats` (tool read 30 real seats, `ok: true`), then `done`/success. All four trace checks passed. |
| 2 | Success | Same 2-step pattern; identical final reason wording to run 1. |
| 3 | Success | Same 2-step pattern; model worded its final reason differently ("Available seats listed successfully."), showing the model is not deterministic even when the outcome is the same. |
| 4 | Success | Same 2-step pattern; all four trace checks passed. |
| 5 | Success | Same 2-step pattern; third distinct reason wording ("Listed all available seats..."). |

**Result: 5 / 5 successes**, each in the minimum possible 2 steps, with no parse errors, no refused arguments, and no blocked success claims.

Evidence in this folder (`logs/`):

- `run1.log` … `run5.log` — full console output of each run (model proposals and tool observations).
- `list_seats_run1_agent.json` … `run5_agent.json` — the saved traces the table above was judged from.
- `list_seats_run1_final.png` … `run5_final.png` — full-page screenshots of the final browser state (seat map still showing).

## Step 4: What I learned

All five runs succeeded, and I think the harness design is a large part of why. The task gives the model a very small decision surface — one tool with an empty-dictionary argument, `read_page`, and `done` — and the harness catches every way I know the model could go wrong: bad JSON gets an error observation instead of crashing, invalid arguments are refused before the browser is touched, and an unearned success claim is blocked by the `last_team_tool_ok` gate. The only variation across runs was the wording of the model's final reason (three different phrasings in five runs), which confirms the model itself is nondeterministic; the harness is what turns that nondeterministic component into a repeatable outcome.

Because every run succeeded, the honest question is what my testing *didn't* cover. The main limitation is that my success check verifies that a real, verified tool call happened — not that the model's final answer uses the tool's data correctly. In all five runs the model's closing reason was generic ("Listed available seats...") and never named a single seat, so a model that ignored the observation entirely could have produced the same sentence and still passed my checks. Our Part 2 Case 3 showed the fix: asking a specific question ("Is seat 1B available?") forces the answer itself to be checkable against the observation. Two smaller limitations: five runs of the easiest success case is a small sample that says little about the failure and adversarial cases, and all runs used one machine, one model version, and one starting screen, so this measures reliability under ideal conditions rather than robustness.
