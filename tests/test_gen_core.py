"""Offline tests for gen_core: no network, no API key. Every LLM agent is called through a
fake `call` so these exercise the real repair loop, gates and file-writing logic.
"""
from __future__ import annotations

import json

from gen_core import agents, scout
from gen_core.orchestrator import generate_task

DOC_TEXT = "This agreement is governed by the Laws of Testland. The term is five (5) years."

GOOD_HEADER = {
    "title": "Test Task",
    "work_type": "review",
    "tags": ["test"],
    "instructions": "Review the agreement and write `memo.md`.",
    "deliverables": ["memo.md"],
}
GOOD_CRITERIA = [
    {
        "id": "C-001",
        "title": "States governing law",
        "match_criteria": "PASS if the memo states Testland law governs. FAIL if omitted or misstated.",
        "deliverables": ["memo.md"],
        "sources": ["doc.txt"],
        "evidence": [{"document": "doc.txt", "quote": "This agreement is governed by the Laws of Testland."}],
        "basis": "text",
    }
]
BAD_CRITERIA = [dict(GOOD_CRITERIA[0], evidence=[{"document": "doc.txt", "quote": "this quote is not in the document anywhere"}])]


def _provenance():
    return {
        "doc.txt": {
            "origin": {"filer": "TEST FILER"},
            "obtained_from": {"repository": "https://example.test/corpus", "license": "CC BY 4.0"},
            "kind": "test contract",
        }
    }


def test_scout_copies_and_hashes(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text(DOC_TEXT, encoding="utf-8")
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    entry = scout.add_source_document(task_dir, src, **_provenance()["doc.txt"])
    assert (task_dir / "documents" / "doc.txt").read_text(encoding="utf-8") == DOC_TEXT
    assert entry["modifications"] == "none"
    assert json.loads((task_dir / "sources.json").read_text())["sources"][0]["file"] == "doc.txt"


def test_agents_parse_json_from_a_noisy_reply():
    fake_call = lambda prompt: f"Sure, here it is:\n{json.dumps(GOOD_CRITERIA)}\nHope that helps."
    criteria = agents.write_rubric(fake_call, instructions="x", deliverables=["memo.md"], documents={"doc.txt": DOC_TEXT})
    assert criteria == GOOD_CRITERIA


def test_generate_task_manual_mode_is_accepted(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text(DOC_TEXT, encoding="utf-8")
    result = generate_task(
        "area/group/manual-task",
        tasks_dir=tmp_path / "tasks",
        registry_dir=tmp_path / "registry",
        practice_area="contracts",
        work_type="review",
        source_documents={"doc.txt": src},
        source_provenance=_provenance(),
        manual_header=GOOD_HEADER,
        manual_criteria=GOOD_CRITERIA,
        manual_reference={"memo.md": "This agreement is governed by the Laws of Testland."},
    )
    assert result["accepted"] is True
    gen_meta = json.loads((tmp_path / "tasks" / "area/group/manual-task" / "gen_meta.json").read_text())
    assert gen_meta["gates"]["schema_provenance_evidence"] == "pass"


def test_repair_loop_recovers_from_a_bad_quote(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text(DOC_TEXT, encoding="utf-8")
    attempts = {"n": 0}

    def fake_call(prompt: str) -> str:
        attempts["n"] += 1
        if "criteria" in prompt.lower() or attempts["n"] == 1:
            return json.dumps(BAD_CRITERIA if attempts["n"] == 1 else GOOD_CRITERIA)
        return "memo content"

    result = generate_task(
        "area/group/repaired-task",
        tasks_dir=tmp_path / "tasks",
        registry_dir=tmp_path / "registry",
        practice_area="contracts",
        work_type="review",
        source_documents={"doc.txt": src},
        source_provenance=_provenance(),
        manual_header=GOOD_HEADER,
        call=fake_call,
        manual_reference={"memo.md": "ok"},
    )
    assert result["accepted"] is True
    assert attempts["n"] >= 2


def test_task_discarded_after_max_repairs_logs_failure(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text(DOC_TEXT, encoding="utf-8")
    result = generate_task(
        "area/group/doomed-task",
        tasks_dir=tmp_path / "tasks",
        registry_dir=tmp_path / "registry",
        practice_area="contracts",
        work_type="review",
        source_documents={"doc.txt": src},
        source_provenance=_provenance(),
        manual_header=GOOD_HEADER,
        manual_criteria=BAD_CRITERIA,
        manual_reference={"memo.md": "ok"},
    )
    assert result["accepted"] is False
    assert not (tmp_path / "tasks" / "area/group/doomed-task").exists()
    log = (tmp_path / "registry" / "log.jsonl").read_text()
    assert "doomed-task" in log and '"accepted": false' in log
