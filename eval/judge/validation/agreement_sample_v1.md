# Agreement Sample v1

`agreement_sample_v1.csv` is a blind recheck of 20 card+criterion pairs
where the hand score and both judge runs agreed. It checks whether the
cases where we all agree are actually correct, since the disagreement
review (`review_v1.csv`) only covered pairs where we didn't. Scores are
left out so the recheck is blind.

- **Random seed:** 20261017
- **Drawn:** 2026-10-17, before any score change from `review_v1.csv` was
  written (no change touches an agreed pair, so this doesn't matter)
- **Hand scores:** `eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2/scores.csv`
- **Judge runs:** 2026-10-13_214206 and 2026-10-13_222522
- **Population:** every pair where `scores.csv`, run A, and run B give the
  same Y or N. Atomic 173, supported 174, no leakage 183, unambiguous 176.
- **Sample:** 5 per criterion, drawn in the order atomic, supported,
  no_leakage, unambiguous from one `random.Random(20261017)`, each with
  `rng.sample(sorted(pool), 5)`, then sorted by card ID within the
  criterion.
