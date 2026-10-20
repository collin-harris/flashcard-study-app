# Evaluation Results Log

## Shipping criteria

Set on 2026-10-09, after the baseline was rescored under rubric 1.5 and
test set 2, and before any new runs. Reviewed for rubric 1.6 on
2026-10-12. A prompt or model change ships only when a valid run under
rubric 1.6 and test set 2 meets all of these:

- Clean card rate ≥ 95%
- Card count pass rate ≥ 90%
- Supported rate ≥ 98%
- Zero false rejections and zero false acceptances
- Split-scored (see "Split scoring" in
  [`README.md`](README.md#split-scoring)): judge v1 (judge hash
  `d21413e84dec`) scores atomic, supported, no leakage, and duplicates,
  and unambiguous is scored by hand. Every card the judge fails is
  reviewed by hand, along with a seeded random sample of the cards it
  passes, and corrections are applied before scoring.

The last criterion changed on 2026-10-18. It used to say "scored by a
validated judge", and judge v1 wasn't validated: it failed only on
unambiguous catches. The split was adopted after seeing that result. The
other criteria are unchanged.

If the rubric or test set version changes, review these criteria before
applying them to runs under the new versions.

## Runs

One row per valid evaluation run, rubric and test set version, and scorer,
written by `eval/score_run.py`.
Only runs that are not partial, interrupted, or incomplete appear here. The
definition of every metric is in [`rubric.md`](rubric.md), and each run's
full metrics, overall and per category, are in its folder in `runs/`.

- **Scorer:** who scored the judgment-based criteria. `hand` is a person;
  an LLM judge's label names its model and judge prompt version. A run can
  have one row per scorer. `not scored` means only the automated metrics
  were logged.
- **Rates** are shown as a percentage with the count behind it, for example
  `97.3% (181/186)`.
- **Rubric** and **Test set** are the versions the run was scored under.
  Rows scored under different versions are not directly comparable. A run
  recomputed under new versions gets new rows, and its earlier rows are
  kept.

The table is rewritten by the script, so don't edit its rows by hand.
Rerunning the script on a run updates that run's row for the same versions
and scorer.

A `hand:corrected:<judge>` row is a run's hand scores after corrections made
while validating that judge, rescored from its `scores.csv`; each change is
logged in the run folder's `score_changes.csv`. The `hand` row beside it is
the scoring as first made and is kept. Run 2026-10-02_215109 under rubric 1.6
was corrected while validating judge v1 (28 changes: 27 from the
disagreement review on 2026-10-17, 1 from the agreement check on
2026-10-18), then 4 more in a consistency check on 2026-10-20, for 32 in
all. The consistency check scored "significance" questions as failing
unambiguous, since several different answers would be correct, to match
the standard used for prompt v2's unambiguous sheet, which was scored
first. Its original clean card rate is 86.0% (160/186).

A `judge:opus-5.5:v1+hand` row is split-scored (see "Split scoring" in
[`README.md`](README.md#split-scoring)). For run 2026-10-02_215109 under
rubric 1.6, it uses judge run 2026-10-13_214206 (run A) and the corrected
unambiguous scores. Its review decisions come from the corrected hand
scores, which already cover every card. Judge run B gives the same reviewed
clean card rate. Before review, A gives 76.3% (142/186) and B 76.9%
(143/186).

| Run ID | Date | Model | Prompt | Prompt hash | Rubric | Test set | Scorer | Clean card | Atomic | Supported | No leakage | Unambiguous | Duplicate-free | False rejection | False acceptance | Card count pass | Source match | Avg cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.4 | 1 | hand | 89.8% (167/186) | 97.3% (181/186) | 97.8% (182/186) | 98.9% (184/186) | 93.5% (174/186) | 98.4% (183/186) | 0.0% (0/30) | 0.0% (0/5) | 53.3% (16/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.5 | 2 | hand | 86.0% (160/186) | 94.1% (175/186) | 98.9% (184/186) | 96.8% (180/186) | 93.5% (174/186) | 98.4% (183/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | hand | 86.0% (160/186) | 94.1% (175/186) | 98.9% (184/186) | 96.8% (180/186) | 93.5% (174/186) | 97.8% (182/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | hand:corrected:judge-v1 | 79.6% (148/186) | 89.2% (166/186) | 95.2% (177/186) | 96.8% (180/186) | 94.6% (176/186) | 96.8% (180/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | judge:opus-5.5:v1+hand | 80.1% (149/186) | 89.2% (166/186) | 95.2% (177/186) | 97.3% (181/186) | 94.6% (176/186) | 96.8% (180/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.4 | 1 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 53.3% (16/30) | 94.7% (180/190) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.5 | 2 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.7% (180/190) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.7% (180/190) | $0.0032 |
