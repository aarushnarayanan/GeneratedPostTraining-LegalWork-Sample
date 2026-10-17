"""Content agents (roles 1, 5-8 of the architecture): Designer, Rubric Writer, Reference
Author, Auditor. Each takes the model call as a parameter (`call: Callable[[str], str]`), the
same injection pattern bench_core.scoring uses for its judge, so tests can pass a fake and a
live run passes gen_core.llm.make_caller().
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

Call = Callable[[str], str]
PROMPTS = Path(__file__).parent / "prompts"


def _extract_json(reply: str):
    match = re.search(r"\{.*\}|\[.*\]", reply, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object/array found in model reply: {reply[:200]!r}")
    return json.loads(match.group(0))


def _render_documents(documents: dict[str, str]) -> str:
    return "\n\n".join(f"--- {name} ---\n{text}" for name, text in documents.items())


def design_task(call: Call, *, practice_area: str, work_type: str, documents: dict[str, str], avoid_overlap: str = "none") -> dict:
    """Role 5: Task Designer. Returns a dict with title, tags, instructions, deliverables."""
    prompt = (PROMPTS / "designer.txt").read_text(encoding="utf-8").format(
        practice_area=practice_area,
        work_type=work_type,
        documents=_render_documents(documents),
        avoid_overlap=avoid_overlap,
    )
    header = _extract_json(call(prompt))
    for field in ("title", "tags", "instructions", "deliverables"):
        if field not in header:
            raise ValueError(f"Task Designer reply missing '{field}'")
    return header


def write_rubric(call: Call, *, instructions: str, deliverables: list[str], documents: dict[str, str]) -> list[dict]:
    """Role 6: Rubric Writer. Returns a list of criterion dicts."""
    prompt = (PROMPTS / "rubric_writer.txt").read_text(encoding="utf-8").format(
        instructions=instructions,
        deliverables=", ".join(deliverables),
        documents=_render_documents(documents),
    )
    criteria = _extract_json(call(prompt))
    if not isinstance(criteria, list):
        raise ValueError("Rubric Writer must return a JSON array of criteria")
    return criteria


def write_reference(call: Call, *, deliverable: str, instructions: str, documents: dict[str, str], criteria: list[dict]) -> str:
    """Role 7: Reference Author. Returns the Markdown text of one deliverable."""
    prompt = (PROMPTS / "reference_author.txt").read_text(encoding="utf-8").format(
        deliverable=deliverable,
        instructions=instructions,
        documents=_render_documents(documents),
        criteria=json.dumps([{"title": c["title"], "match_criteria": c["match_criteria"]} for c in criteria], indent=2),
    )
    return call(prompt).strip()


def audit_rubric(call: Call, *, criteria: list[dict]) -> list[dict]:
    """Role 8: Rubric Auditor. Returns [] if the rubric has no writing-rule violations."""
    prompt = (PROMPTS / "auditor.txt").read_text(encoding="utf-8").format(
        criteria=json.dumps([{k: c[k] for k in ("id", "title", "match_criteria")} for c in criteria], indent=2),
    )
    problems = _extract_json(call(prompt))
    if not isinstance(problems, list):
        raise ValueError("Rubric Auditor must return a JSON array")
    return problems
