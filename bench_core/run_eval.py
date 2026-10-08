"""Grade one run's deliverables against a task's rubric.

    python -m bench_core.run_eval --task <task-id> --output <dir> --judge-cmd "<command>"

The judge command receives the grading prompt on stdin and must print the
model's reply on stdout. That keeps the benchmark independent of any one
model provider. `--judge-cmd mock:pass` and `mock:fail` exist for testing the
pipeline without a model.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .scoring import score_task
from .tasks import TASKS_DIR, load


def make_judge(spec: str):
    if spec in ("mock:pass", "mock:fail"):
        verdict = spec.split(":")[1]
        return lambda prompt: json.dumps({"reasoning": "mock judge", "verdict": verdict})

    def run(prompt: str) -> str:
        done = subprocess.run(spec, shell=True, input=prompt, capture_output=True, text=True, timeout=600)
        return done.stdout

    return run


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="task id, e.g. contracts/supply/agape-odm-supply-review")
    ap.add_argument("--output", required=True, type=Path, help="directory holding the deliverables")
    ap.add_argument("--judge-cmd", required=True)
    ap.add_argument("--save", type=Path, help="write the score JSON here")
    args = ap.parse_args()

    task = load(TASKS_DIR / args.task)
    result = {"task": args.task, "judge": args.judge_cmd, **score_task(task, args.output, make_judge(args.judge_cmd))}
    text = json.dumps(result, indent=2)
    if args.save:
        args.save.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
