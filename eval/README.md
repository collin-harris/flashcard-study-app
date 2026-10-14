# Evaluation

Tooling for measuring the quality of AI-generated flashcards. The runner
(`run_eval.py`) sends every sample in the test set through the same
`generate_cards()` function the API will use
(`backend/app/services/card_generation.py`), so what gets measured is what
gets shipped. It computes the automated metrics defined in
[`rubric.md`](rubric.md) and produces a sheet for hand-scoring the rest.

- `rubric.md`: How generated cards are scored, and the definition of every
  metric
- `test_set/test_set.json`: The 35 test samples, with category tags and
  expected card ranges. Versioned; see [Test set](#test-set)
- `run_eval.py`: The evaluation runner
- `recompute_run.py`: Recomputes a run's automated metrics under the
  current rubric and test set, without calling the API
- `score_run.py`: Turns a run's hand scores into final metrics and records
  the run in `results_log.md`
- `run_judge.py`: Scores a run's judgment-based criteria with the LLM
  judge. See [LLM judge](#llm-judge)
- `validate_judge.py`: Compares judge runs with the hand scores and decides
  whether the judge is validated
- `judge/`: The judge prompt (`judge_prompt_v1.txt`), the seeded examples
  (`seeded_examples.json`), judge runs on the seeded examples
  (`seeded_runs/`), and validation reports (`validation/`)
- `tests/`: Offline tests for the judge, using a stubbed client
- `results_log.md`: The shipping criteria, and one row per valid run,
  rubric and test set version, and scorer, for comparing runs
- `requirements.txt`: The runner's dependencies: `backend/requirements.txt`
  plus `python-dotenv`
- `runs/`: One folder per full run, created by the runner. Partial runs go
  in `runs/partial/`, which is excluded by `.gitignore`

All commands below are run from the repository root.

## Test set

**Test Set Version:** 2

Each run records the test set version and a hash of the test set
(`test_set_hash`), like the prompt hash, so an edit made without a version
bump still shows up as a different hash. Any change to a sample's labels
(`tags` or `expected_card_range`) increments the version. A sample's
`source_text` is never edited, since a run's recorded outputs were
generated from it; to change the text, add a new sample with a new ID.
Runs scored under different test set versions are not directly
comparable; [recompute](#recomputing-a-run) the earlier run under the
current version first.

### Changelog

- **2:** Replaced the `expected_card_range` of every sample expected to be
  accepted with hand-counted ranges. The original ranges came from the
  synthetic data generator that produced the test set and were never
  checked against the notes. The new ranges count one card per distinct
  fact worth studying: a closed set of six or fewer items counts as one
  card, and framing or transition sentences don't count. The counts were
  made after the baseline runs, and some were made after seeing Run 1's
  output, so they may lean toward what the model produced. No
  `source_text` changed, and the `unusable_input` samples stay at
  `[0, 0]`.
- **1:** Initial 35-sample test set. Runs made before test set versioning
  (`2026-10-02_215109` and `2026-10-02_215610`) used this version.

### Known limitations

- **Duplicates are under-tested.** No sample repeats content, so the
  duplicate criterion only catches the model restating a fact in a new
  way, never notes that repeat themselves.

## Setup

The runner uses a local virtual environment rather than Docker. It matches
the backend's Docker image: Python 3.11.16 and the same pinned library
versions.

1. Install [uv](https://docs.astral.sh/uv/) (once per machine). It installs
   to `~/.local/bin` and doesn't need sudo:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install Python 3.11.16 and create the environment in `.venv/` (excluded
   by `.gitignore`):

   ```bash
   uv python install 3.11.16
   uv venv --python 3.11.16 .venv
   UV_LINK_MODE=copy uv pip install --python .venv -r eval/requirements.txt
   ```

   `UV_LINK_MODE=copy` avoids a warning: uv's package cache (in your WSL
   home) and `.venv` (on `/mnt/c`) are on different filesystems, so uv
   can't hardlink between them and copies instead.

**Version matching.** `backend/requirements.txt` pins only direct
dependencies. Their own dependencies resolve to the newest compatible
version at install time, so the image and the venv can drift apart if
they're built on different days. To check, compare:

```bash
uv pip freeze --python .venv
docker compose run --rm --no-deps backend pip freeze
```

When this was set up (2026-09-29) the two matched exactly, except for
`packaging`, which exists only in the image because the base image's
`wheel` needs it. Neither the app nor the runner uses it.

**Startup delay.** Each run spends roughly 20 seconds importing Python
packages before the first sample starts. This comes from keeping `.venv`
on the Windows-mounted `/mnt/c` path, where WSL2 file access is slow; the
same import takes about a second from the WSL home folder. The very first
run after installing takes a couple of minutes while Python writes its
bytecode cache.

## API key

The runner needs `ANTHROPIC_API_KEY`. It looks in two places:

1. **The shell environment.** A key exported in the shell always wins. To
   keep the key out of your shell history, prompt for it instead of typing
   it inline:

   ```bash
   read -s ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
   ```

2. **`.env` at the repository root**, the same file Docker Compose uses
   (see `.env.example`). The runner reads only `ANTHROPIC_API_KEY` from
   it. Other values in the file, such as `DATABASE_URL`, are never loaded.

If neither has the key, the runner exits with a message before loading the
test set or making any API calls.

## Running

Start with a smoke test on a couple of samples, for example one normal
sample and one `unusable_input` sample (which should be rejected):

```bash
.venv/bin/python eval/run_eval.py --samples sample_001,sample_031
```

Then run the full test set:

```bash
.venv/bin/python eval/run_eval.py
```

Samples run one at a time, and the runner prints each sample's outcome and
cost as it goes. At Claude Haiku 4.5's rates, a two-sample smoke test costs
about half a cent and a full run about $0.15. These are estimates, and each
run records its actual cost.

A sample that fails (API error, truncated output, refusal, invalid output,
or an unexpected error) is recorded as an error and the run continues.

Each sample's result is saved as soon as it finishes. If you stop a run
with Ctrl+C, the runner writes all the output files for the samples that
finished and marks the run interrupted. A run killed outright (for example,
by closing the terminal) keeps `run.json` and the finished samples in
`results.json`, and `run.json` still marks it interrupted.

## Output

Each run writes to its own folder, where the run ID is the local start time
(for example `2026-10-01_141502`):

- Full runs: `eval/runs/<run_id>/`
- Partial runs (`--samples`): `eval/runs/partial/<run_id>/`. This folder is
  excluded by `.gitignore`, so smoke tests are never committed.

Each folder contains:

- `run.json`: Run metadata (date, rubric version, test set version and
  hash, source text hash, model, prompt version and hash, max tokens,
  request timeout, max retries, gate approach, SDK version, partial,
  interrupted, and incomplete flags, test set size), the
  list of errored samples, and every automated metric, overall and per
  category. The prompt hash covers the system prompt, the text wrapped
  around the notes, and the output schema.
- `results.json`: One record per sample: outcome, the model's raw output, the
  parsed output, token counts and cost, any error, the card count, and the
  source check for each card and excerpt. Rewritten after every sample.
- `summary.md`: The run status, errored samples, and metrics as readable
  tables, overall, per category, and per sample
- `scoring_sheet.md`: Read-only reference for hand scoring: each correctly
  accepted sample's source text, followed by its cards and their source
  excerpts, each marked ✓ or ✗ by the automated source check
- `scores.csv`: One row per card, with its question and answer and blank
  columns for the hand-scored criteria

### Hand scoring

The automated metrics cover the input gate, card counts, source matching,
cost, latency, and errors. The judgment-based criteria are scored by hand
in `scores.csv`, reading `scoring_sheet.md` alongside it:

- `atomic`, `supported`, `no_leakage`, `unambiguous`: `Y` or `N`
- `duplicate_of`: the ID of the earlier card this one duplicates, or blank
- `notes`: optional

The definitions and examples for each criterion are in
[`rubric.md`](rubric.md). `scores.csv` is written with a UTF-8 byte order
mark so Excel displays non-ASCII characters correctly.

## Scoring a run

`score_run.py` validates a run's hand scores, computes the hand-scored
metrics, and records the run in `results_log.md`. It uses only the standard
library and makes no API calls.

```bash
.venv/bin/python eval/score_run.py eval/runs/2026-10-02_215109/rescored/rubric-1.5_test-set-2
```

It reads only `card_id`, the four criteria, and `duplicate_of` from
`scores.csv`. Excel auto-converts some values in the `question` and
`answer` columns (dates, for example), so card text always comes from
`results.json`. Saving from Excel as "CSV UTF-8" is fine; the byte order
mark, stray spaces around values, and blank trailing rows are all handled.

**Validation.** Before computing anything, the script checks the following
and, if anything fails, lists every problem and writes nothing:

- The run is valid: not partial, interrupted, or incomplete (see
  [Run validity](#run-validity)), with no errored or missing samples in
  `results.json`.
- The run's rubric and test set versions match the current `rubric.md`
  and test set. A run's automated metrics were computed under its own
  versions, so scores under different versions can't be combined with
  them. To score an older run under the current versions,
  [recompute](#recomputing-a-run) it first and score the recomputed
  folder. A run without a recorded test set version counts as version 1.
- Every card scored in Stage 2 has exactly one row in the scores file,
  and every row is a card scored in Stage 2.
- Each of the four criteria is exactly `Y` or `N`.
- Each `duplicate_of` is an earlier card in the same sample.

**Output.** The metrics are written to `hand_scores.json` in the run folder:
the rubric and test set versions, the scores file used, the clean card
rate, the atomic, supported, no-leakage, unambiguous, and duplicate-free
rates, and the automated metrics copied from `run.json`, all overall and
per category. Per-card rates are pooled across all scored
cards, and duplicates don't count against the clean card rate, as defined
in [`rubric.md`](rubric.md).

### Scorers

`--scorer` names who scored the run, and defaults to `hand`. An LLM judge's
label **must** include the judge's model and judge prompt version, for
example `judge:sonnet-5:v1`. The scorer label identifies the run's row in
the results log, so an unversioned label would let a new judge prompt
silently replace the old one's results. The output file is named after
the scorer (`judge_sonnet-5_v1_scores.json`, with colons replaced since
Windows doesn't allow them in file names).

### Scores file

By default the script reads `scores.csv` in the run folder. `--scores`
reads a different file instead, and its name is recorded in the output as
`scores_file`:

```bash
.venv/bin/python eval/score_run.py --scores path/to/scores.csv <run_folder>
```

### Logging a run without scores

To record a valid run's automated metrics without hand scores, for example
to track run-to-run variation:

```bash
.venv/bin/python eval/score_run.py --automated-only eval/runs/2026-10-02_215610/rescored/rubric-1.5_test-set-2
```

No scores file is read or written. The run's row shows the scored columns
as `not scored`.

## Results log

`results_log.md` opens with the shipping criteria: the results a prompt or
model change must reach before it ships, set before the runs that will be
judged against them. Below them is one row per valid run, rubric and test
set version, and scorer: run ID, date, model, prompt version and hash,
rubric and test set versions, scorer, each scored rate, the Stage 1 gate
rates, card count pass rate, source match rate, and average cost. Each
run's full metrics, including per-category results, stay in its folder.

The table is written by `score_run.py`, so don't edit its rows by hand.
Text above the table, including the shipping criteria, is left as it is.
Rerunning the script updates rows rather than adding duplicates:

- A row is identified by its run ID, rubric version, test set version, and
  scorer. Recomputing and rescoring a run under new versions adds rows, so
  the run's earlier results stay visible.
- Scoring a run again under the same versions with the same scorer
  replaces that row.
- Scoring a run replaces its `not scored` row for the same versions, if it
  has one.
- A run can have rows from several scorers, for example `hand` and a judge,
  so their scores can be compared.
- `--automated-only` is refused for a run that already has a scored row
  for the same versions, since that row already includes the automated
  metrics.

## Recomputing a run

When the rubric or test set version changes, an existing run's automated
metrics can be recomputed under the new versions without calling the API:

```bash
.venv/bin/python eval/recompute_run.py eval/runs/2026-10-02_215109
```

The run's original files are never modified. The recomputed run is
written to its own folder inside the run folder,
`rescored/rubric-<version>_test-set-<version>/`, with `results.json`,
`run.json`, `summary.md`, and `scoring_sheet.md`. The original results,
and any scores made under the earlier versions, stay where they are.

- The model's recorded outputs (outcome, raw and parsed output, token
  counts and cost, errors, and each card's ID, question, answer, and
  source) are copied unchanged. The script stops without writing anything
  if any of them would differ.
- The fields derived from them and from the test set's labels are
  recomputed with the runner's own code: the expected outcome and card
  range, Stage 1 correctness, which samples are scored in Stage 2, the
  card count check, and the source check.
- `run.json` records the new rubric and test set versions and hashes, and
  `recomputed_from` gives the versions the run was originally made under.
- Recomputing is only valid if the run's notes haven't changed, which is
  why `source_text` is never edited. Each run records a `source_text_hash`
  of its samples' IDs and notes, and the script refuses to recompute a run
  whose hash no longer matches. Runs made before the hash existed can't be
  checked this way, and the script prints a note saying so.
- If the current test set has samples the run didn't cover, the
  recomputed run is marked partial.

The script imports the runner's code, so it has the same startup delay
(see [Setup](#setup)), but it never calls the API.

Rerunning it rewrites those four files, but never a scores file, so scores
saved in the recomputed folder are kept. The hand-scored criteria aren't
recomputed. Rescore them under the new rubric, by hand or with a validated
judge, save the scores as `scores.csv` in the recomputed folder (a copy of
the earlier `scores.csv` is a good starting point), and run
`score_run.py` on that folder.

## LLM judge

`run_judge.py` scores the judgment-based criteria (atomic, supported, no
leakage, unambiguous, and near-duplicates) with Claude Opus 5.5, so a run
doesn't need full hand scoring. The input gate, card count, and source
check are already computed by code, so the judge doesn't score them. Until
the judge is [validated](#validating-the-judge), its scores don't count
toward the shipping criteria.

- **One call per sample,** with the sample's notes and all of its cards,
  since duplicates can only be judged across the whole batch.
- **Blind:** the judge never sees the hand scores or their notes, the
  automated source check, or the cards' source excerpts. Cards are
  renumbered `c01`, `c02`, ... so sample and seed IDs don't reach it either.
- **Settings:** effort `low` (Opus 5.5 always thinks, so effort is the only
  control), the system prompt cached after the first call, a summary of the
  judge's thinking saved with each result, and no fallback model: a refusal
  is recorded as an errored sample. The model is different from both
  candidate generators, so a generator is never graded by its own model.
- **Versioned:** the instructions are in `judge/judge_prompt_v1.txt`. The
  rubric's criteria, from "Per-card criteria" up to "Card Count", are
  loaded from `rubric.md` at run time, so they can't drift from the
  rubric. Each judge run records a judge hash covering the prompt, the
  loaded criteria, the output format, the model, and the effort level.

### Running the judge

The judge needs `ANTHROPIC_API_KEY`, found the same way as for the
[runner](#api-key). It only judges a valid run made or recomputed under
the current rubric and test set versions. Smoke test it on a couple of
samples first:

```bash
.venv/bin/python eval/run_judge.py --samples sample_001,sample_018 eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
```

Then judge the whole run, and, for validation, the seeded examples:

```bash
.venv/bin/python eval/run_judge.py eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
.venv/bin/python eval/run_judge.py --seeded eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
```

At Opus 5.5's rates, a full judge run of Run 1 is estimated at $0.40 to
$1.20 and a seeded run at $0.35 to $1.00, mostly depending on how much the
judge thinks. Each judge run records its actual cost.

Each judge run writes its own folder. Judge runs of a run go inside that
run's folder, in `judge/<judge_run_id>/`; seeded runs go in
`judge/seeded_runs/<judge_run_id>/`. A `--samples` or `--seeds` run is
partial and goes in a `partial/` folder, which is excluded by `.gitignore`.
Each folder contains:

- `judge_run.json`: Settings (judge model, prompt version, judge hash,
  effort, token limit), the run judged, the partial, interrupted, and
  incomplete flags, errored samples, and cost and latency
- `judge_results.json`: One record per sample: the grades and reasons, the
  raw output, the thinking summary, tokens, cost, any error or warning,
  and how many attempts it took, with any retried attempt's error, output,
  and cost
- `judge_summary.md`: The grades and reasons as readable tables
- `judge_scores.csv`: Only for a complete judge run of every card. The same
  format as `scores.csv`, with the judge's reasons in `notes`

A response that doesn't match the batch, such as a grade list that stops
before the last card, is retried once. If the retry fails too, the sample
errors and the judge run is incomplete. API errors (already retried by the
SDK), truncated responses, and refusals aren't retried. Each judge run
records its total API calls and retries, and its cost includes every
attempt. The retry belongs to the runner, not the judge, so the judge hash
doesn't cover it.

The judge never writes `scores.csv`. To record a judge run in the results
log, once the judge is validated:

```bash
.venv/bin/python eval/score_run.py --scorer judge:opus-5.5:v1 \
    --scores eval/runs/<run>/judge/<judge_run_id>/judge_scores.csv eval/runs/<run>
```

### Seeded examples

Run 1 has too few real failures to test some criteria (2 for supported, 4
duplicates), so `judge/seeded_examples.json` holds 26 cards, each a Run 1
card changed to have exactly one known defect, or none for a control. Each
seed lists its criterion, how subtle the defect is, the card it replaces
or is inserted after, and its expected labels. A seeded judge run puts one
seed into a copy of its sample's batch per call, and only the seed's own
card is compared. Seeds are kept apart from the test set, and none appear
in the judge prompt.

### Validating the judge

A judge counts as **validated** only if, in each of two judge runs on Run 1
(`2026-10-02_215109`, rubric 1.6, test set 2), compared with the hand
scores in `rescored/rubric-1.6_test-set-2/scores.csv`, all of the following
hold:

- Unambiguous: catches at least 10 of the 12 hand-scored failures
- Atomic: catches at least 9 of 11
- No leakage: catches at least 5 of 6
- Every criterion, including duplicates: false alarm rate at most 5%
- Clean card rate within ±3 points of the hand-scored 86.0%
- Seeded examples, in each of two seeded judge runs: correct on at least 4
  of 5 per criterion, and at least 5 of 6 for duplicates

Supported and duplicates have no catch threshold because Run 1 has too few
real failures (2 and 4); they rely on the seeded examples and the false
alarm rate. The duplicate seeds went from 5 to 6, with the threshold raised
from 4 of 5 to 5 of 6, on 2026-10-12, before the judge produced any output.
A judge stays validated only while its judge hash is unchanged. Changing
the prompt, the rubric criteria it loads, the model, or the effort level
means validating again.

If a hand score is corrected (see below), each catch threshold keeps the
same number of allowed misses (2 for unambiguous, 2 for atomic, 1 for no
leakage), and the clean card rate is compared with the corrected hand
rate.

```bash
.venv/bin/python eval/validate_judge.py \
    --runs <judge_run_A> <judge_run_B> --seeded <seeded_run_A> <seeded_run_B>
```

Add `--discarded <judge_run>...` for any incomplete or interrupted judge run
of the same judge that was set aside, so its API calls, dropped outputs,
and cost are still counted. A discarded run is never graded or compared.

The report is written to `judge/validation/judge_opus-5.5_v1.md`. It
shows each threshold for both runs; catch and false alarm rates per
criterion, with the counts behind them; the judge's clean card rate against
the hand score's; every seed and whether the judge caught it;
self-consistency between the two runs; retries, the drop rate (responses
that didn't match the batch, as a share of API calls), and the total spent,
all including discarded runs; and every card where the judge and the hand
scores differ, with the judge's reason and the hand-scoring note side by
side. Like `score_run.py`, it uses only the standard library and
makes no API calls.

### Correcting hand scores

Reviewing disagreements may show that a hand score was wrong. No script
ever changes hand scores. A person changes one in the run's `scores.csv`
only when the judge's reason points to a specific rubric rule that was
misapplied, and records every change in `score_changes.csv` beside it: the
date, card ID, field, old and new value, what prompted it (a judge run ID,
or `pre-judge` for a change made before any judge output), the rubric rule,
and the reason.

Correcting only the cards the judge disagrees with moves the hand scores
toward the judge, so the report compares the judge with both the original
scores (every judge-prompted change reverted) and the corrected ones. The
verdict is decided on the corrected scores, and if the two verdicts differ,
the report says so at the top. Changes marked `pre-judge` are part of both.

### Tests

The judge's tests run offline with a stubbed client, so they make no API
calls. They judge a copy of Run 1 in a temporary folder:

```bash
.venv/bin/python -m unittest discover -s eval/tests -v
```

## Run validity

Three flags in `run.json`, also shown at the top of `summary.md`, say
whether a run can be used as a baseline or comparison point. They're
independent, so a run can have any combination of them. Only a run with
none of them set is valid for comparison.

**Partial:** the run used `--samples` to run a subset of the test set, for
smoke testing. Its rates cover only the selected samples and aren't
comparable with those of full runs.

**Interrupted:** the run stopped before every selected sample ran. Its
rates cover only the samples that finished. The flag is set when the run
starts and cleared only after every sample has run and all output is
written, so a run killed without warning is still marked.

**Incomplete:** at least one sample errored. Errored samples are excluded
from every Stage 1 and Stage 2 rate, which can make results look better
than they are. They're reported as an error rate, overall and per
category, instead. An incomplete run must not be used as a baseline or
comparison point until the errored samples are resolved and rerun.

See the "Errored Samples and Run Validity" section of
[`rubric.md`](rubric.md) for the full definitions.

## Committing runs

Commit a run folder only if none of the three flags is set: not partial,
not interrupted, and not incomplete. Delete any other run, or fix the cause
and rerun it. Partial runs are already excluded by `.gitignore`, but
interrupted and incomplete runs are written to `eval/runs/` alongside valid
ones, so check `run.json` or the top of `summary.md` before committing.

Commit a run's `rescored/` folders along with it, so each row in
`results_log.md` can be traced back to its files.
