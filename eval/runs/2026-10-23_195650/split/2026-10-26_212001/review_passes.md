# Pass Sample: 2026-10-26_212001

`review_passes.csv` is a blind check of card+criterion pairs that judge run 2026-10-26_212001
passed, on any card and any of its four criteria (atomic, supported, no leakage, and duplicates). It's
there to catch a judge that does badly on new kinds of cards. It doesn't measure how often the judge
misses, because 20 pairs can't pin down a low miss rate. The judge's grades are left out so the check
is blind.

- **Random seed:** 91824494
- **Drawn:** 2026-10-26
- **Run:** eval/runs/2026-10-23_195650
- **Judge run:** 2026-10-26_212001 (judge hash d21413e84dec)
- **Population:** every pair the judge passed, out of 251 cards per criterion: atomic 245, supported 242, no_leakage 241, duplicate 240
- **Sample:** 5 per criterion, drawn in the order atomic, supported, no_leakage, duplicate from one
  `random.Random(91824494)`, each with `rng.sample(sorted(pool), 5)`, then sorted by
  card ID within the criterion. A card can be drawn for more than one criterion.
- **Decisions:** `Y` or `N`; for duplicate, the ID of the earlier card it duplicates, or `none`.
