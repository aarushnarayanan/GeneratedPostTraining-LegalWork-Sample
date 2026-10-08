"""Re-check the tasks against the upstream CUAD release.

    python scripts/verify_against_cuad.py /path/to/CUADv1.json

Confirms two things the offline validator cannot:
  1. each document is byte-identical to the contract text CUAD published;
  2. each criterion whose basis is "cuad:<category>" cites evidence that
     overlaps a span CUAD's expert annotators labelled with that category
     in that same contract.
CUADv1.json is inside data.zip at https://github.com/TheAtticusProject/cuad
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench_core.tasks import discover, load, load_sources, normalize  # noqa: E402


def main() -> int:
    cuad = {d["title"]: d["paragraphs"][0] for d in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["data"]}
    problems, n_docs, n_label, n_text = [], 0, 0, 0
    for task_id, task_dir in discover():
        records = {}
        for src in load_sources(task_dir)["sources"]:
            rec = cuad.get(src["obtained_from"]["record_title"])
            if rec is None:
                problems.append(f"{task_id}: no CUAD record titled {src['obtained_from']['record_title']!r}")
                continue
            records[src["file"]] = rec
            n_docs += 1
            if (task_dir / "documents" / src["file"]).read_bytes() != rec["context"].encode("utf-8"):
                problems.append(f"{task_id}: {src['file']} differs from the CUAD text")
        for crit in load(task_dir)["criteria"]:
            if not crit["basis"].startswith("cuad:"):
                n_text += 1
                continue
            n_label += 1
            category = crit["basis"][5:]
            hit = False
            for ev in crit["evidence"]:
                rec = records.get(ev["document"])
                if rec is None:
                    continue
                quote = normalize(ev["quote"])
                for qa in rec["qas"]:
                    if re.search(r'"(.+?)"', qa["question"]).group(1) != category:
                        continue
                    for ans in qa["answers"]:
                        span = normalize(ans["text"])
                        if span and (span in quote or quote in span):
                            hit = True
            if not hit:
                problems.append(f"{task_id} {crit['id']}: no '{category}' annotation overlaps the evidence")
    for p in problems:
        print("ERROR", p)
    print(f"{n_docs} documents identical to CUAD; {n_label} criteria tied to expert labels, "
          f"{n_text} tied to document text only; {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
