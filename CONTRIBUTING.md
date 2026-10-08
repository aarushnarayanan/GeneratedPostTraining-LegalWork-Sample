# Contributing

## Adding a task

1. Pick real public documents that meet [docs/sourcing-policy.md](docs/sourcing-policy.md).
2. Copy them into `tasks/<area>/<group>/<task>/documents/` without changing a byte.
3. Write `sources.json` with origin, where you obtained each file, its licence and its SHA-256.
4. Write `task.json` following [docs/task-format.md](docs/task-format.md). Quote the supporting
   passage for every criterion.
5. Run `python -m bench_core.validate` and `pytest -q`.

## Ground rules

- Do not write, edit or generate source documents.
- Do not include documents you cannot redistribute.
- Mark a criterion `text` unless an existing expert label supports it.
- Say in the pull request whether a lawyer has reviewed the rubric.
