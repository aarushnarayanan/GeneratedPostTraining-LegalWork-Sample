"""All-pass rubric scoring.

A task scores 1.0 only if every criterion passes. The criterion pass rate is
kept as a diagnostic. Each criterion is judged against only the deliverables
it names.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

PROMPT = (Path(__file__).parent / "prompts" / "rubric_criterion.txt").read_text(encoding="utf-8")
Judge = Callable[[str], str]  # prompt in, raw model reply out


def build_prompt(task: dict, criterion: dict, outputs: dict[str, str]) -> str:
    parts = []
    for name in criterion["deliverables"]:
        body = outputs.get(name)
        parts.append(f"--- {name} ---\n{body if body is not None else '[deliverable not produced]'}")
    return PROMPT.format(
        instructions=task["instructions"],
        output="\n\n".join(parts),
        title=criterion["title"],
        match_criteria=criterion["match_criteria"],
    )


def parse_verdict(reply: str) -> tuple[str, str]:
    """Return (verdict, reasoning). Anything unparseable is a fail."""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            verdict = str(data.get("verdict", "")).strip().lower()
            if verdict in ("pass", "fail"):
                return verdict, str(data.get("reasoning", ""))
        except json.JSONDecodeError:
            pass
    return "fail", "judge reply could not be parsed"


def score_task(task: dict, output_dir: Path, judge: Judge) -> dict:
    outputs = {}
    for name in task["deliverables"]:
        path = output_dir / name
        if path.is_file():
            outputs[name] = path.read_text(encoding="utf-8", errors="replace")
    results = []
    for criterion in task["criteria"]:
        missing = [d for d in criterion["deliverables"] if d not in outputs]
        if missing:
            verdict, reasoning = "fail", f"deliverable not produced: {', '.join(missing)}"
        else:
            verdict, reasoning = parse_verdict(judge(build_prompt(task, criterion, outputs)))
        results.append({"id": criterion["id"], "title": criterion["title"], "verdict": verdict, "reasoning": reasoning})
    n_passed = sum(r["verdict"] == "pass" for r in results)
    n = len(results)
    return {
        "score": 1.0 if n and n_passed == n else 0.0,
        "all_pass": bool(n) and n_passed == n,
        "n_criteria": n,
        "n_passed": n_passed,
        "criteria": results,
    }
