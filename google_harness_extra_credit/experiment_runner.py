import sys, json, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import browser_agent as agent
import browser_tools as bt
out = HERE
original_close = bt.close_browser
run_number = 0
def capture_and_close():
    try:
        if bt.page is not None:
            bt.page.screenshot(path=str(out / f'run_{run_number}.png'), full_page=True)
    finally:
        original_close()
bt.close_browser = capture_and_close
results = []
for n in range(1, 6):
    run_number = n
    agent.TRACE_FILE = out / f'run_{n}_trace.json'
    print(f'EXPERIMENT {n}', flush=True)
    with (out / f'run_{n}_console.txt').open('w') as log:
        old_stdout = sys.stdout
        sys.stdout = log
        try:
            result = agent.run_agent()
        except Exception as exc:
            traceback.print_exc(file=log)
            result = f'exception: {exc}'
        finally:
            sys.stdout = old_stdout
    results.append({'run': n, 'result': result})
    (out / 'results.json').write_text(json.dumps(results, indent=2))
    print(f'EXPERIMENT {n}: {result}', flush=True)
