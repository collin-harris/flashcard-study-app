# Pass Sample: 2026-10-13_214206

`review_passes.csv` is a blind check of card+criterion pairs that judge run 2026-10-13_214206
passed, on any card and any of its four criteria (atomic, supported, no leakage, and duplicates). It's
there to catch a judge that does badly on new kinds of cards. It doesn't measure how often the judge
misses, because 20 pairs can't pin down a low miss rate. The judge's grades are left out so the check
is blind.

- **Random seed:** 39116060
- **Drawn:** 2026-10-19
- **Run:** eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
- **Judge run:** 2026-10-13_214206 (judge hash d21413e84dec)
- **Population:** every pair the judge passed, out of 186 cards per criterion: atomic 163, supported 174, no_leakage 180, duplicate 180
- **Sample:** 5 per criterion, drawn in the order atomic, supported, no_leakage, duplicate from one
  `random.Random(39116060)`, each with `rng.sample(sorted(pool), 5)`, then sorted by
  card ID within the criterion. A card can be drawn for more than one criterion.
- **Decisions:** `Y` or `N`; for duplicate, the ID of the earlier card it duplicates, or `none`.
- **Decisions filled from hand scores:** `--decisions-from-hand`, from the corrected
  `scores.csv`, which already covers every card of this run.
