"""CLI entry point.

    python -m gen_core.generate --task-id contracts/<group>/<slug> \\
        --practice-area contracts --work-type review \\
        --reuse-document tasks/contracts/supply/agape-odm-supply-review/documents/agape-atp-odm-supply-agreement.txt \\
        [--second-judge "python scripts/judge_gpt.py"]

Needs ANTHROPIC_API_KEY. Reuses a document already vetted by an earlier task (its sources.json
entry is copied as-is) rather than fetching a new one — see gen_core/README.md for why.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import llm, scout
from .orchestrator import generate_task
from .tools_judge import make_second_judge

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"
REGISTRY_DIR = ROOT / "registry"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task-id", required=True, help="e.g. contracts/supply/new-task-slug")
    ap.add_argument("--practice-area", required=True)
    ap.add_argument("--work-type", required=True, choices=["analyze", "draft", "review", "research"])
    ap.add_argument("--reuse-document", required=True, action="append", help="path to a document already in tasks/.../documents/; repeatable")
    ap.add_argument("--model", default=llm.DEFAULT_MODEL)
    ap.add_argument("--second-judge", help='command for a second-family judge, e.g. "python scripts/judge_gpt.py"')
    ap.add_argument("--avoid-overlap", default="none", help="free text describing sibling tasks on the same document to not duplicate")
    args = ap.parse_args()

    docs = {Path(p).name: Path(p) for p in args.reuse_document}
    source_provenance = {name: scout.provenance_from_existing_task(path.resolve()) for name, path in docs.items()}

    call = llm.make_caller(model=args.model)
    judges = {args.model: llm.make_caller(model=args.model, system="Reply with JSON only.")}
    if args.second_judge:
        judges[args.second_judge] = make_second_judge(args.second_judge)

    result = generate_task(
        args.task_id,
        tasks_dir=TASKS_DIR,
        registry_dir=REGISTRY_DIR,
        practice_area=args.practice_area,
        work_type=args.work_type,
        source_documents=docs,
        source_provenance=source_provenance,
        call=call,
        judges=judges,
        avoid_overlap=args.avoid_overlap,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    sys.exit(main())
