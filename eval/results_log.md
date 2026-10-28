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
2026-10-18), then 5 more in consistency checks, for 33 in all. The check
on 2026-10-20 (4 changes) scored "significance" questions as failing
unambiguous, since several different answers would be correct, to match
the standard used for prompt v2's unambiguous sheet, which was scored
first. The check on 2026-10-21 (1 change) removed sample_007-c03's
duplicate mark, added in the disagreement review: the fact it tests, what
the term depolarization means, isn't in sample_007-c02's answer, which
matches the decision on the same pair in prompt v2's review. Its original
clean card rate is 86.0% (160/186).

A `judge:opus-5.5:v1+hand` row is split-scored (see "Split scoring" in
[`README.md`](README.md#split-scoring)). For run 2026-10-02_215109 under
rubric 1.6, it uses judge run 2026-10-13_214206 (run A) and the corrected
unambiguous scores. Its review decisions come from the corrected hand
scores, which already cover every card. Judge run B gives the same reviewed
clean card rate. Before review, A gives 76.3% (142/186) and B 76.9%
(143/186).

**Scoring standards of 2026-10-27.** Three standards were set while
reviewing the Sonnet 5.5 run and applied to every run as logged consistency
checks (provenance `consistency check`, prompted by `Sonnet review
standards`):

- **Supported:** a claim about code passes only if the notes state it, in
  prose or in a code comment. It fails if it has to be worked out by
  reading or running the code.
- **No leakage:** a card fails if a code snippet, formula or name in the
  question spells out the answer.
- **Atomic:** a card fails if it splits naturally into separate questions.
  A closed set passes only when the notes say the same thing about each
  item and the list is complete.

They lowered every run's clean card rate: Run 1 from 80.1% to 78.5% (3
cards), v2 Haiku from 78.1% to 75.1% (6 cards), and v2 Sonnet 5.5 from
90.8% to 87.6% (8 cards). Run 1 got 4 changes, logged in both its hand
scores and its split log; v2 Haiku got 10 and Sonnet 5.5 got 9. The rows
they replaced are kept under "Superseded rows" below the table.

Run 2026-10-23_195650 (Sonnet 5.5) cost $0.3725 to generate ($0.0106 per
sample, the Avg cost column), after a $0.0194 two-sample smoke test, and
$0.7384 to judge.

**Decision (2026-10-27):** ship Sonnet 5.5 (`claude-sonnet-5-5`, thinking
`between_tools`, effort `high`) with prompt v2.

Decision rule, agreed 2026-10-23 during planning, after the v2 Haiku result
and before the Sonnet 5.5 run; not recorded in the repo at the time: ship
the setup with the highest split-scored clean card rate; if the leader is
within about 2 points, choose on cost and speed and call them comparable;
allow at most one prompt v3 run, only if results point to a clear fix. This
departs from the shipping criteria above, which no run met; those criteria
remain the target for production. Sonnet 5.5 leads under both the original
and the 2026-10-27 standards (90.8% and 87.6%, against 80.1%/78.1% and
78.5%/75.1%).

Sonnet 5.5 is at 87.6% clean card (needs 95%), 66.7% card count pass (needs
90%) and 94.8% supported (needs 98%). The mitigation is the review step
being built into the app: the user will review and edit every card before
it's saved.

**Limitations:**

- The model and the prompt changed together, so the gain can't be credited
  to the prompt. On Haiku 4.5, prompt v2 alone lowered the clean card rate,
  from 78.5% to 75.1%.
- Prompt v2 asks for cards about what code does and returns, which the
  supported standard fails unless the notes state it.
- Sonnet 5.5 is below both Haiku runs on duplicate-free (95.6%, 11
  duplicates, against 97.3% and 99.0%), and 7 of the 11 are reversed pairs.
  It's also below both on no leakage (95.2%), and its lowest rate is
  supported (94.8%).
- The card count ranges were set after the Haiku 4.5 baseline and may favor
  its output; all 10 of Sonnet 5.5's card count misses are over range.

**Next experiment (not run):** prompt v3, limiting code cards to what the
notes state and tightening the reversed-pair rule.

**Judge:** judge v1 is still not validated. Under the final standards it
fails three catch checks against Run 1's corrected hand scores: unambiguous
(3/10 and 4/10, needs 8), atomic (run B 19/22, needs 20) and no leakage (run
A 5/7, needs 6).

| Run ID | Date | Model | Prompt | Prompt hash | Rubric | Test set | Scorer | Clean card | Atomic | Supported | No leakage | Unambiguous | Duplicate-free | False rejection | False acceptance | Card count pass | Source match | Avg cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.4 | 1 | hand | 89.8% (167/186) | 97.3% (181/186) | 97.8% (182/186) | 98.9% (184/186) | 93.5% (174/186) | 98.4% (183/186) | 0.0% (0/30) | 0.0% (0/5) | 53.3% (16/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.5 | 2 | hand | 86.0% (160/186) | 94.1% (175/186) | 98.9% (184/186) | 96.8% (180/186) | 93.5% (174/186) | 98.4% (183/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | hand | 86.0% (160/186) | 94.1% (175/186) | 98.9% (184/186) | 96.8% (180/186) | 93.5% (174/186) | 97.8% (182/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | hand:corrected:judge-v1 | 78.0% (145/186) | 88.2% (164/186) | 94.6% (176/186) | 96.2% (179/186) | 94.6% (176/186) | 97.3% (181/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | judge:opus-5.5:v1+hand | 78.5% (146/186) | 88.2% (164/186) | 94.6% (176/186) | 96.8% (180/186) | 94.6% (176/186) | 97.3% (181/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.4 | 1 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 53.3% (16/30) | 94.7% (180/190) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.5 | 2 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.7% (180/190) | $0.0032 |
| 2026-10-02_215610 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | not scored | not scored | not scored | not scored | not scored | not scored | not scored | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.7% (180/190) | $0.0032 |
| 2026-10-19_190307 | 2026-10-19 | claude-haiku-4-5-20251001 | v2 | a24b2d79f726 | 1.6 | 2 | judge:opus-5.5:v1+hand | 75.1% (151/201) | 91.0% (183/201) | 89.6% (180/201) | 97.5% (196/201) | 91.5% (184/201) | 99.0% (199/201) | 0.0% (0/30) | 0.0% (0/5) | 70.0% (21/30) | 99.5% (200/201) | $0.0037 |
| 2026-10-23_195650 | 2026-10-23 | claude-sonnet-5-5 | v2 | a24b2d79f726 | 1.6 | 2 | judge:opus-5.5:v1+hand | 87.6% (220/251) | 98.4% (247/251) | 94.8% (238/251) | 95.2% (239/251) | 97.2% (244/251) | 95.6% (240/251) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 100.0% (251/251) | $0.0106 |

## Superseded rows

Rows replaced by the 2026-10-27 standards, kept as they were. `score_run.py`
only rewrites the table above, so this one is never changed.

| Run ID | Date | Model | Prompt | Prompt hash | Rubric | Test set | Scorer | Clean card | Atomic | Supported | No leakage | Unambiguous | Duplicate-free | False rejection | False acceptance | Card count pass | Source match | Avg cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | hand:corrected:judge-v1 | 79.6% (148/186) | 89.2% (166/186) | 95.2% (177/186) | 96.8% (180/186) | 94.6% (176/186) | 97.3% (181/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-02_215109 | 2026-10-02 | claude-haiku-4-5-20251001 | v1 | f5e88f4d8fd8 | 1.6 | 2 | judge:opus-5.5:v1+hand | 80.1% (149/186) | 89.2% (166/186) | 95.2% (177/186) | 97.3% (181/186) | 94.6% (176/186) | 97.3% (181/186) | 0.0% (0/30) | 0.0% (0/5) | 66.7% (20/30) | 94.6% (176/186) | $0.0032 |
| 2026-10-19_190307 | 2026-10-19 | claude-haiku-4-5-20251001 | v2 | a24b2d79f726 | 1.6 | 2 | judge:opus-5.5:v1+hand | 78.1% (157/201) | 92.5% (186/201) | 92.0% (185/201) | 98.5% (198/201) | 91.5% (184/201) | 99.0% (199/201) | 0.0% (0/30) | 0.0% (0/5) | 70.0% (21/30) | 99.5% (200/201) | $0.0037 |
