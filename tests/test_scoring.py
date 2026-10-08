"""All-pass scoring behaves as documented."""
import json

from bench_core.scoring import parse_verdict, score_task

TASK = {
    "instructions": "Write `memo.md`.",
    "deliverables": {"memo.md": "memo.md"},
    "criteria": [
        {"id": "C-001", "title": "a", "match_criteria": "PASS if x. FAIL if not.", "deliverables": ["memo.md"]},
        {"id": "C-002", "title": "b", "match_criteria": "PASS if y. FAIL if not.", "deliverables": ["memo.md"]},
    ],
}
reply = lambda v: json.dumps({"reasoning": "r", "verdict": v})


def test_all_pass(tmp_path):
    (tmp_path / "memo.md").write_text("text")
    out = score_task(TASK, tmp_path, lambda p: reply("pass"))
    assert out["score"] == 1.0 and out["all_pass"] and out["n_passed"] == 2


def test_one_failure_scores_zero(tmp_path):
    (tmp_path / "memo.md").write_text("text")
    out = score_task(TASK, tmp_path, lambda p: reply("fail" if "REQUIREMENT: b" in p else "pass"))
    assert out["score"] == 0.0 and out["n_passed"] == 1


def test_missing_deliverable_fails_without_calling_judge(tmp_path):
    def judge(prompt):
        raise AssertionError("judge should not be called")
    out = score_task(TASK, tmp_path, judge)
    assert out["score"] == 0.0 and out["n_passed"] == 0


def test_unparseable_reply_is_a_fail():
    assert parse_verdict("looks good to me")[0] == "fail"
    assert parse_verdict('```json\n{"reasoning": "ok", "verdict": "PASS"}\n```')[0] == "pass"
