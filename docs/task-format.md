# Task format

A task is a directory with three parts.

```text
tasks/<practice-area>/<group>/<task>/
    task.json
    sources.json
    documents/
```

## task.json

The core fields are the ones Harvey LAB uses, so a LAB-style harness can read them.
`evidence` and `basis` are additions.

| Field | Meaning |
|---|---|
| `title` | Human-readable title |
| `work_type` | `analyze`, `draft`, `review` or `research` |
| `tags` | Free-form labels for filtering |
| `instructions` | The assignment given to the agent. Names every deliverable in backticks. |
| `deliverables` | Map of expected output filenames |
| `criteria` | The rubric: a list of pass/fail criteria |

Each criterion:

| Field | Meaning |
|---|---|
| `id` | `C-001`, `C-002`, ... unique within the task |
| `title` | Short description |
| `match_criteria` | What the judge checks. Must contain both `PASS if` and `FAIL if`. |
| `deliverables` | Which outputs the judge reads for this criterion |
| `sources` | Which documents the criterion concerns |
| `evidence` | List of `{document, quote}`. Each quote must appear verbatim in that document, ignoring runs of whitespace. |
| `basis` | `cuad:<category>` or `text`. See the sourcing policy. |

Example:

```json
{
  "id": "C-006",
  "title": "States the governing law",
  "match_criteria": "PASS if the memo states that the agreement is governed by the laws of England. FAIL if governing law is omitted or misstated.",
  "deliverables": ["issues-memo.md"],
  "sources": ["agape-atp-odm-supply-agreement.txt"],
  "evidence": [
    {
      "document": "agape-atp-odm-supply-agreement.txt",
      "quote": "This agreement shall be governed by the Laws of England (English common and statutory Law)."
    }
  ],
  "basis": "cuad:Governing Law"
}
```

## sources.json

One entry per file in `documents/`:

| Field | Meaning |
|---|---|
| `file` | Filename in `documents/` |
| `sha256`, `bytes`, `chars` | Fingerprint of the file as distributed |
| `kind` | What the document is |
| `origin` | Who filed or issued it: `filer`, `form`, `filing_date`, `exhibit`, `edgar_url` |
| `obtained_from` | The dataset, record, repository, commit and licence it was copied from |
| `modifications` | Must be `"none"` |

An optional top-level `notes` field describes quirks of the documents.

## reference/ (optional)

A task may hold a `reference/` directory with one file per name in `deliverables` — a gold
completion that satisfies every criterion, meant to be used as training data (the prompt is
`instructions` plus `documents/`, the completion is `reference/`), not as something an evaluated
agent ever sees. It is authored content, scoped by the same sourcing-policy rules as `instructions`
and `criteria`: it states no fact the documents don't support, and it does not guess at redacted
text. `python -m bench_core.run_eval --output <task>/reference --judge-cmd ...` scores it like any
other run's deliverables; `bench_core.validate` does not check it, so passing every criterion
against it still needs an independent judge run (or a lawyer) before it is trusted as ground truth.

## Writing criteria

- One fact or finding per criterion.
- Write what a supervising lawyer would check before the work goes out. Leave out nice-to-haves:
  under all-pass scoring every extra criterion is another way to fail the task.
- State the fact in the criterion. The judge does not see the source documents, only the deliverable.
- Add a `FAIL if` for the likely wrong answer, not only for omission.
