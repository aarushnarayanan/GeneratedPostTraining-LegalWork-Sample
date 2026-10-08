# Sourcing policy

This benchmark exists to test legal work on documents as they are found in the world. The policy
below is what makes that claim checkable.

## What counts as a source document

A document qualifies if all of these hold:

- A court, legislature, agency or filer published it, and the public can obtain it.
- It can be redistributed: public-domain government text, or a dataset with an open licence.
- A named, versioned place to fetch it again exists.

Examples: contracts filed as SEC exhibits, court opinions and docket filings, statutes, regulations,
agency rules and guidance.

## What may never be done to a document

- No writing new documents, by a person or a model.
- No editing, redacting, summarising, translating, re-typing or cleaning.
- No converting between formats if that changes the text.
- No anonymising. If a document cannot be published as it is, leave it out.

Real documents are messy. Redactions, scanning errors, blank placeholders and overlapping segments stay
in, and `sources.json` describes them in `notes`. A task may tell the agent about them.

## What is authored

| Authored | Rule |
|---|---|
| `instructions` | Describes the assignment. States no facts about the matter beyond what the documents show. |
| `criteria` | Each one quotes the passage it rests on in `evidence`. |
| `tags`, titles, `sources.json` | Metadata only. |

Instructions do not invent a client, a deal or a dispute. They may assign a point of view, such as
"you act for the Customer", because that changes what the reader should flag, not what the documents say.

## Where labels come from

Each criterion states its `basis`:

- `cuad:<category>`: an expert annotator labelled the quoted passage with that clause category in the
  source dataset. `scripts/verify_against_cuad.py` re-checks this against the upstream release.
- `text`: no upstream label exists. The criterion rests on the quoted passage alone and needs review
  by a lawyer before it is relied on.

Other label sources can be added the same way, each with its own prefix and its own verification
script. Candidates are court-written parentheticals and expert-coded case databases.

## Training use and contamination

These documents are public and the CUAD labels are widely used, so a model may have seen both.
Report results with that in mind. A held-out split built from documents filed after a stated cutoff
date is the planned remedy and is not part of this sample.
