# Pass Sample: 2026-10-20_180350

`review_passes.csv` is a blind check of card+criterion pairs that judge run 2026-10-20_180350
passed, on any card and any of its four criteria (atomic, supported, no leakage, and duplicates). It's
there to catch a judge that does badly on new kinds of cards. It doesn't measure how often the judge
misses, because 20 pairs can't pin down a low miss rate. The judge's grades are left out so the check
is blind.

- **Random seed:** 69616259
- **Drawn:** 2026-10-20
- **Run:** eval/runs/2026-10-19_190307
- **Judge run:** 2026-10-20_180350 (judge hash d21413e84dec)
- **Population:** every pair the judge passed, out of 201 cards per criterion: atomic 182, supported 182, no_leakage 198, duplicate 196
- **Sample:** 5 per criterion, drawn in the order atomic, supported, no_leakage, duplicate from one
  `random.Random(69616259)`, each with `rng.sample(sorted(pool), 5)`, then sorted by
  card ID within the criterion. A card can be drawn for more than one criterion.
- **Decisions:** `Y` or `N`; for duplicate, the ID of the earlier card it duplicates, or `none`.
