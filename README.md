# Shared Browser Agent Project

**Introduction to Agentic AI | Online and in-person sections | Student repository**

This is the **shared student codebase** for our multi-week group project. We will build a small browser agent together, then develop an evaluation laboratory to test and improve it.

The website used for practice is [Agent Airways](https://onyourmark.github.io/browser-agent-form/travel/). It is a **simulation**. It does not purchase tickets or send a real reservation.

## Start programming in class

**Start with [START_PROGRAMMING.md](START_PROGRAMMING.md) and [practice_dropdown.py](practice_dropdown.py).**

This is the first hands-on exercise. You will write Python code that changes the departure airport, destination, and passenger count on the real Agent Airways practice page. It needs only Playwright and Python, **not** Ollama or the language model. You may work on it while project partners are being assigned.

## Starting point

This repository starts with a **working but deliberately limited** agent.

- `browser_agent.py`: model calls, parser, validator, agent loop, state, trace, and stopping check
- `browser_tools.py`: two starting actions (`open_site` and `read_page`), plus browser setup and observation
- `tests.py`: nine offline checks, including invalid proposals and premature success
- `CONTRIBUTING.md`: how teams submit and review their work
- `PROJECT_BACKLOG.md`: candidate team contributions
- `.github/workflows/tests.yml`: basic automated tests for pull requests

The starter's only task is to open the practice site and verify that it reached the correct page. **It cannot book a pretend flight yet.** That is intentional: student teams will add more capabilities over time. The earlier Wikipedia and form assignments remain useful examples of the same agent loop.

## Install on your own computer

Use Python 3.10 or newer, VS Code, and a visible desktop. Install [Ollama](https://ollama.com/download) and then run:

```text
ollama pull qwen3:8b
```

Download or clone this repository, open a terminal in its folder, and install Python dependencies.

Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
python tests.py
python browser_agent.py
```

macOS (if your Python command is `python3`):

```sh
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 tests.py
python3 browser_agent.py
```

Ollama must be running locally at `http://localhost:11434`. The model can run slowly on CPU-only machines. The offline tests do not require Ollama, Chromium, or network access to the practice site.

The agent opens a visible browser and writes `run_trace.json` when it stops. Inspect that file to see the model decisions, validation results, browser observations, checks, state updates, and stopping reason.

## The rule for every team contribution

Each contribution must include all four parts:

1. **Capability:** one new browser tool or well-defined improvement to an existing capability.
2. **Validation:** checks on the model's proposed action and arguments **before** the action runs.
3. **Observation / verification:** meaningful evidence returned **after** the action, including failure where appropriate.
4. **Tests:** at least one normal case and one failure/edge case, with trace evidence for browser-driven features.

**A successful demo alone is not sufficient.** A valid pull request needs understandable code, tests, and an honest explanation of what the checks establish.

## How teams collaborate

Both course sections use this same repository, but students do **not** edit `main` directly.

1. Each team receives one GitHub issue describing its capability.
2. Team members create a fork or an approved team branch.
3. They work together outside class and run the tests.
4. They open **one pull request** referring to their assigned issue.
5. Another team or the TA reviews it; the instructor or designated maintainer approves the merge.
6. After merging, everyone updates their own copy of the repository.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact process. Do not add real credentials, payment details, personal data, or browser profiles to the repository.

## The project has two phases

**Phase 1: Browser capabilities.** Teams add navigation, form interaction, tab management, page understanding, error handling, and better evidence checks.

**Phase 2: Browser evaluation laboratory.** Teams create normal, failure, and adversarial cases; inspect traces; diagnose faults; improve the agent; and rerun the same cases to see whether it improved.

We are developing a **teaching and research prototype**, not a commercial airline agent or a general-purpose system allowed to perform purchases. Broader websites and any externally consequential actions require approval and appropriate safeguards.

## In-person team: detect_stage progress

Development branch: `team2-detect-stage`. This tool is being built in small steps.

**Step 1 completed:** `team_tools/detect_stage.py` provides `validate(argument)`.
Only `{}` is accepted; a caller-supplied stage and malformed arguments are rejected.
Run its eight offline checks with `python -m team_tests.test_detect_stage`.

**Next steps:** implement visible-stage detection through `run(page, argument, context)`,
then add loading-state checks, browser failure cases, and the manual demonstration.
Browser-stage detection is not implemented in this first step.

## Instructor note on GitHub protection

The course rule is that pull requests are reviewed before merge. Repository settings must separately enforce that rule: GitHub Settings > Branches / Rulesets should protect `main`, require pull requests, and (once configured) require the tests check to pass. A documented rule is not the same thing as an enforced GitHub setting.
