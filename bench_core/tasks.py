"""Task discovery and loading."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"


def discover(tasks_dir: Path = TASKS_DIR) -> list[tuple[str, Path]]:
    """Return (task_id, task_dir) for every directory holding a task.json."""
    found = []
    for task_json in sorted(tasks_dir.rglob("task.json")):
        task_dir = task_json.parent
        found.append((task_dir.relative_to(tasks_dir).as_posix(), task_dir))
    return found


def load(task_dir: Path) -> dict:
    return json.loads((task_dir / "task.json").read_text(encoding="utf-8"))


def load_sources(task_dir: Path) -> dict:
    return json.loads((task_dir / "sources.json").read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    """Collapse all whitespace runs to single spaces. Used only for comparing quotes."""
    return " ".join(text.split())
