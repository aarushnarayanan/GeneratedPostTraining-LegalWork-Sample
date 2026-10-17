"""Runs one seed through the whole pipeline (role: orchestrator, ties roles 1-11 together).

Repair loop: a Rubric Writer attempt that fails G1-G3 is handed the validator errors and asked
to try again, up to `max_repairs` times. A seed that still fails is discarded and logged to
registry/log.jsonl with its last error, rather than written to tasks/.

Coverage Planner dedup and the Solver Panel (build-order steps 4-5 in the architecture doc)
aren't built yet, so a seed here is one task_id chosen by the caller, not drawn from a grid.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Callable

from . import agents, gates, scout

Call = Callable[[str], str]


def _write_task_json(task_dir: Path, header: dict, criteria: list[dict]) -> None:
    task = {
        "title": header["title"],
        "work_type": header["work_type"],
        "tags": header["tags"],
        "instructions": header["instructions"],
        "deliverables": {d: d for d in header["deliverables"]},
        "criteria": criteria,
    }
    (task_dir / "task.json").write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")


def _log(registry_dir: Path, record: dict) -> None:
    registry_dir.mkdir(parents=True, exist_ok=True)
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **record}
    with (registry_dir / "log.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def generate_task(
    task_id: str,
    *,
    tasks_dir: Path,
    registry_dir: Path,
    practice_area: str,
    work_type: str,
    source_documents: dict[str, Path],
    source_provenance: dict[str, dict],
    call: Call | None = None,
    judges: dict[str, Call] | None = None,
    manual_header: dict | None = None,
    manual_criteria: list[dict] | None = None,
    manual_reference: dict[str, str] | None = None,
    avoid_overlap: str = "none",
    max_repairs: int = 3,
    split: str = "train",
) -> dict:
    task_dir = tasks_dir / task_id
    if task_dir.exists():
        raise FileExistsError(f"{task_dir} already exists")
    task_dir.mkdir(parents=True)

    # Role 2: Source Scout. Copy+hash only; never touches document text.
    for name, path in source_documents.items():
        scout.add_source_document(task_dir, path, **source_provenance[name])
    documents = {name: (task_dir / "documents" / name).read_text(encoding="utf-8") for name in source_documents}

    # Role 5: Task Designer.
    header = dict(manual_header) if manual_header else agents.design_task(
        call, practice_area=practice_area, work_type=work_type, documents=documents, avoid_overlap=avoid_overlap,
    )
    header.setdefault("work_type", work_type)

    # Role 6: Rubric Writer, with the G1-G3 repair loop.
    criteria = manual_criteria
    errors: list[str] = []
    for attempt in range(1, max_repairs + 1):
        if criteria is None:
            if call is None:
                raise RuntimeError("no rubric given and no model `call` configured to write one")
            criteria = agents.write_rubric(call, instructions=header["instructions"], deliverables=header["deliverables"], documents=documents)
        _write_task_json(task_dir, header, criteria)
        ok, errors = gates.run_schema_provenance_evidence(task_id, task_dir)
        if ok:
            break
        if call is None:
            break  # manually supplied criteria can't be auto-repaired
        criteria = None  # drop it and let the Rubric Writer try again next loop

    if not ok:
        _log(registry_dir, {"task_id": task_id, "accepted": False, "gate": "G1-G3", "errors": errors})
        shutil.rmtree(task_dir)
        return {"accepted": False, "task_id": task_id, "errors": errors}

    # Role 7: Reference Author, one call per deliverable (or a manually supplied gold completion).
    reference_dir = task_dir / "reference"
    reference_dir.mkdir()
    reference_texts: dict[str, str] = {}
    for deliverable in header["deliverables"]:
        text = (manual_reference or {}).get(deliverable)
        if text is None:
            if call is None:
                raise RuntimeError(f"no reference given for {deliverable} and no model `call` configured")
            text = agents.write_reference(call, deliverable=deliverable, instructions=header["instructions"], documents=documents, criteria=criteria)
        reference_texts[deliverable] = text
        (reference_dir / deliverable).write_text(text, encoding="utf-8")

    # G4: label check.
    g4 = gates.run_label_check(criteria)

    # Role 8 / G5: adversarial audit.
    audit_fn = (lambda c: agents.audit_rubric(call, criteria=c)) if call else None
    g5_passed, g5_problems = gates.run_audit(audit_fn, criteria)

    # Role 9 / G6: judge panel on the reference completion.
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    if judges:
        g6 = gates.run_reference_judges(task, reference_dir, judges)
        g6_status = [("pass" if r["all_pass"] else "fail") for r in g6["results"].values()]
    else:
        g6 = {"passed": None, "results": {}}
        g6_status = ["skipped: no judges configured for this run"]

    gen_meta = {
        "seed": {"practice_area": practice_area, "group": task_id.split("/")[1] if "/" in task_id else "", "work_type": work_type, "mode": "real"},
        "agents": {
            "designer": "manual" if manual_header else "llm",
            "rubric_writer": "manual" if manual_criteria else "llm",
            "reference_author": "manual" if manual_reference else "llm",
        },
        "gates": {
            "schema_provenance_evidence": "pass",
            "label": g4,
            "audit": "pass" if g5_passed else {"fail": g5_problems},
            "reference_judges": g6_status,
            "blind_solve": gates.NOT_RUN,
            "leakage": gates.NOT_RUN,
            "dedup": gates.NOT_RUN,
            "human_review": gates.NOT_RUN,
        },
        "split": split,
        "review_status": "unreviewed",
        "revision_of": None,
    }
    (task_dir / "gen_meta.json").write_text(json.dumps(gen_meta, indent=2) + "\n", encoding="utf-8")

    _log(registry_dir, {"task_id": task_id, "accepted": True, "gates": gen_meta["gates"]})
    return {"accepted": True, "task_id": task_id, "task_dir": str(task_dir), "gen_meta": gen_meta}
