# Evaluation

Grading follows the method Harvey LAB uses.

1. The agent writes its deliverables to an output directory, using the filenames in `deliverables`.
2. For each criterion, a judge model reads only the deliverables that criterion names, plus the task
   instructions and the criterion's `match_criteria`.
3. The judge returns `pass` or `fail` with a short reason. A reply that cannot be parsed is a fail.
   A missing deliverable fails its criteria without calling the judge.
4. **All-pass scoring:** the task scores 1.0 if every criterion passed and 0.0 otherwise.
5. The criterion pass rate (`n_passed / n_criteria`) is reported beside it as a diagnostic.

The judge does not see the source documents or the `evidence` quotes. Evidence is for the people who
write and audit rubrics, and for the validator.

## Known limits

- One judge. Use two judge models from different families and report both before publishing numbers.
- The judge has not been calibrated against lawyers on these tasks.
- Deliverables are Markdown. LAB also grades `.docx` and `.xlsx` outputs.
