# Google Harness Extra Credit

## 1. Connection to Google's harness

Google's course describes a harness as the software around an AI model that gives it context, connects tools, enforces permissions, and manages the loop that decides when to continue, stop, or ask for help. My browser agent uses Python as this harness. The model suggests one action at a time. Python checks the response format and whether the action is allowed, runs the browser tool, and sends the observation back to the model. It also limits the agent to eight steps. The model's claim that it is done is never trusted on its own: Python checks the real page before accepting success.

The table below maps the agent to the four parts of the course.

| Course part | What my agent does | What it does not cover |
| --- | --- | --- |
| Context and memory | The `messages` list acts as the session: it holds the goal, the model's replies, and the observations. `step`, `finished`, and `stop_reason` act as state that the code reads directly. | There is no long-term memory, so every run starts fresh. This kept the five runs independent. |
| Tools and execution flow | Three Python function tools (`open_site`, `read_page`, `done`) run in a fixed loop, with an eight-step limit that stops a stuck run. | No MCP server, graph workflow, or parallel checks. |
| Runtime, security, and privacy | Permissions are enforced in code, not just the prompt: `open_site` takes no URL argument and always uses the fixed practice URL, so injected page text cannot use this tool to send the agent to another address. Page text is labeled as webpage data, not instructions. The model runs locally in Ollama, so page text is not sent to a hosted model. | This is a limited tool permission, not a complete defense against prompt injection. There is no sandbox beyond a fresh browser on a fake practice site, and page text is saved in the trace files. |
| Evaluation | A deterministic check, `check_goal()`, decides success. I also reviewed the traces myself, which is how the cause of the failures was found (see Section 4). | No LLM-as-judge was used. |

## 2. How success is checked

The class starter version of my agent has a small goal: open and identify the Agent Airways practice page. It does not fill in or submit a booking form.

When the model proposes `done`, Python reads the actual browser page. The `check_goal()` function requires all three values to match exactly:

| Item | Required value |
| --- | --- |
| URL | `https://onyourmark.github.io/browser-agent-form/travel/` |
| Title | `Agent Airways Lab` |
| Main heading | `Agent Airways` |

Only then does Python record `stop_reason: "success"`. The model saying “done” is not enough. If the check fails, feedback goes back to the model. If eight steps are used without accepted success, the program records `budget_exceeded`. Some model errors cause it to stop with `model_error`.

The intermediate `check_result` after opening or reading the page checks only the URL. The complete three-part check is performed when the model proposes `done`.

## 3. Five experiments

The experiments used the code from the class starter repository, with Ollama's `qwen3:8b` model and Playwright Chromium. The agent source was unchanged between runs. Each run started a separate browser with a new, empty browser context and blank page, so previous browser state was not reused. The reset method was a fresh browser context, rather than clicking the site's Reset trip button.

An external runner called the same agent five times, saved each trace separately, and captured the final page before closing the browser. It changed the trace output path and wrapped browser cleanup to take the screenshot. It did not change the goal, model, tools, prompts, validation, or success check. The runner and source checksums are included for transparency.

| Run | Success or Failure | Notes | Evidence |
| --- | --- | --- | --- |
| 1 | Failure | Page opened, but the URL included `#search`. Python rejected `done`; the agent stopped after eight steps with `budget_exceeded`. | [Screenshot](run_1.png), [trace](run_1_trace.json), [console](run_1_console.txt) |
| 2 | Failure | Page opened, but the URL included `#search`. Python rejected `done`; the agent stopped after eight steps with `budget_exceeded`. | [Screenshot](run_2.png), [trace](run_2_trace.json), [console](run_2_console.txt) |
| 3 | Failure | Page opened, but the URL included `#search`. Python rejected `done`; the agent stopped after eight steps with `budget_exceeded`. | [Screenshot](run_3.png), [trace](run_3_trace.json), [console](run_3_console.txt) |
| 4 | Failure | Page opened, but the URL included `#search`. Python rejected `done`; the agent stopped after eight steps with `budget_exceeded`. | [Screenshot](run_4.png), [trace](run_4_trace.json), [console](run_4_console.txt) |
| 5 | Failure | Page opened, but the URL included `#search`. Python rejected `done`; the agent stopped after eight steps with `budget_exceeded`. | [Screenshot](run_5.png), [trace](run_5_trace.json), [console](run_5_console.txt) |

Runs 1, 3, 4 and 5 produced byte-identical traces because the model gave the same replies and the trace has no timestamps. Run 2 differs in the wording of its `done` explanation. The console logs differ in their saved paths. Runs 1, 3, 4 and 5 also have byte-identical screenshots because they captured the same rendered page.

**Result: 0 of 5 runs met the program's success check.** All five opened the expected page, but none was accepted as successful by Python.

**Test logs:** Each run has two logs in this folder. `run_N_console.txt` is the full terminal output, and `run_N_trace.json` is the agent's step-by-step trace (model reply, parse and validation results, browser observation, check result, and stop reason). `results.json` summarizes the stop reason of all five runs.

## 4. Findings and limitations

All five runs failed for the same reason. The browser reported `https://onyourmark.github.io/browser-agent-form/travel/#search`, but the code expected the URL without `#search`. The title and heading matched the expected values in the recorded page observations, but the success function rejected the URL first. After Python rejected `done`, the model tried opening the page again. This did not solve the mismatch, and every run reached the eight-step limit.

Relative to the intended goal of opening and identifying the page, these results are false negatives from the evaluator, rather than failures to reach the page. The model reached the right page and proposed `done` with reasoning supported by the title and heading, but the deterministic URL check was too strict. Google's course warns that an LLM judge can be wrong. These experiments show that a code check can also give the wrong decision for the intended goal, so the checker needs its own tests. The feedback only said that the browser was not on the allowed URL; it never showed the expected and actual URLs. Reopening the page did not fix the fragment mismatch, and no available action could change the checker or explicitly remove the fragment.

The automated check could not explain its own mistake. I found the cause by reading the traces and comparing the observed URL with the expected one. This matches the course's point that human review catches what automated checks miss, and that the different kinds of evaluation work best together.

I learned that reliability depends on the Python checks as well as the model. A check can be too strict and reject a page that otherwise matches the intended goal. One possible improvement is to compare the expected scheme, host, and path while allowing the known `#search` fragment. This improvement was not applied during the experiments. It would need a separate set of tests.

These experiments only tested opening and identifying one page. They do not show that the agent can submit a booking or verify passenger details. Five runs on one website with one model also provide limited evidence about reliability in other situations. The screenshots show the final browser page; the traces provide the evidence for the program's failure decision.

## Sources

- [Google AI Harness course](https://g.dev/ai/ai-harness), including the AI Harness Crash Course video transcript.
- `browser_agent.py` and `browser_tools.py` from the class starter repository.

## Running the evidence runner

Place this `google_harness_extra_credit` folder at the root of the class starter repository, beside `browser_agent.py` and `browser_tools.py`. With the original dependencies, Chromium, Ollama, and `qwen3:8b` available, run `python3 google_harness_extra_credit/experiment_runner.py` from the repository root. It saves evidence beside the runner and overwrites the existing run files, so preserve the original evidence before rerunning. When run in a terminal, each run waits for Enter after it finishes, but the prompt is written to the console log rather than the screen, so press Enter when a run appears to pause. The console logs retain the original execution paths as part of the evidence.