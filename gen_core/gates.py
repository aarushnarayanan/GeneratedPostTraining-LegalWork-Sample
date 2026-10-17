"""Quality gates G1-G6 (roles 8-9 of the architecture). G1-G3 reuse bench_core.validate
unchanged rather than re-implementing schema/checksum/evidence checks. G7-G10 (blind solve,
leakage, dedup, human review) are later build-order steps, not part of this first draft —
each is recorded as "not_run" in gen_meta.json rather than faked.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench_core.scoring import score_task  # noqa: E402
from bench_core.validate import check_task  # noqa: E402

NOT_RUN = "not_run: build-order step not in this first draft (see gen_core README)"


def run_schema_provenance_evidence(task_id: str, task_dir: Path) -> tuple[bool, list[str]]:
    """G1 schema + G2 provenance + G3 evidence, exactly as the benchmark itself checks them."""
    errors = check_task(task_id, task_dir)
    return not errors, errors


def run_label_check(criteria: list[dict]) -> str:
    """G4. Re-checking a cuad:<category> basis needs the upstream CUADv1.json (scripts/
    verify_against_cuad.py); that file isn't fetched by this first draft. Criteria written with
    basis "text" (the Rubric Writer's default) need no label check at all.
    """
    cuad_based = [c for c in criteria if c.get("basis", "").startswith("cuad:")]
    if not cuad_based:
        return "pass: no cuad-basis criteria"
    return "skipped: cuad-basis criteria present but CUADv1.json was not supplied to this run"


def run_audit(audit_fn: Callable[[list[dict]], list[dict]] | None, criteria: list[dict]) -> tuple[bool, list[dict]]:
    """G5. audit_fn is agents.audit_rubric bound to a model call, or None to skip."""
    if audit_fn is None:
        return True, []
    problems = audit_fn(criteria)
    return not problems, problems


def run_reference_judges(task: dict, reference_dir: Path, judges: dict[str, Callable[[str], str]]) -> dict:
    """G6. Grade reference/ with every judge given; all must be all-pass for this gate to pass.
    `judges` maps a label (e.g. "claude-sonnet-5-5", "gpt-5.5") to a Judge callable.
    """
    results = {name: score_task(task, reference_dir, judge) for name, judge in judges.items()}
    passed = all(r["all_pass"] for r in results.values())
    return {"passed": passed, "results": results}
