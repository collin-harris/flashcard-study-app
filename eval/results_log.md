# Evaluation Results Log

One row per valid evaluation run and scorer, written by `eval/score_run.py`.
Only runs that are not partial, interrupted, or incomplete appear here. The
definition of every metric is in [`rubric.md`](rubric.md), and each run's
full metrics, overall and per category, are in its folder in `runs/`.

- **Scorer:** who scored the judgment-based criteria. `hand` is a person;
  an LLM judge's label names its model and judge prompt version. A run can
  have one row per scorer. `not scored` means only the automated metrics
  were logged.
- **Rates** are shown as a percentage with the count behind it, for example
  `97.3% (181/186)`.
- **Rubric** is the rubric version the run was scored under. Rows scored
  under different rubric versions are not directly comparable.

The table is rewritten by the script, so don't edit its rows by hand.
Rerunning the script on a run updates that run's row for the same scorer.

| Run ID | Date | Model | Prompt | Prompt hash | Rubric | Scorer | Clean card | Atomic | Supported | No leakage | Unambiguous | Duplicate-free | False rejection | False acceptance | Card count pass | Source match | Avg cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.4 | hand | 89.8% (167/186) | 97.3% (181/186) | 97.8% (182/186) | 98.9% (184/186) | 93.5% (174/186) | 98.4% (183/186) | 0.0% (0/30) | 0.0% (0/5) | 53.3% (16/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.4 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 53.3% (16/30) | 94.7% (180/190) | $0.0032 |
