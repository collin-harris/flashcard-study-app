# Evaluation Rubric: AI Flashcard Generation

**Project:** Flashcard & Spaced Repetition Study App
**Rubric Version:** 1.0
**Last Updated:** September 2026
**Status:** Active

---

## Purpose

This rubric defines how generated flashcards are scored against the test set
in `eval/test_set/test_set.json`. It was written before any model output was
reviewed, so that scoring reflects what good output should look like rather
than what a particular model happens to produce.

The test set and this rubric stay fixed across evaluation runs. What changes
between runs is the system under test: the prompt, the model, or the
pipeline design. Holding the test set and rubric constant is what makes
scores comparable from one run to the next.

---

## Unit of Evaluation

The unit of evaluation is the **batch**: everything the system produces for
one test sample. This matches what a user experiences, since pasting one set
of notes returns a set of cards, not a single card.

Some criteria are scored per card and aggregated; others are properties of
the batch as a whole.

---

## Stage 1: Input Gate

Scored on **all 35 samples**.

### Expected outcome

| Category tag         | Expected outcome |
|----------------------|------------------|
| `unusable_input`     | Reject           |
| All other categories | Accept           |

`too_short` samples contain real content and should be **accepted**. They are
expected to produce a small number of cards, not a rejection.

### Error types

| Error            | Definition                                      |
|------------------|-------------------------------------------------|
| False rejection  | A sample expected to be accepted was rejected   |
| False acceptance | A sample expected to be rejected produced cards |

**False rejection is the more serious error.** A student who pastes real
notes and is refused has no recourse. Generated cards from unusable input
are visible to the student during the review step before saving, and any
invented content is also caught by the Stage 2 "supported" criterion. When
the gate is uncertain, it should lean toward accepting.

### Scoring

- Samples that fail Stage 1 in either direction are **not** scored in
  Stage 2.
- Samples correctly rejected have no cards and are not scored in Stage 2.
- Only **correctly accepted** samples proceed to Stage 2.

This scoring is independent of how the gate is implemented (a separate
classification call, a single call that returns either cards or a
rejection, or non-AI pre-checks). The rubric measures the decision, not the
mechanism.

---

## Stage 2: Card Quality

Scored on **correctly accepted samples only**.

### Per-card criteria

Each card receives a pass or fail on each of the following four criteria.

#### 1. Atomic

> A card is **atomic** if there is no meaningful way to get its answer
> partially right.
>
> **Exception:** an answer that lists a **closed set of six or fewer
> items** (a fixed group the question itself defines) counts as atomic.

**Why it matters:** SM-2 schedules each card from a single 0–5 rating. If a
card contains several facts and the student remembers only some of them,
no single rating is correct, and the schedule will be wrong for part of the
card.

**Examples:**

- **Q:** What did the Treaty of Versailles require of Germany?
  **A:** Reparations, military limits, and territorial changes.
  → **Fail.** These are separate facts, not a defined closed set. A
  student could remember some and forget others.

- **Q:** What are the three states of a JavaScript promise?
  **A:** Pending, fulfilled, rejected.
  → **Pass.** A closed set of three items that the question itself defines.

- **Q:** Why is the lagging strand synthesized discontinuously?
  **A:** Because the strands are antiparallel and synthesis only proceeds
  5' to 3'.
  → **Pass.** One idea, even though the answer is a full sentence.

#### 2. Supported

> A card is **supported** if every claim in its question and answer is
> explicitly stated in the source text. Rewording is allowed. Combining
> facts that are each stated in the source is allowed. Adding facts from
> outside the source, or drawing conclusions the source does not state,
> fails.

**Why it matters:** the goal is zero hallucination. This rule also keeps
scoring practical: each card is checked against the source text, not
fact-checked against the outside world.

**Examples:**

- **Source:** "The Magna Carta was sealed in 1215..."
  **Q:** Which English king sealed the Magna Carta?
  **A:** King John.
  → **Fail.** Historically correct, but the source never mentions King
  John. The fact came from outside the student's material.

- **Source:** States that only a fraction of the energy at one trophic level
  is transferred to the next.
  **Q:** Why are there usually fewer top predators than producers in an
  ecosystem?
  → **Fail.** The conclusion follows logically, but the source never says
  anything about predator numbers. This is inference, not a stated fact.

- **Source:** "...organisms use much of it for metabolism and lose energy as
  heat."
  **Q:** What happens to most of the energy at each trophic level?
  **A:** It is spent on metabolism and lost as heat.
  → **Pass.** The answer rewords the source without adding anything new.

#### 3. No Answer Leakage

> A card **leaks** if its answer can be found in, or directly deduced from,
> the question text itself.
>
> **Test:** could someone answer correctly using only the words in the
> question?

**Examples:**

- **Q:** The mitochondrion produces ATP through oxidative phosphorylation.
  What process does the mitochondrion use to produce ATP?
  **A:** Oxidative phosphorylation.
  → **Fail.** The answer appears in the question itself.

- **Q:** Through what process does the mitochondrion produce much of a
  cell's ATP?
  **A:** Oxidative phosphorylation.
  → **Pass.** The question gives no clue to the answer.

