# Judge Validation: judge:opus-5.5:v1

**Verdict (corrected hand scores): NOT VALIDATED**

- **Judge:** claude-opus-5-5, prompt v1, effort low, judge hash d21413e84dec
- **Ground truth:** eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2/scores.csv, run 2026-10-02_215109 under rubric 1.6 and test set 2
- **Judge runs:** A = 2026-10-13_214206, B = 2026-10-13_222522
- **Seeded runs:** A = 2026-10-13_223040, B = 2026-10-13_223531
- **Judge cost:** $0.5550, $0.5751, $0.5380, $0.5407 (runs A, B, seeded A, seeded B)
- **Total spent, including discarded runs:** $2.7309
- **Retries:** 1; drop rate 1.4% (2/143) of API calls, including discarded runs (see [Retries](#retries))
- **Score changes:** 1 pre-judge, 0 prompted by the judge (see [Score changes](#score-changes))

Every threshold must hold in both runs. Catch thresholds allow a fixed number of misses (unambiguous 2, atomic 2, no leakage 1), so they still apply if a hand score is corrected.

## Checks against the corrected hand scores

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

## Checks against the original hand scores

No score has been changed because of the judge, so these are the same as above.

## Per criterion (corrected hand scores)

| Criterion | Run | My fails | Caught | Catch rate | My passes | False alarms | False alarm rate |
|---|---|---|---|---|---|---|---|
| Atomic | A | 11 | 11 | 100.0% (11/11) | 175 | 12 | 6.9% (12/175) |
| Atomic | B | 11 | 11 | 100.0% (11/11) | 175 | 9 | 5.1% (9/175) |
| Supported | A | 2 | 2 | 100.0% (2/2) | 184 | 10 | 5.4% (10/184) |
| Supported | B | 2 | 2 | 100.0% (2/2) | 184 | 10 | 5.4% (10/184) |
| No leakage | A | 6 | 5 | 83.3% (5/6) | 180 | 1 | 0.6% (1/180) |
| No leakage | B | 6 | 5 | 83.3% (5/6) | 180 | 2 | 1.1% (2/180) |
| Unambiguous | A | 12 | 3 | 25.0% (3/12) | 174 | 0 | 0.0% (0/174) |
| Unambiguous | B | 12 | 3 | 25.0% (3/12) | 174 | 1 | 0.6% (1/174) |
| Duplicates | A | 4 | 4 | 100.0% (4/4) | 182 | 2 | 1.1% (2/182) |
| Duplicates | B | 4 | 4 | 100.0% (4/4) | 182 | 3 | 1.6% (3/182) |

Duplicates both of us flagged, with a different original card: none.

## Clean card rate

| Scorer | Clean card rate |
|---|---|
| Hand (corrected) | 86.0% (160/186) |
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

## Score changes

| Date | Card | Field | Old | New | Prompted by | Rubric rule | Reason |
|---|---|---|---|---|---|---|---|
| 2026-10-12 | sample_005-c07 | duplicate_of | — | sample_005-c01 | pre-judge | Rubric 1.6, No Near-Duplicates: a card is also a near-duplicate if the fact it tests is already contained in an earlier card's answer | sample_005-c01's answer ("Energy flows through ecosystems while matter is repeatedly recycled") already contains the fact that energy is not recycled the way matter is. Applies the rubric 1.6 rule; made before any judge output. |

## Disagreements (corrected hand scores)

Every card where either judge run differs from the corrected hand score. Cards whose hand score was corrected because of the judge are marked †.

### Atomic (13)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_005-c02 | How do producers such as plants and algae capture and convert energy? | They capture energy from sunlight through photosynthesis and convert it into chemical energy | Y | N | N | A: The answer contains two separate facts, 'capture energy from sunlight through photosynthesis' and 'convert it into chemical energy', which could be partially recalled. / B: The answer combines two facts, 'capture energy from sunlight through photosynthesis' and 'convert it into chemical energy', which could be recalled partially. | — |
| sample_005-c06 | What do decomposers do? | They break down dead organisms and waste, and return nutrients to the environment | Y | N | N | A: The answer combines two separate facts, 'break down dead organisms and waste' and 'return nutrients to the environment', which could be partially recalled. / B: The answer combines 'break down dead organisms and waste' and 'return nutrients to the environment', two facts that could be recalled partially. | — |
| sample_006-c01 | What event triggered the calling of the Estates General in 1789? | A financial crisis and bad harvests | Y | Y | N | B: The answer 'A financial crisis and bad harvests' gives two separate causes, so a student could recall one and forget the other. | — |
| sample_007-c04 | What causes repolarization of the neuronal membrane? | Sodium channels close/inactivate and potassium channels open, allowing potassium ions to flow out | Y | N | N | A: The answer combines separate facts, 'Sodium channels close/inactivate' and 'potassium channels open, allowing potassium ions to flow out', so a student could get it partially right. / B: The answer combines separate facts, 'Sodium channels close/inactivate' and 'potassium channels open, allowing potassium ions to flow out', so it could be partially recalled. | — |
| sample_007-c05 | What is hyperpolarization? | The condition that occurs when potassium channels stay open too long, causing the membrane potential to become more negative than the resting level | Y | N | Y | A: The answer combines the cause 'potassium channels stay open too long' with a separate definition 'more negative than the resting level'. | The answer gives the correct answer based on the context of the flashcard, then infers based on prior context after the comma in the answer. This is good behavior but not explicity allowed by the rubric. |
| sample_007-c06 | What is the refractory period? | A period during which the neuron cannot immediately fire in the same way, consisting of an absolute phase followed by a relative phase | Y | N | N | A: The answer combines the definition 'cannot immediately fire in the same way' with a separate fact about its phases, 'an absolute phase followed by a relative phase'. / B: The answer combines the definition 'cannot immediately fire in the same way' with the separate fact 'an absolute phase followed by a relative phase'. | — |
| sample_008-c05 | What are limitations of using GDP per capita as a measure? | It does not tell the distribution of output/income, unpaid work, or environmental costs | Y | N | N | A: The answer lists 'distribution', 'unpaid work', and 'environmental costs' from an open-ended 'etc.' list, so it is not a closed set and can be partially recalled. / B: The answer lists 'distribution..., unpaid work, or environmental costs', and the notes end that list with 'etc.', so it is an open list a student could recall only part of. | Closed set example. |
| sample_008-c06 | How do exports and imports affect GDP? | Exports add to GDP and imports subtract from GDP, calculated as net exports (NX = X - M) | Y | N | N | A: The answer combines how exports and imports each affect GDP with the formula 'NX = X - M', which are separate facts that can be partially recalled. / B: The answer combines the effect of exports and imports with the separate formula 'NX = X - M', so it can be partially recalled. | Batch-level note: Run produced 6 flashcards. This is a a good number and the flashcards were largely well done. If the model broke up this card into two with one asking for the net export equation that would be fine. Additionally, an additional card could be added for GDP being good for average output/income. So 6-8 is a good range for this sample. |
| sample_010-c02 | What was the significance of the US victory at Midway? | Four Japanese carriers were lost and it was a big turning point | Y | N | N | A: The answer combines two separate facts, 'Four Japanese carriers were lost' and 'it was a big turning point', so it can be partially right. / B: The answer combines two separate facts, 'Four Japanese carriers were lost' and 'it was a big turning point', so a student could recall one and not the other. | — |
| sample_010-c03 | When did the Battle of Guadalcanal begin and end? | August 1942 to February 1943 | Y | N | N | A: The question asks for both 'begin and end' dates, two separate facts a student could partially recall. / B: The card asks for both when Guadalcanal 'began and end[ed]', two separate dates that could be partially recalled. | — |
| sample_013-c02 | What are the major functions of carbohydrates? | Quick energy; structural support | Y | N | Y | A: The answer 'Quick energy; structural support' lists separate functions a student could partially recall, not a closed set the question itself defines. | Closed set example. |
| sample_013-c04 | What are the major functions of proteins? | Enzymes; transport; structure | Y | N | Y | A: The answer 'Enzymes; transport; structure' lists separate functions a student could partially recall, not a closed set the question itself defines. | Closed set example. |
| sample_013-c06 | What are the major functions of lipids? | Energy storage; membranes | Y | N | Y | A: The answer 'Energy storage; membranes' lists separate functions a student could partially recall, not a closed set the question itself defines. | Closed set example. |

### Supported (12)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_002-c04 | What products are released when water is split during light-dependent reactions? | Oxygen, electrons, and protons | Y | Y | N | B: The question says electrons and protons are 'released', but the notes only say water splitting releases oxygen and 'contributing electrons and protons'. | Closed set. Does not need to be split into multiple flashcards v1.5: atomic Y to N under the closed set test: the notes say something different about each item. |
| sample_006-c03 | What was the Tennis Court Oath? | A declaration that the Third Estate would not leave until a constitution was made | Y | N | Y | A: The answer attributes the oath to 'the Third Estate', but the notes only say 'they weren't leaving' without identifying who took the oath. | — |
| sample_006-c06 | In what year and at what location did Louis XVI attempt to escape Paris? | 1791 at Varennes | Y | N | Y | A: The question says Louis attempted to escape 'at' Varennes, but the notes say he was 'caught at Varennes', not that he escaped from there. | The question asks two questions in one and the answer has two answers. This could be split into multiple flashcards. |
| sample_006-c10 | Who led the Committee of Public Safety during the Reign of Terror? | Robespierre | Y | N | N | A: The question claims Robespierre 'led the Committee of Public Safety', but the notes only list 'Robespierre, Committee of Public Safety' without stating that he led it. / B: The notes only list 'Robespierre, Committee of Public Safety' and never state that Robespierre 'led' the Committee. | This is an excellent example of the model taking a messy bullet point and rewording it into a clear flashcard. |
| sample_007-c07 | What is saltatory conduction? | A method of action potential propagation along myelinated axons where the action potential jumps from node to node | Y | Y | N | B: The answer says 'along myelinated axons', but the notes never mention axons. | Another exellent example of the model taking a messy bullet point and rewording it into a clean flashcard. |
| sample_007-c08 | What are the Nodes of Ranvier? | The gaps between myelin sheaths where saltatory conduction occurs during action potential propagation | Y | N | N | A: The answer adds 'The gaps between myelin sheaths', which the notes never state. / B: The answer defines the nodes as 'gaps between myelin sheaths', which the notes never state. | Batch-level note: 8 cards were generated in this run. That is the correct number of distinct facts. |
| sample_009-c06 | What are Okazaki fragments? | Short DNA segments on the lagging strand; each starts with a primer and DNA polymerase fills them, then ligase seals them | Y | N | N | A: The answer describes the fragments as 'Short DNA segments', but the notes never say they are short. / B: The answer adds 'Short DNA segments', which the notes never state. | Answer is atomic up until semi-colon, then expands with additional facts that could have been made their own flashcards. Additional flashcard regarding polymerase function and ligase function possible. |
| sample_010-c09 | On what date was the atomic bomb dropped on Hiroshima? | August 6 | Y | N | N | A: The question adds 'the atomic bomb was dropped', which the notes never state; they only say 'Hiroshima Aug 6'. / B: The question adds 'the atomic bomb was dropped', which the notes never state; they only list 'Hiroshima Aug 6'. | — |
| sample_010-c10 | On what date was the atomic bomb dropped on Nagasaki? | August 9 | Y | N | N | A: The question adds 'the atomic bomb was dropped', which the notes never state; they only say 'Nagasaki Aug 9'. / B: The question adds 'the atomic bomb was dropped', which the notes never state; they only list 'Nagasaki Aug 9'. | — |
| sample_013-c05 | What is the building block of lipids? | Glycerol + fatty acids | Y | N | N | A: The card presents 'Glycerol + fatty acids' as 'the building block of lipids', dropping the notes' qualifier '(common form)'. / B: The card presents 'Glycerol + fatty acids' as the building block of lipids, dropping the notes' qualifier '(common form)' and so overstating the claim. | Closed set example. |
| sample_016-c05 | In Python, what does a negative index like nums[-1] refer to? | The last element in the list | Y | N | N | A: The answer 'The last element in the list' is never stated; the notes only say nums[-1] returns 50 and that negative indexes count from the end. / B: The answer 'The last element in the list' generalizes beyond the notes, which only state that nums[-1] returns 50 and that negative indexes count from the end. | — |
| sample_021-c02 | Through what process does the mitochondrion produce most of a eukaryotic cell's ATP? | Oxidative phosphorylation | Y | N | N | A: The question says 'most of a eukaryotic cell's ATP', but the notes only say 'much of' it. / B: The question says 'most of' a eukaryotic cell's ATP, but the notes only say 'much of'. | This flashcard is stated in the specified duplicate flashcard because the previous flashcard incorrectly provided too much context in the answer. It is being marked as a duplicate as a result. The run correctly produced two flashcards, however, it resulted in a duplicate. |

### No leakage (3)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_001-c08 | How did German resentment toward the Treaty of Versailles relate to the rise of the Nazi movement? | It became an important factor exploited by Adolf Hitler and the Nazi movement | N | Y | Y | — | Question is essentially the answer as a question. Could be perceived as ambiguous if a student thought it was looking for a deeper answer. |
| sample_002-c06 | What molecule is reduced by electrons from light-dependent reactions to form NADPH? | NADP+ | Y | Y | N | B: The question's phrase 'reduced... to form NADPH' makes the answer 'NADP+' directly deducible from the question text. | — |
| sample_002-c10 | How does the Calvin cycle depend on light-dependent reactions if it does not directly require photons? | It depends on products generated by the light-dependent reactions | Y | N | N | A: The question 'depend on light-dependent reactions' gives away the answer 'depends on products generated by the light-dependent reactions'. / B: The question names 'light-dependent reactions' and the answer 'products generated by the light-dependent reactions' adds little beyond what the question supplies. | Batch level note: This run produced 10 flashcards for this sample. I identified 10-11 distinct facts so this is a good range for this sample. |

### Unambiguous (10)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_001-c03 | What were the main controversial provisions of the Treaty of Versailles? | Placing responsibility for wartime damage on Germany, requiring substantial reparations, limiting the German military to 100,000 personnel, and prohibiting Germany from maintaining an air force or submarines | N | Y | Y | — | Answer takes wording directly from text, rather than simplifying |
| sample_001-c08 | How did German resentment toward the Treaty of Versailles relate to the rise of the Nazi movement? | It became an important factor exploited by Adolf Hitler and the Nazi movement | N | Y | Y | — | Question is essentially the answer as a question. Could be perceived as ambiguous if a student thought it was looking for a deeper answer. |
| sample_002-c01 | What does photosynthesis convert light energy into? | Chemical energy stored in organic molecules | N | Y | Y | — | Question is a bit ambiguous in its wording. It should be reworded as what type of energy to photosynthesis convert light energy into. With current wording any of the products of photosynthesis could be correct. |
| sample_008-c05 | What are limitations of using GDP per capita as a measure? | It does not tell the distribution of output/income, unpaid work, or environmental costs | Y | Y | N | B: The question 'What are limitations' has no fixed answer set, since the notes' list ends with 'etc.', so many different answers could be correct. | Closed set example. |
| sample_009-c05 | What is the structure of the leading strand during DNA replication? | Basically continuous | N | Y | Y | — | Verbatim: Question is reworded but answer is taken verbatim from the source notes. The source notes did not describe the fact well so verbatim makes it ambiguous. |
| sample_011-c06 | During which stage does crossing over occur? | Prophase I | N | Y | Y | — | Question is worded a bit ambiguously. Should have been reworded to what mitotic phase instead of just what stage, or something to that effect. |
| sample_011-c08 | During which stage does independent assortment occur? | Metaphase I | N | Y | Y | — | Question is worded a bit ambiguously. Should have been reworded to what mitotic phase instead of just what stage, or something to that effect. |
| sample_011-c10 | What is an example of cytokinesis in animal cells? | Cleavage furrow | N | Y | Y | — | Question is worded incorrectly leading the answer to be ambiguous. It is supported by the labels of the chart however, saying that a cleavage furrow is an example of cytokinesis is not correct. Should have been reworded because a cleavage furrow is more a feature of cytokinesis than it is an example of it. Model should account for poor labels. |
| sample_017-c01 | In C++, what is a reference? | An alias for an existing object, commonly used to avoid copying when passing arguments. | N | Y | Y | — | Answer could have been split into two flashcards, one for definition of reference and the other for why it is used. Current flashcard expects both answers. |
| sample_020-c04 | What value does the provided binary_search function return when the target is not found? | -1 | N | Y | Y | — | Question does not show the code snippet in question. It says "provided binary search function" without showing the function. The code snippet should be included in the question to avoid ambiguity. |

### Duplicates (3)

| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |
|---|---|---|---|---|---|---|---|
| sample_002-c10 | How does the Calvin cycle depend on light-dependent reactions if it does not directly require photons? | It depends on products generated by the light-dependent reactions | — | — | sample_002-c09 | B: The question states 'it does not directly require photons', which is the same fact c09 tests. | Batch level note: This run produced 10 flashcards for this sample. I identified 10-11 distinct facts so this is a good range for this sample. |
| sample_007-c03 | What is depolarization? | The influx of sodium ions into the neuron | — | sample_007-c02 | sample_007-c02 | A: The fact that sodium flows into the cell, which the notes call depolarization, is already contained in c02's answer 'allowing sodium ions to flow into the cell'. / B: The fact that sodium flows into the cell, the answer here, is already contained in c02's answer 'allowing sodium ions to flow into the cell'. | This was marked as a clean flashcard because it is the best answer based on the context in the notes. However, it is not necessarily the best answer to the question given outside context. |
| sample_017-c04 | What is the purpose of the `const` keyword in a const reference parameter in C++? | It prevents the function from changing the referred-to object through that parameter. | — | sample_017-c02 | sample_017-c02 | A: Its answer, 'prevents the function from changing the referred-to object', tests the same fact as c02's answer, 'Read an object without modifying it'. / B: Tests the same fact as c02: c04's answer 'prevents the function from changing the referred-to object' restates c02's 'Read an object without modifying it.' | Batch-level note: Run produced only 4 flashcards. Should have produced about 6. Missing questions: pupose or common use of a reference (wrapped into the first flashcards answer), syntax of a const reference parameter |

