# realdocs-legal-bench (working name)

A benchmark for legal AI agents in which **every source document is a real, public legal document**.
Tasks ask an agent to do a piece of legal work on those documents, and a rubric of pass/fail criteria
grades the result.

**Status: sample for review.** Four tasks, six documents, 58 criteria, and a `reference/` gold
completion for each task — see [docs/task-format.md](docs/task-format.md#reference-optional). The
first three were hand-authored; `contracts/ip-licensing/trademark-license-compliance-checklist`
was produced by the generator in [gen_core/](gen_core/README.md) and passed every gate that
doesn't need a model API key. Judged independently by Claude Sonnet 5: 50/50 criteria pass on the
three hand-authored tasks, all scoring 1.0 (`results/`, not committed) — the generated task's
reference has not yet been judged. A second judge, GPT-5.5, is wired up (`scripts/judge_gpt.py`)
but has not actually run — it needs an `OPENAI_API_KEY`. No lawyer has reviewed any rubric yet.

## How it relates to Harvey LAB

The layout and grading follow [Harvey LAB](https://github.com/harveyai/harvey-labs): one directory per
task holding `task.json` and `documents/`, rubric criteria written inline, each criterion scoped to the
deliverables it grades, and all-pass scoring. The difference is the documents.

| | Harvey LAB | This benchmark |
|---|---|---|
| Source documents | Synthetic matter files written for the benchmark | Real public filings, reproduced unchanged |
| Provenance | Not applicable | `sources.json` per task: origin, dataset, commit, SHA-256 |
| Rubric basis | Expert-written criteria | Criteria that each quote the source text; most also trace to an expert annotation |
| Machine checks | Schema | Schema, checksums, and that every quoted passage exists in its document |

## The real-documents rule

1. Nothing in `documents/` is written, edited, summarised, translated or reformatted by a person or a model.
2. Each document is listed in `sources.json` with where it came from, its licence and its SHA-256.
3. Only three things are authored: the task instructions, the rubric criteria and the metadata.
4. Every criterion carries at least one `evidence` quote copied from a named document.
   `python -m bench_core.validate` fails if a quote is not found verbatim.

See [docs/sourcing-policy.md](docs/sourcing-policy.md).

## What is in the sample

| Task | Work type | Documents | Criteria | Tied to expert labels |
|---|---|---|---|---|
| `contracts/supply/agape-odm-supply-review` | review | 1 supply agreement (10-K/A exhibit, 2019) | 17 | 14 |
| `contracts/ip-licensing/ms-trademark-license-analysis` | analyze | 1 trademark license (10-12G/A exhibit, 2019) | 16 | 11 |
| `contracts/distribution/netgear-ingram-consolidated-terms` | analyze | 3 segments of one exhibit: a distributor agreement and two amendments | 17 | 11 |
| `contracts/ip-licensing/trademark-license-compliance-checklist` | draft | 1 trademark license (same document as `ms-trademark-license-analysis`, reused) | 8 | 0 |

All five documents are contracts that companies filed with the SEC, taken from
[CUAD v1](https://github.com/TheAtticusProject/cuad), which publishes their text under CC BY 4.0 together
with its annotators' clause labels. A criterion marked `cuad:<category>`
rests on one of those labels. A criterion marked `text` rests only on the quoted passage.

## Layout

```text
tasks/<practice-area>/<group>/<task>/
    task.json          instructions, deliverables, criteria
    sources.json       provenance for every document
    documents/         the real documents, unchanged
    reference/         optional: a gold completion per deliverable, for training/calibration use
bench_core/
    validate.py        format, checksum and evidence checks
    scoring.py         all-pass rubric scoring
    run_eval.py        grade a run's deliverables with a judge model
    prompts/           the judge prompt
scripts/
    verify_against_cuad.py   re-check documents and labels against the upstream dataset
    judge_gpt.py             second judge for run_eval.py, via the OpenAI API (needs OPENAI_API_KEY)
gen_core/              generates new tasks; see gen_core/README.md
registry/              log of generated tasks, accepted and discarded
tests/                 offline tests
docs/                  task format, evaluation, sourcing policy
```

## Use

```bash
python -m bench_core.validate                 # check every task
pytest -q                                     # offline tests
python -m bench_core.run_eval \
    --task contracts/supply/agape-odm-supply-review \
    --output path/to/deliverables \
    --judge-cmd "your-command-that-reads-a-prompt-on-stdin"
```

The benchmark needs only the Python standard library. The judge is any command that reads a prompt on
standard input and prints the model's reply, so no model provider is built in.

## Not built yet

- An agent harness to evaluate a model against these tasks. LAB ships a sandboxed agent loop and
  model adapters; [gen_core/](gen_core/README.md) generates tasks, it doesn't run one.
- A working second judge. `scripts/judge_gpt.py` is wired up but needs `OPENAI_API_KEY`.
- Coverage planning / dedup across generated tasks, and a blind-solve difficulty check
  (`gen_core`'s G7-G9) — see [gen_core/README.md](gen_core/README.md) for the full gate status.
- Synthetic matter files (Mode B in the architecture doc) — only real documents are used so far.
- Links to the original EDGAR filings. `sources.json` records filer, form and date as CUAD gives them,
  and `edgar_url` is empty.
- Document types beyond contracts: court opinions, dockets, statutes and regulations.

## Licence and attribution

The documents are redistributed under CC BY 4.0 with attribution in [NOTICE.md](NOTICE.md).
A licence for the code, instructions and rubrics has not been chosen yet.