#### 4. Unambiguous

> A card is **unambiguous** if a student who knows the material would know
> exactly what the card is asking, and there is only one correct answer (or
> one closed set, per the atomic rule).
>
> **Test:** hide the source text and read the question alone. It fails if
> it depends on context from the source ("it," "this process," "the
> above"), or if multiple different answers would be correct.

**Examples:**

- **Q:** What happened in 1792?
  → **Fail.** Several events from that year would be correct answers, so a
  student can't tell which one the card wants.

- **Q:** What does it regulate?
  → **Fail.** "It" only makes sense next to the original source text.

- **Q:** In what year did France become a republic?
  **A:** 1792.
  → **Pass.** Clear on its own, with one correct answer.

### Batch-level criteria

#### 5. No Near-Duplicates

> Two cards are **near-duplicates** if they test the same fact, regardless
> of wording or direction, **including reversed term/definition pairs**.

When a card duplicates an earlier card in the batch, the later card is
counted as a duplicate.

**Examples:**

- **Card 1 Q:** What is the powerhouse of the cell?
  **Card 2 Q:** Which organelle is called the cell's powerhouse?
  → **Duplicate.** The same fact, worded two ways.

- **Card 1 Q:** What is opportunity cost?
  **A:** The value of the next-best alternative given up when making a
  choice.
  **Card 2 Q:** What term describes the value of the next-best alternative
  given up when making a choice?
  **A:** Opportunity cost.
  → **Duplicate.** The same fact tested in opposite directions (a reversed
  pair).

- **Card 1 Q:** In what year was the Magna Carta sealed?
  **Card 2 Q:** What did the Magna Carta place limits on?
  → **Not a duplicate.** Same topic, but the cards test different facts.

Reversed pairs are counted as duplicates because `expected_card_range`
values assume one card per fact. Reversal, if offered, is intended as a
deterministic app feature rather than model output.

#### 6. Card Count

> A batch passes if the number of generated cards falls within the
> sample's `expected_card_range`, inclusive.

---

## Metrics

Each evaluation run records the following.

### Headline

| Metric              | Definition                                             |
|---------------------|--------------------------------------------------------|
| **Clean card rate** | Cards passing all four per-card criteria ÷ total cards |
|                     | scored in Stage 2                                      |

### Stage 1

| Metric                | Definition                                              |
|-----------------------|---------------------------------------------------------|
| False rejection rate  | False rejections ÷ samples expected to be accepted (30) |
| False acceptance rate | False acceptances ÷ samples expected to be rejected (5) |

### Stage 2

| Metric               | Definition                                            |
|----------------------|-------------------------------------------------------|
| Atomic rate          | Atomic cards ÷ total cards scored                     |
| Supported rate       | Supported cards ÷ total cards scored                  |
| No-leakage rate      | Non-leaking cards ÷ total cards scored                |
| Unambiguous rate     | Unambiguous cards ÷ total cards scored                |
| Duplicate-free rate  | Non-duplicate cards ÷ total cards scored              |
| Card count pass rate | Batches within `expected_card_range` ÷ batches scored |

Per-card rates are **pooled** across all cards in all scored batches.

### Breakdown by category

All Stage 1 and Stage 2 metrics are also reported per category tag, so that
failures specific to one input type (for example, tables or code) are
visible rather than averaged away.

### Operational

| Metric                         | Definition                          |
|--------------------------------|-------------------------------------|
| Average cost per generation    | Total API cost ÷ samples run        |
| Average latency per generation | Total generation time ÷ samples run |

---

## Scoring Procedure

For each sample:

1. Record whether the system accepted or rejected the input.
2. Compare against the expected outcome. If Stage 1 failed, record the
   error type and stop.
3. If correctly rejected, stop.
4. If correctly accepted, score each card on the four per-card criteria.
5. Mark any card that duplicates an earlier card in the batch.
6. Record the card count and whether it falls within
   `expected_card_range`.

Then compute the run's metrics and record them in
`eval/results_log.md`.

---

## Run Record

Each run in `eval/runs/` records at minimum:

- Run ID and date
- Rubric version used for scoring
- Model and prompt version
- Gate approach (separate call, combined call, pre-checks, or none)
- All metrics listed above
- Notes on what changed from the previous run and why

---

## Versioning

Any change to a definition, threshold, or metric increments the rubric
version. Past runs keep the version they were scored under. Runs scored
under different rubric versions are not directly comparable; if a
comparison is needed, rescore the earlier run under the current version.

---

## Known Limitations

- **Synthetic messiness.** The `sloppy_bullets` samples are synthetic and
  likely understate the inconsistency of real student notes. Strong results
  in that category are weaker evidence than they appear.
- **Small rejection sample.** Only 5 samples are expected to be rejected, so
  one wrong gate decision moves the false acceptance rate by 20 percentage
  points. Treat small swings with caution.
- **Single scorer.** Scoring is done by one person. The definitions and
  examples above exist to keep scoring consistent across runs, but some
  judgment remains, particularly for the "supported" and "unambiguous"
  criteria.