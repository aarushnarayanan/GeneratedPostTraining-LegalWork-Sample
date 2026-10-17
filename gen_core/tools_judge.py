"""Wraps bench_core.run_eval's subprocess judge so gen_core can use a second-family judge
(e.g. scripts/judge_gpt.py) in G6 the same way bench_core.run_eval does for scoring a run.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench_core.run_eval import make_judge  # noqa: E402


def make_second_judge(judge_cmd: str) -> Callable[[str], str]:
    return make_judge(judge_cmd)
