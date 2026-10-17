# gen_core

An agent pipeline that turns a seed (practice area, work type, a document to build on) into a
new task directory under `tasks/`, checked the same way `bench_core.validate` checks every
other task. It implements the content-generation side of the architecture: Task Designer,
Rubric Writer, Reference Author and Rubric Auditor (roles 5-8), plus the deterministic and
LLM gates that check their output (G1-G6).

## Run it

```bash
export ANTHROPIC_API_KEY=...
python -m gen_core.generate \
    --task-id contracts/supply/some-new-task-slug \
    --practice-area contracts --work-type review \
    --reuse-document tasks/contracts/supply/agape-odm-supply-review/documents/agape-atp-odm-supply-agreement.txt \
    --avoid-overlap "the existing agape-odm-supply-review task already covers termination, exclusivity and payment terms" \
    --second-judge "python scripts/judge_gpt.py"   # optional, needs OPENAI_API_KEY too
```

This reuses a document (and its already-vetted `sources.json` entry) from an existing task
rather than fetching a brand-new one from CUAD or EDGAR. The Source Scout (`gen_core/scout.py`)
is written generically — point it at any file with known origin/licence metadata — but wiring
it to a live corpus is left for build-order step 7 below, not needed to prove the pipeline.

A run writes `task.json`, `sources.json`, `documents/`, `reference/` and `gen_meta.json` (an
addition, never shown to an evaluated agent: which agents/model wrote the task, every gate's
result, the split and review status), and appends one line to `registry/log.jsonl`.

## What's built vs. what isn't

| | Status |
|---|---|
| Source Scout (copy + hash, no text access) | Built, generic; not wired to a live corpus fetch |
| Task Designer, Rubric Writer, Reference Author, Rubric Auditor | Built (`gen_core/agents.py`), model-agnostic via an injected `call` |
| G1 schema, G2 provenance, G3 evidence | Reused unchanged from `bench_core.validate` |
| G4 label check | Reused logic from `scripts/verify_against_cuad.py`'s approach: skipped unless a criterion claims a `cuad:` basis, since the Rubric Writer defaults to `"text"` |
| G5 audit, G6 judge panel (one Claude call + optional second-family judge via `--second-judge`) | Built |
| Repair loop (G1-G3 failures sent back to the Rubric Writer, capped at 3 attempts) | Built |
| G7 blind solve, G8 leakage, G9 dedup, G10 human review | Not built — later build-order steps (a sandboxed solver harness, an embedding-dedup index, and a human-in-the-loop step aren't needed to generate and validate a first task) |
| Coverage Planner (grid + dedup), Mode B (synthetic matter files) | Not built — same reason; see the architecture doc's build order |

`gen_meta.json` records each of these as `"not_run"` rather than a faked pass, so nothing
downstream mistakes "not checked yet" for "checked and fine".

## Tests

`tests/test_gen_core.py` runs the agents, the Source Scout and the full repair loop offline,
with a fake `call` standing in for the model — no network, no API key.
