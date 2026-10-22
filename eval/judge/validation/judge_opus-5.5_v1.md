# Judge Validation: judge:opus-5.5:v1

**Verdict (corrected hand scores): NOT VALIDATED**

- **Judge:** claude-opus-5-5, prompt v1, effort low, judge hash d21413e84dec
- **Ground truth:** eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2/scores.csv, run 2026-10-02_215109 under rubric 1.6 and test set 2
- **Judge runs:** A = 2026-10-13_214206, B = 2026-10-13_222522
- **Seeded runs:** A = 2026-10-13_223040, B = 2026-10-13_223531
- **Judge cost:** $0.5550, $0.5751, $0.5380, $0.5407 (runs A, B, seeded A, seeded B)
- **Total spent, including discarded runs:** $2.7309
- **Retries:** 1; drop rate 1.4% (2/143) of API calls, including discarded runs (see [Retries](#retries))
- **Score changes:** 1 pre-judge, 27 from the judge review, 1 from the agreement check, 5 from the consistency check (see [Score changes](#score-changes))
- **Agreement check:** 19 of 20 matched, 1 shared error (see [Agreement check](#agreement-check))

Every threshold must hold in both runs. Catch thresholds allow a fixed number of misses (unambiguous 2, atomic 2, no leakage 1), so they still apply if a hand score is corrected.

## Checks against the corrected hand scores

| Check | Threshold | Run A | Run B | Result |
|---|---|---|---|---|
| Unambiguous: catches | ≥ 8 of 10 | **30.0% (3/10)** | **40.0% (4/10)** | **FAIL** |
| Atomic: catches | ≥ 18 of 20 | 100.0% (20/20) | 95.0% (19/20) | pass |
| No leakage: catches | ≥ 5 of 6 | 83.3% (5/6) | 83.3% (5/6) | pass |
| Atomic: false alarm rate | ≤ 5% | 1.8% (3/166) | 0.6% (1/166) | pass |
| Supported: false alarm rate | ≤ 5% | 1.7% (3/177) | 2.3% (4/177) | pass |
| No leakage: false alarm rate | ≤ 5% | 0.6% (1/180) | 1.1% (2/180) | pass |
| Unambiguous: false alarm rate | ≤ 5% | 0.0% (0/176) | 0.0% (0/176) | pass |
| Duplicates: false alarm rate | ≤ 5% | 0.6% (1/181) | 1.1% (2/181) | pass |
| Clean card rate | within ±3 points of 79.6% (148/186) | 79.0% (147/186) | 79.6% (148/186) | pass |
| Seeded supported: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded atomic: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded no leakage: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded unambiguous: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded duplicates: correct | ≥ 5 of 6 | 6 of 6 | 6 of 6 | pass |

## Checks against the original hand scores

| Check | Threshold | Run A | Run B | Result |
|---|---|---|---|---|
| Unambiguous: catches | ≥ 10 of 12 | **25.0% (3/12)** | **25.0% (3/12)** | **FAIL** |
| Atomic: catches | ≥ 9 of 11 | 100.0% (11/11) | 100.0% (11/11) | pass |
| No leakage: catches | ≥ 5 of 6 | 83.3% (5/6) | 83.3% (5/6) | pass |
| Atomic: false alarm rate | ≤ 5% | **6.9% (12/175)** | **5.1% (9/175)** | **FAIL** |
| Supported: false alarm rate | ≤ 5% | **5.4% (10/184)** | **5.4% (10/184)** | **FAIL** |
| No leakage: false alarm rate | ≤ 5% | 0.6% (1/180) | 1.1% (2/180) | pass |
| Unambiguous: false alarm rate | ≤ 5% | 0.0% (0/174) | 0.6% (1/174) | pass |
| Duplicates: false alarm rate | ≤ 5% | 1.1% (2/182) | 1.6% (3/182) | pass |
| Clean card rate | within ±3 points of 86.0% (160/186) | **79.0% (147/186)** | **79.6% (148/186)** | **FAIL** |
| Seeded supported: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded atomic: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded no leakage: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded unambiguous: correct | ≥ 4 of 5 | 5 of 5 | 5 of 5 | pass |
| Seeded duplicates: correct | ≥ 5 of 6 | 6 of 6 | 6 of 6 | pass |

## Per criterion (corrected hand scores)

| Criterion | Run | My fails | Caught | Catch rate | My passes | False alarms | False alarm rate |
|---|---|---|---|---|---|---|---|
| Atomic | A | 20 | 20 | 100.0% (20/20) | 166 | 3 | 1.8% (3/166) |
| Atomic | B | 20 | 19 | 95.0% (19/20) | 166 | 1 | 0.6% (1/166) |
| Supported | A | 9 | 9 | 100.0% (9/9) | 177 | 3 | 1.7% (3/177) |
| Supported | B | 9 | 8 | 88.9% (8/9) | 177 | 4 | 2.3% (4/177) |
| No leakage | A | 6 | 5 | 83.3% (5/6) | 180 | 1 | 0.6% (1/180) |
| No leakage | B | 6 | 5 | 83.3% (5/6) | 180 | 2 | 1.1% (2/180) |
| Unambiguous | A | 10 | 3 | 30.0% (3/10) | 176 | 0 | 0.0% (0/176) |
| Unambiguous | B | 10 | 4 | 40.0% (4/10) | 176 | 0 | 0.0% (0/176) |
| Duplicates | A | 5 | 5 | 100.0% (5/5) | 181 | 1 | 0.6% (1/181) |
| Duplicates | B | 5 | 5 | 100.0% (5/5) | 181 | 2 | 1.1% (2/181) |

Duplicates both of us flagged, with a different original card: none.

## Clean card rate

| Scorer | Clean card rate |
|---|---|
| Hand (corrected) | 79.6% (148/186) |
| Hand (original) | 86.0% (160/186) |
| Judge run A | 79.0% (147/186) |
| Judge run B | 79.6% (148/186) |

## Seeded examples

| Criterion | Run A correct | Run B correct | Needed |
|---|---|---|---|
| Supported | 5 of 5 | 5 of 5 | 4 |
| Atomic | 5 of 5 | 5 of 5 | 4 |
| No leakage | 5 of 5 | 5 of 5 | 4 |
| Unambiguous | 5 of 5 | 5 of 5 | 4 |
| Duplicates | 6 of 6 | 6 of 6 | 5 |

| Seed | Criterion | Subtlety | Control | Expected | Run A | Run B | Other labels that differ (A / B) |
|---|---|---|---|---|---|---|---|
| sup-1 | supported | obvious | no | N | N | N | — / — |
| sup-2 | supported | obvious | no | N | N | N | — / — |
| sup-3 | supported | moderate | no | N | N | N | — / — |
| sup-4 | supported | subtle | no | N | N | N | — / — |
| sup-5 | supported | subtle | yes | Y | Y | Y | — / — |
| ato-1 | atomic | obvious | no | N | N | N | — / — |
| ato-2 | atomic | moderate | no | N | N | N | — / — |
| ato-3 | atomic | moderate | no | N | N | N | — / — |
| ato-4 | atomic | subtle | no | N | N | N | — / — |
| ato-5 | atomic | moderate | yes | Y | Y | Y | — / — |
| lea-1 | no_leakage | obvious | no | N | N | N | — / — |
| lea-2 | no_leakage | obvious | no | N | N | N | — / — |
| lea-3 | no_leakage | moderate | no | N | N | N | — / — |
| lea-4 | no_leakage | obvious | no | N | N | N | — / — |
| lea-5 | no_leakage | subtle | no | N | N | N | — / — |
| amb-1 | unambiguous | obvious | no | N | N | N | — / — |
| amb-2 | unambiguous | obvious | no | N | N | N | — / — |
| amb-3 | unambiguous | moderate | no | N | N | N | — / — |
| amb-4 | unambiguous | moderate | no | N | N | N | — / — |
| amb-5 | unambiguous | subtle | no | N | N | N | — / — |
| dup-1 | duplicate | obvious | no | sample_029-c03 | sample_029-c03 | sample_029-c03 | — / — |
| dup-2 | duplicate | subtle | no | sample_010-c06 | sample_010-c06 | sample_010-c06 | — / — |
| dup-3 | duplicate | obvious | no | sample_028-c02 | sample_028-c02 | sample_028-c02 | — / — |
| dup-4 | duplicate | moderate | no | sample_004-c03 | sample_004-c03 | sample_004-c03 | — / — |
| dup-5 | duplicate | subtle | yes | — | — | — | — / — |
| dup-6 | duplicate | moderate | no | sample_009-c06 | sample_009-c06 | sample_009-c06 | — / — |

## Self-consistency (run A vs run B)

| Criterion | Agreement | Flipped cards |
|---|---|---|
| Atomic | 97.3% (181/186) | sample_006-c01, sample_007-c05, sample_013-c02, sample_013-c04, sample_013-c06 |
| Supported | 97.8% (182/186) | sample_002-c04, sample_006-c03, sample_006-c06, sample_007-c07 |
| No leakage | 99.5% (185/186) | sample_002-c06 |
| Unambiguous | 99.5% (185/186) | sample_008-c05 |
| Duplicates | 99.5% (185/186) | sample_002-c10 |

| Seeded criterion | Agreement | Flipped seeds |
|---|---|---|
| Atomic | 100.0% (26/26) | — |
| Supported | 100.0% (26/26) | — |
| No leakage | 100.0% (26/26) | — |
| Unambiguous | 100.0% (26/26) | — |
| Duplicates | 100.0% (26/26) | — |

## Retries

A response that doesn't match the batch, such as a grade list that stops short, is retried once. The drop rate is those responses as a share of every API call, including discarded runs. Discarded runs are never graded or compared.

| Pass | Judge run | Status | API calls | Retries | Dropped outputs | Cost |
|---|---|---|---|---|---|---|
| Run A | 2026-10-13_214206 | used; run before retries existed, so it had none | 30 | 0 | 0 | $0.5550 |
| Run B | 2026-10-13_222522 | used | 31 | 1 | 1 | $0.5751 |
| Seeded A | 2026-10-13_223040 | used | 26 | 0 | 0 | $0.5380 |
| Seeded B | 2026-10-13_223531 | used | 26 | 0 | 0 | $0.5407 |
| Discarded 1 | 2026-10-13_214607 | discarded (incomplete) | 30 | 0 | 1 | $0.5221 |
| **Total** | | | 143 | 1 | 2 | $2.7309 |

**Drop rate:** 1.4% (2/143)

- Run B, sample_005: Output did not match the batch: No grade for c02, c03, c04, c05, c06, c07.
- Discarded 1, sample_005: Output did not match the batch: No grade for c02, c03, c04, c05, c06, c07.

## Agreement check

A blind recheck of 20 card+criterion pairs where the original hand score and both judge runs agreed: eval/judge/validation/agreement_sample_v1.csv, random seed 20261017, 5 atomic, 5 supported, 5 no leakage, 5 unambiguous. A pair whose recheck differs is a shared error, where the hand score and both runs were wrong together. Until it's corrected in scores.csv, no catch or false alarm check can see it. The check is reported only; it isn't part of the verdict.

**19 of 20 matched; 1 shared error.**

| Card | Criterion | Agreed | Recheck | Reason |
|---|---|---|---|---|
| sample_015-c05 | unambiguous | Y | N | The question is bit ambiguous in its wording. 'Position' could mean many things and results in many answers potentially being correct. |

**Caveat:** shared errors exist at a rate this sample can't pin down (1/20), and the unambiguous result is likely optimistic.

## Score changes

| Date | Card | Field | Old | New | Prompted by | Provenance | Rubric rule | Reason |
|---|---|---|---|---|---|---|---|---|
| 2026-10-12 | sample_005-c07 | duplicate_of | — | sample_005-c01 | pre-judge | — | Rubric 1.6, No Near-Duplicates: a card is also a near-duplicate if the fact it tests is already contained in an earlier card's answer | sample_005-c01's answer ("Energy flows through ecosystems while matter is repeatedly recycled") already contains the fact that energy is not recycled the way matter is. Applies the rubric 1.6 rule; made before any judge output. |
| 2026-10-17 | sample_005-c02 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Atomic | The question asks two distinct questions, how energy is captured and how it is converted. These could be broken into two distinct flashcards. |
| 2026-10-17 | sample_005-c06 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Atomic | The question is atomic, but nonspecific. The answer states the action that decomposers perform as well as what it does for the environment. These could be split into two flashcards with more specific questions to elicit the desired answers. |
| 2026-10-17 | sample_007-c04 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, Atomic | [after recheck] The answer is stating two actions that are part of the repolarization process. These could be split into two flashcards asking what each channel does during repolarization. |
| 2026-10-17 | sample_007-c05 | atomic | Y | N | 2026-10-13_214206 | blind | Rubric 1.6, Atomic | The question is atomic, but nonspecific. The answer gives both the cause of and definition of hyperpolarization. This could be split into two flashcards with more specific questions. |
| 2026-10-17 | sample_007-c06 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Atomic | The answer gives the definition of the refractory period (as it should), but also includes the phases of the refractory period. The phases could be removed from this cards answer and made into its own flashcard. |
| 2026-10-17 | sample_008-c05 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, Atomic | [after recheck] This is not a very good flashcard due to the quality of the source notes. The notes themselves imply this is an open list and not a closed set. However, the information does deserve to be included in the batch. The model just needs to be clever about how to word these flashcards. |
| 2026-10-17 | sample_008-c06 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Atomic | The questions asks two distinct questions, about how imports and exports affect GDP. These could be split into two flashcards. Additionally, the answer provides information on net export equations which should be a third separate flashcard. |
| 2026-10-17 | sample_010-c02 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Atomic | This honestly could be considered an ambiguous question, which lead to a non-atomic answer. The fact that four Japanese carriers were destroyed could be its own flashcard and the victory at Midway being a big turning point could be another flashcard. |
| 2026-10-17 | sample_010-c03 | atomic | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Atomic | Question asks when Guadalcanal began and ended. These could be two distinct flaschards. |
| 2026-10-17 | sample_006-c06 | supported | Y | N | 2026-10-13_214206 | after judge | Rubric 1.6, Supported | [after judge] The facts the way they are worded in the flashcard are not supported. However,the biggest issue is that it is not atomic as it asks for the year and location. This should be split into two flashcards, one asking the year of the attempted escape and the other asking the location of his capture. |
| 2026-10-17 | sample_006-c10 | supported | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | after judge | Rubric 1.6, Supported | [after judge] This is not a supported flashcard based on the source notes. The notes do not say he led the committee of public safety. However, it is a good flashcard, The model intelligently reworded a messy bullet point to extract a well articulated question with a distinct answer. May need to modify outside context criteria. |
| 2026-10-17 | sample_007-c08 | supported | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Supported | While this is a great flashcard, it is not supported by the source notes. The source notes do mention the Nodes of Ranvier and saltatory conduction jumping from node to node, however it never defines the afformentioned nodes or Nodes of Ranvier as the gaps between myelin on the axons. |
| 2026-10-17 | sample_009-c06 | supported | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Supported | Answer is not supported by source notes alone. It is heavily implied by the surrounding context, such as leading is continuous, lagging… as well as the process of filling the gaps done by the other molecules. However, nowhere in the source notes does it define Okazaki fragments as short DNA segments. Given the name is unintuitive I would say this is unsupported. Nonetheless, asking what Okazaki fragments are would be a good flashcard for this batch, just unfortunately is unsupported without outside context. |
| 2026-10-17 | sample_010-c09 | supported | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Supported | Question is not supported. Nowhere in the source notes does it say that a nuclear bomb was dropped at the specified location on the specified day, despite the location and date being correct and accurate. Technically, this flashcard is not supported without outside context that a nuclear bomb being dropped is the event in question. However, this is an important flashcard to include in the batch, so we may need to modify outside context criteria. |
| 2026-10-17 | sample_010-c10 | supported | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Supported | Question is not supported. Nowhere in the source notes does it say that a nuclear bomb was dropped at the specified location on the specified day, despite the location and date being correct and accurate. Technically, this flashcard is not supported without outside context that a nuclear bomb being dropped is the event in question. However, this is an important flashcard to include in the batch, so we may need to modify outside context criteria. |
| 2026-10-17 | sample_021-c02 | supported | Y | N | 2026-10-13_214206 + 2026-10-13_222522 | after judge | Rubric 1.6, Supported | [after judge] This is almost supported by the source notes. Card should be reworded to 'much' instead of 'most'. |
| 2026-10-17 | sample_001-c03 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, Unambiguous | [after recheck] The flashcard depends on the source text to know what provisions are deemed controversial. However, with good knowledge of the source text, a student should be able to provide all of the answers. The main problem is it is not atomic and the answer could be partially correct. |
| 2026-10-17 | sample_001-c08 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Unambiguous | The question is clear. It's main problem is the potential leakage and just the general fact that it is not a good flashcard worded as it is. |
| 2026-10-17 | sample_002-c01 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, Unambiguous | [after recheck] The question is fairly straight forward. Question is asking for a form of energy not a product. |
| 2026-10-17 | sample_008-c05 | unambiguous | Y | N | 2026-10-13_222522 | after recheck | Rubric 1.6, Unambiguous | [after recheck] The question is ambiguous due to being an open list that can be partially correct. The card should be split and the questions need to be more clear to elicit the correct responses. A student might not know what answer the question is searching for with it worded as is. |
| 2026-10-17 | sample_009-c05 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Unambiguous | Question and answer are clear. This was a bad hand grade. |
| 2026-10-17 | sample_011-c06 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Unambiguous | Question and answer are clear. This could be reworded better to provide a little more context, but it is fine. |
| 2026-10-17 | sample_011-c08 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Unambiguous | Question and answer are clear. This could be reworded better to provide a little more context, but it is fine. |
| 2026-10-17 | sample_011-c10 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, Unambiguous | [after recheck] This is just a bad flashcard as can be seen by my original comment. It is not accurate to say a cleavage furrow is an example of cytokinesis. However, on the question of ambiguity, the flashcard is straightforward and expects one answer. |
| 2026-10-17 | sample_017-c01 | unambiguous | N | Y | 2026-10-13_214206 + 2026-10-13_222522 | blind | Rubric 1.6, Unambiguous | Flashcard is unambiguous but not atomic. This was a bad hand grade. |
| 2026-10-17 | sample_007-c03 | duplicate_of | — | sample_007-c02 | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, No near-duplicates: fact already contained in an earlier card's answer | [after recheck] Based on rubric 1.6 criteria this is technically a duplicate. However, we may need to change the rubric because the questions are distinct. If the flashcards are very similar in their answers, but the questions are distinct it should probably not be a duplicate and this is a perfect example of why. |
| 2026-10-17 | sample_017-c04 | duplicate_of | — | sample_017-c02 | 2026-10-13_214206 + 2026-10-13_222522 | after recheck | Rubric 1.6, No near-duplicates: fact already contained in an earlier card's answer | [after recheck] This is borderline. Both questions are about a similar topic however one is asking a definition the other is asking purpose within a specified context. The fact is already in c02’s answer (the 1.6 rule). |
| 2026-10-18 | sample_015-c05 | unambiguous | Y | N | agreement_sample_v1 | agreement check | Rubric 1.6, Unambiguous | The question is bit ambiguous in its wording. 'Position' could mean many things and results in many answers potentially being correct. |
| 2026-10-20 | sample_010-c02 | unambiguous | Y | N | v2 unambiguous scoring | consistency check | Rubric 1.6, Unambiguous | Significance question: several different answers would be correct. Aligned with the standard applied when scoring prompt v2's unambiguous sheet (v2 scored first, 2026-10-20). |
| 2026-10-20 | sample_010-c04 | unambiguous | Y | N | v2 unambiguous scoring | consistency check | Rubric 1.6, Unambiguous | Significance question: several different answers would be correct. Aligned with the standard applied when scoring prompt v2's unambiguous sheet (v2 scored first, 2026-10-20). |
| 2026-10-20 | sample_015-c04 | unambiguous | Y | N | v2 unambiguous scoring | consistency check | Rubric 1.6, Unambiguous | Significance question: several different answers would be correct. Aligned with the standard applied when scoring prompt v2's unambiguous sheet (v2 scored first, 2026-10-20). |
| 2026-10-20 | sample_022-c03 | unambiguous | Y | N | v2 unambiguous scoring | consistency check | Rubric 1.6, Unambiguous | Significance question: several different answers would be correct. Aligned with the standard applied when scoring prompt v2's unambiguous sheet (v2 scored first, 2026-10-20). |
| 2026-10-21 | sample_007-c03 | duplicate_of | sample_007-c02 | — | v2 review | consistency check | Rubric 1.6, No near-duplicates: fact already contained in an earlier card's answer | The fact it tests (what the term depolarization means) isn't in sample_007-c02's answer. Aligned with the decision on the same pair in prompt v2's review (2026-10-21). |

## Disagreements (corrected hand scores)

Every card where either judge run differs from the corrected hand score. A card is marked † where the latest change to its hand score for that criterion came from the judge review.

### Atomic (5)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_006-c01 | What event triggered the calling of the Estates General in 1789? | A financial crisis and bad harvests | Y | Y | N | B: The answer 'A financial crisis and bad harvests' gives two separate causes, so a student could recall one and forget the other. | — |
| sample_007-c05 † | What is hyperpolarization? | The condition that occurs when potassium channels stay open too long, causing the membrane potential to become more negative than the resting level | N | N | Y | — | The answer gives the correct answer based on the context of the flashcard, then infers based on prior context after the comma in the answer. This is good behavior but not explicity allowed by the rubric. |
| sample_013-c02 | What are the major functions of carbohydrates? | Quick energy; structural support | Y | N | Y | A: The answer 'Quick energy; structural support' lists separate functions a student could partially recall, not a closed set the question itself defines. | Closed set example. |
| sample_013-c04 | What are the major functions of proteins? | Enzymes; transport; structure | Y | N | Y | A: The answer 'Enzymes; transport; structure' lists separate functions a student could partially recall, not a closed set the question itself defines. | Closed set example. |
| sample_013-c06 | What are the major functions of lipids? | Energy storage; membranes | Y | N | Y | A: The answer 'Energy storage; membranes' lists separate functions a student could partially recall, not a closed set the question itself defines. | Closed set example. |

### Supported (6)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_002-c04 | What products are released when water is split during light-dependent reactions? | Oxygen, electrons, and protons | Y | Y | N | B: The question says electrons and protons are 'released', but the notes only say water splitting releases oxygen and 'contributing electrons and protons'. | Closed set. Does not need to be split into multiple flashcards v1.5: atomic Y to N under the closed set test: the notes say something different about each item. |
| sample_006-c03 | What was the Tennis Court Oath? | A declaration that the Third Estate would not leave until a constitution was made | Y | N | Y | A: The answer attributes the oath to 'the Third Estate', but the notes only say 'they weren't leaving' without identifying who took the oath. | — |
| sample_006-c06 † | In what year and at what location did Louis XVI attempt to escape Paris? | 1791 at Varennes | N | N | Y | — | The question asks two questions in one and the answer has two answers. This could be split into multiple flashcards. |
| sample_007-c07 | What is saltatory conduction? | A method of action potential propagation along myelinated axons where the action potential jumps from node to node | Y | Y | N | B: The answer says 'along myelinated axons', but the notes never mention axons. | Another exellent example of the model taking a messy bullet point and rewording it into a clean flashcard. |
| sample_013-c05 | What is the building block of lipids? | Glycerol + fatty acids | Y | N | N | A: The card presents 'Glycerol + fatty acids' as 'the building block of lipids', dropping the notes' qualifier '(common form)'. / B: The card presents 'Glycerol + fatty acids' as the building block of lipids, dropping the notes' qualifier '(common form)' and so overstating the claim. | Closed set example. |
| sample_016-c05 | In Python, what does a negative index like nums[-1] refer to? | The last element in the list | Y | N | N | A: The answer 'The last element in the list' is never stated; the notes only say nums[-1] returns 50 and that negative indexes count from the end. / B: The answer 'The last element in the list' generalizes beyond the notes, which only state that nums[-1] returns 50 and that negative indexes count from the end. | — |

### No leakage (3)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_001-c08 | How did German resentment toward the Treaty of Versailles relate to the rise of the Nazi movement? | It became an important factor exploited by Adolf Hitler and the Nazi movement | N | Y | Y | — | Question is essentially the answer as a question. Could be perceived as ambiguous if a student thought it was looking for a deeper answer. |
| sample_002-c06 | What molecule is reduced by electrons from light-dependent reactions to form NADPH? | NADP+ | Y | Y | N | B: The question's phrase 'reduced... to form NADPH' makes the answer 'NADP+' directly deducible from the question text. | — |
| sample_002-c10 | How does the Calvin cycle depend on light-dependent reactions if it does not directly require photons? | It depends on products generated by the light-dependent reactions | Y | N | N | A: The question 'depend on light-dependent reactions' gives away the answer 'depends on products generated by the light-dependent reactions'. / B: The question names 'light-dependent reactions' and the answer 'products generated by the light-dependent reactions' adds little beyond what the question supplies. | Batch level note: This run produced 10 flashcards for this sample. I identified 10-11 distinct facts so this is a good range for this sample. |

### Unambiguous (7)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_008-c05 † | What are limitations of using GDP per capita as a measure? | It does not tell the distribution of output/income, unpaid work, or environmental costs | N | Y | N | — | Closed set example. |
| sample_010-c02 | What was the significance of the US victory at Midway? | Four Japanese carriers were lost and it was a big turning point | N | Y | Y | — | — |
| sample_010-c04 | What was the significance of the Battle of Guadalcanal? | It was the first big Allied offensive in the Pacific | N | Y | Y | — | — |
| sample_015-c04 | What was the significance of the U.S. entering World War II in 1941? | Wartime production greatly expanded employment and output | N | Y | Y | — | — |
| sample_015-c05 | What position did the U.S. emerge as following the end of World War II in 1945? | A major global economic and military power | N | Y | Y | — | — |
| sample_020-c04 | What value does the provided binary_search function return when the target is not found? | -1 | N | Y | Y | — | Question does not show the code snippet in question. It says "provided binary search function" without showing the function. The code snippet should be included in the question to avoid ambiguity. |
| sample_022-c03 | What historical significance did the Magna Carta have in the development of government? | It became an important symbol in the development of constitutional government. | N | Y | Y | — | — |

### Duplicates (2)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_002-c10 | How does the Calvin cycle depend on light-dependent reactions if it does not directly require photons? | It depends on products generated by the light-dependent reactions | — | — | sample_002-c09 | B: The question states 'it does not directly require photons', which is the same fact c09 tests. | Batch level note: This run produced 10 flashcards for this sample. I identified 10-11 distinct facts so this is a good range for this sample. |
| sample_007-c03 | What is depolarization? | The influx of sodium ions into the neuron | — | sample_007-c02 | sample_007-c02 | A: The fact that sodium flows into the cell, which the notes call depolarization, is already contained in c02's answer 'allowing sodium ions to flow into the cell'. / B: The fact that sodium flows into the cell, the answer here, is already contained in c02's answer 'allowing sodium ions to flow into the cell'. | This was marked as a clean flashcard because it is the best answer based on the context in the notes. However, it is not necessarily the best answer to the question given outside context. |

