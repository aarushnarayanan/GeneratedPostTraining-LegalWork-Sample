"""Source Scout (role 2): copies a document into a task's documents/ and records its
provenance in sources.json. It only ever opens files in binary mode to hash and copy them —
it has no function that returns document text, so the real-documents rule (no editing,
no re-typing) is enforced by what this module can do, not by an instruction to an agent.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


def add_source_document(
    task_dir: Path,
    src_file: Path,
    *,
    origin: dict,
    obtained_from: dict,
    kind: str,
) -> dict:
    """Copy src_file into task_dir/documents/ unchanged and append its sources.json entry."""
    doc_dir = task_dir / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)
    dest = doc_dir / src_file.name
    shutil.copyfile(src_file, dest)  # byte copy, never opened in text mode

    raw = dest.read_bytes()
    entry = {
        "file": dest.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "chars": len(raw.decode("utf-8")),
        "kind": kind,
        "origin": origin,
        "obtained_from": obtained_from,
        "modifications": "none",
    }

    sources_path = task_dir / "sources.json"
    data = json.loads(sources_path.read_text(encoding="utf-8")) if sources_path.is_file() else {"sources": []}
    data["sources"] = [s for s in data["sources"] if s["file"] != entry["file"]] + [entry]
    sources_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return entry


def provenance_from_existing_task(existing_doc_path: Path) -> dict:
    """Look up the origin/obtained_from/kind of a document already vetted by another task,
    to pass into add_source_document when reusing it.

    ponytail: this is the first-draft fetch path — real new-corpus fetching (EDGAR/CUAD
    downloads) is build-order step 7 in the architecture doc, not needed to prove the pipeline.
    """
    existing_task_dir = existing_doc_path.parent.parent
    sources = json.loads((existing_task_dir / "sources.json").read_text(encoding="utf-8"))["sources"]
    src = next(s for s in sources if s["file"] == existing_doc_path.name)
    return {"origin": src["origin"], "obtained_from": src["obtained_from"], "kind": src["kind"]}
