# Judge Run 2026-10-13_223040

- **Mode:** seeded
- **Judged:** eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
- **Scorer:** judge:opus-5.5:v1 (judge hash d21413e84dec, effort low)
- **Partial:** No
- **Interrupted:** No
- **Incomplete:** No (error rate 0.0% (0/26))
- **Cost:** $0.5380 total, $0.0207 per sample (including retries)
- **API calls:** 26, of which 0 retries
- **Average latency:** 7.5s per call
- **Tokens:** 16016 input, 0 cache write, 119054 cache read, 22507 output (includes thinking)

Reasons may refer to cards by the judge's IDs (c01, c02, ...), which number the cards in batch order.

## Grades

Only each seed's own card is shown. Expected labels are in `seeded_examples.json`;
`validate_judge.py` compares them.

| Seed | Criterion | Question | Answer | Atomic | Supported | No leakage | Unambiguous | Duplicate of | Reasons |
|---|---|---|---|---|---|---|---|---|---|
| sup-1 | supported | What is the chemical formula of bauxite? | Al2O3·xH2O | Y | N | Y | Y |  | supported: The answer 'Al2O3·xH2O' is not in the notes, which only describe bauxite as an 'Al-rich ore'. |
| sup-2 | supported | At what membrane potential does a neuron reach threshold? | About -55 mV | Y | N | Y | Y |  | supported: The answer 'About -55 mV' is never stated in the notes, which give no threshold value. |
| sup-3 | supported | What ended the Great Depression in the United States? | Wartime production after the U.S. entered World War II in 1941 | Y | N | Y | Y |  | supported: The claim that wartime production 'ended the Great Depression' is never stated; the notes only say it 'greatly expanded employment and output'. |
| sup-4 | supported | What is the worst-case time complexity of binary search? | O(log n) | Y | N | Y | Y |  | supported: The question adds 'worst-case', which the notes never state; they only say the loop runs in O(log n) in the random-access array model. |
| sup-5 | supported | On what date did Japan announce its surrender? | August 15, 1945 | Y | Y | Y | Y |  |  |
| ato-1 | atomic | In Python, how do negative indexes and a negative step behave? | Negative indexes count from the end, and a negative step can reverse traversal | N | Y | Y | Y |  | atomic: The answer combines two separate facts, 'Negative indexes count from the end' and 'a negative step can reverse traversal', which can be partially recalled. |
| ato-2 | atomic | What principles did the August 1789 Declaration of Rights include, and whom did it not really apply to? | Liberty, equality, and popular sovereignty; it didn't really apply to women | N | Y | Y | Y |  | atomic: The card asks for two separate facts, the principles 'liberty, equality, and popular sovereignty' and whom it 'didn't really apply to'. |
| ato-3 | atomic | What does pH measure? | The acidity or basicity of an aqueous solution on a logarithmic scale, on which a neutral solution is 7 at 25°C | N | Y | Y | Y |  | atomic: The answer combines what pH measures with a separate fact, 'on which a neutral solution is 7 at 25°C', so it can be partially right. |
| ato-4 | atomic | What is the key requirement for binary search to work correctly? | The input must be sorted, so that comparing with the middle element justifies discarding half the interval | N | Y | Y | Y |  | atomic: The answer combines the requirement 'The input must be sorted' with the separate reason 'so that comparing with the middle element justifies discarding half the interval'. |
| ato-5 | atomic | Separation of powers allocates which three governmental functions to different branches? | Legislative, executive, and judicial | Y | Y | Y | Y |  |  |
| lea-1 | no_leakage | In C++, can a const reference be used to modify the object it refers to? | No | Y | Y | N | Y |  | no_leakage: The question 'can a const reference be used to modify...' is a yes/no question that can be answered by guessing. |
| lea-2 | no_leakage | In SQL, does WHERE or HAVING filter rows before grouping? | WHERE | Y | Y | N | Y |  | no_leakage: The question 'does WHERE or HAVING' is an either/or question that names both options, so the answer can be guessed. |
| lea-3 | no_leakage | Of demand-pull and cost-push inflation, which can occur when aggregate demand grows faster than an economy's productive capacity? | Demand-pull inflation | Y | Y | N | Y |  | no_leakage: The question is either/or ('Of demand-pull and cost-push inflation, which...'), so the answer can be guessed from the options it names. |
| lea-4 | no_leakage | In subduction, one tectonic plate moves beneath another. What is this process called? | Subduction | Y | Y | N | Y |  | no_leakage: The question opens with 'In subduction, one tectonic plate moves beneath another', which states the answer 'Subduction' outright. |
| lea-5 | no_leakage | What term describes the exchange of DNA that occurs when homologous chromosomes cross over? | Crossing over | Y | Y | N | Y |  | no_leakage: The question says 'when homologous chromosomes cross over', which gives away the answer 'Crossing over'. |
| amb-1 | unambiguous | What does the first print statement in the example output? | [20, 30, 40] | Y | Y | Y | N |  | unambiguous: The question refers to 'the first print statement in the example', which only makes sense with the source notes visible. |
| amb-2 | unambiguous | What does it unzip during DNA replication? | The double helix | Y | Y | Y | N |  | unambiguous: The question 'What does it unzip' uses 'it' (helicase), which only makes sense alongside the source text. |
| amb-3 | unambiguous | What did the act passed in 1935 establish? | Old-age pensions and related programs | Y | Y | Y | N |  | unambiguous: 'the act passed in 1935' depends on the source to identify which act (the Social Security Act) is meant. |
| amb-4 | unambiguous | Which planet has no moons? | Mercury | Y | Y | Y | N |  | unambiguous: The question 'Which planet has no moons?' has two correct answers in the notes, since both Mercury and Venus have 0 moons. |
| amb-5 | unambiguous | Which 1945 Pacific battle had very high casualties? | Iwo Jima | Y | Y | Y | N |  | unambiguous: The question 'Which 1945 Pacific battle had very high casualties?' fits Okinawa as well, since the notes say Okinawa was 'even worse', so more than one answer is correct. |
| dup-1 | duplicate | What is the name for the amount of work or data processed in a unit of time? | Throughput | Y | Y | Y | Y | sample_029-c03 | duplicate: Like c03, it asks for the term for 'the amount of work or data processed in a unit of time', so it tests the same fact in different wording. |
| dup-2 | duplicate | What did bypassing some islands allow US forces in the Pacific to do? | Move closer to Japan while avoiding some heavily defended positions | Y | Y | Y | Y | sample_010-c06 | duplicate: This card tests the same fact as c06, 'move closer to Japan while avoiding some heavily defended positions', only reworded. |
| dup-3 | duplicate | What is a cation? | A positively charged ion | Y | Y | Y | Y | sample_028-c02 | duplicate: 'What is a cation?' is the reversed term/definition pair of c02, which already tests that a positively charged ion is a 'Cation'. |
| dup-4 | duplicate | What can cause cost-push inflation? | Rising wages, energy prices, or other production costs | Y | Y | Y | Y | sample_004-c03 | duplicate: This reverses c03, testing the same fact that cost-push inflation results from 'rising wages, energy prices, or other production costs'. |
| dup-5 | duplicate | Under what model of computation does binary search run in O(log n) time? | The usual random-access array model | Y | Y | Y | Y |  |  |
| dup-6 | duplicate | What enzyme seals Okazaki fragments during DNA replication? | Ligase | Y | Y | Y | Y | sample_009-c06 | duplicate: The fact that ligase seals Okazaki fragments is already in c06's answer: 'then ligase seals them'. |
