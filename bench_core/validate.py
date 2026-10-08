"""Check every task against the benchmark's rules.

Run:  python -m bench_core.validate

Rules enforced:
  1. task.json has the required fields and well-formed criteria.
  2. Every file in documents/ is declared in sources.json with a matching SHA-256,
     a named public origin, and modifications == "none".
  3. Every criterion cites at least one evidence quote, and every quote appears
     verbatim (ignoring whitespace runs) in the document it names.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from .tasks import discover, load, load_sources, normalize

WORK_TYPES = {"analyze", "draft", "review", "research"}
TASK_FIELDS = ("title", "work_type", "tags", "instructions", "deliverables", "criteria")
CRITERION_FIELDS = ("id", "title", "match_criteria", "deliverables", "sources", "evidence", "basis")


def check_task(task_id: str, task_dir: Path) -> list[str]:
    errors: list[str] = []
    err = lambda msg: errors.append(f"{task_id}: {msg}")

    try:
        task = load(task_dir)
    except Exception as exc:  # noqa: BLE001
        return [f"{task_id}: task.json unreadable: {exc}"]

    for field in TASK_FIELDS:
        if field not in task:
            err(f"task.json missing '{field}'")
    if errors:
        return errors
    if task["work_type"] not in WORK_TYPES:
        err(f"work_type '{task['work_type']}' not in {sorted(WORK_TYPES)}")
    for name in task["deliverables"]:
        if f"`{name}`" not in task["instructions"]:
            err(f"instructions do not name deliverable `{name}`")

    # --- documents and provenance
    doc_dir = task_dir / "documents"
    on_disk = {p.name: p for p in doc_dir.iterdir() if p.is_file()} if doc_dir.is_dir() else {}
    if not on_disk:
        err("documents/ is missing or empty")
    try:
        declared = {s["file"]: s for s in load_sources(task_dir)["sources"]}
    except Exception as exc:  # noqa: BLE001
        err(f"sources.json unreadable: {exc}")
        declared = {}
    for name in sorted(set(on_disk) - set(declared)):
        err(f"document '{name}' has no entry in sources.json")
    for name in sorted(set(declared) - set(on_disk)):
        err(f"sources.json lists '{name}' but the file is not in documents/")
    for name in sorted(set(on_disk) & set(declared)):
        src = declared[name]
        digest = hashlib.sha256(on_disk[name].read_bytes()).hexdigest()
        if digest != src.get("sha256"):
            err(f"'{name}' SHA-256 does not match sources.json")
        if src.get("modifications") != "none":
            err(f"'{name}' must be unmodified (modifications == \"none\")")
        got = src.get("obtained_from") or {}
        if not (got.get("repository") and got.get("license")):
            err(f"'{name}' needs obtained_from.repository and obtained_from.license")
        if not (src.get("origin") or {}).get("filer"):
            err(f"'{name}' needs origin.filer")

    texts = {name: normalize(path.read_text(encoding="utf-8")) for name, path in on_disk.items()}

    # --- criteria
    seen: set[str] = set()
    if not task["criteria"]:
        err("no criteria")
    for i, crit in enumerate(task["criteria"]):
        cid = crit.get("id", f"#{i}")
        for field in CRITERION_FIELDS:
            if field not in crit:
                err(f"{cid} missing '{field}'")
        if cid in seen:
            err(f"duplicate criterion id {cid}")
        seen.add(cid)
        mc = crit.get("match_criteria", "")
        if "PASS if" not in mc or "FAIL if" not in mc:
            err(f"{cid} match_criteria must state both 'PASS if' and 'FAIL if'")
        for d in crit.get("deliverables", []):
            if d not in task["deliverables"]:
                err(f"{cid} references unknown deliverable '{d}'")
        if not crit.get("deliverables"):
            err(f"{cid} names no deliverable")
        for s in crit.get("sources", []):
            if s not in on_disk:
                err(f"{cid} references unknown source document '{s}'")
        basis = crit.get("basis", "")
        if basis != "text" and not basis.startswith("cuad:"):
            err(f"{cid} basis must be 'text' or 'cuad:<category>'")
        if not crit.get("evidence"):
            err(f"{cid} has no evidence quote")
        for ev in crit.get("evidence", []):
            doc, quote = ev.get("document"), normalize(ev.get("quote", ""))
            if doc not in texts:
                err(f"{cid} evidence names unknown document '{doc}'")
            elif len(quote) < 15:
                err(f"{cid} evidence quote is too short to be meaningful")
            elif quote not in texts[doc]:
                err(f"{cid} evidence quote not found in '{doc}': {quote[:70]!r}")
            elif doc not in crit.get("sources", []):
                err(f"{cid} evidence document '{doc}' is not listed in its sources")
    return errors


def main() -> int:
    tasks = discover()
    all_errors: list[str] = []
    n_criteria = n_docs = 0
    for task_id, task_dir in tasks:
        all_errors += check_task(task_id, task_dir)
        try:
            n_criteria += len(load(task_dir)["criteria"])
            n_docs += len(load_sources(task_dir)["sources"])
        except Exception:  # noqa: BLE001
            pass
    for line in all_errors:
        print("ERROR", line)
    print(f"{len(tasks)} tasks, {n_docs} documents, {n_criteria} criteria, {len(all_errors)} errors")
    return 1 if all_errors or not tasks else 0


if __name__ == "__main__":
    sys.exit(main())
