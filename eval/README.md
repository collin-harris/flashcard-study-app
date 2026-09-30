# Evaluation

Tooling for measuring the quality of AI-generated flashcards. The runner
(`run_eval.py`) sends every sample in the test set through the same
`generate_cards()` function the API will use
(`backend/app/services/card_generation.py`), so what gets measured is what
gets shipped. It computes the automated metrics defined in
[`rubric.md`](rubric.md) and produces a sheet for hand-scoring the rest.

- `rubric.md`: How generated cards are scored, and the definition of every
  metric
- `test_set/test_set.json`: The 35 fixed test samples, with category tags and
  expected card ranges
- `run_eval.py`: The evaluation runner
- `requirements.txt`: The runner's dependencies: `backend/requirements.txt`
  plus `python-dotenv`
- `runs/`: One folder per run, created by the runner

All commands below are run from the repository root.

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

## Output

Each run writes to its own folder, `eval/runs/<run_id>/`, where the run ID
is the local start time (for example `2026-10-01_141502`).

- `run.json`: Run metadata (date, rubric version, model, prompt version and
  hash, temperature, max tokens, gate approach, SDK version, partial and
  incomplete flags, test set size), the list of errored samples, and every
  automated metric, overall and per category
- `results.json`: One record per sample: outcome, the model's raw output, the
  parsed output, token counts and cost, any error, the card count, and the
  source check for each card and excerpt
- `summary.md`: The run status, errored samples, and metrics as readable
  tables, overall, per category, and per sample
- `scoring_sheet.md`: Read-only reference for hand scoring: each correctly
  accepted sample's source text, followed by its cards and their source
  excerpts, each marked ✓ or ✗ by the automated source check
- `scores.csv`: One row per card, with blank columns for the hand-scored
  criteria

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

Computing the clean card rate and the other hand-scored rates from
`scores.csv`, and recording results in `eval/results_log.md`, is not
automated yet.

## Run validity

Two flags in `run.json`, also shown at the top of `summary.md`, say whether
a run can be used as a baseline or comparison point. They're independent,
so a run can be partial, incomplete, both, or neither. Only a run that is
neither is valid for comparison.

**Partial:** the run used `--samples` to run a subset of the test set, for
smoke testing. Its rates cover only the selected samples and aren't
comparable with those of full runs.

**Incomplete:** at least one sample errored. Errored samples are excluded
from every Stage 1 and Stage 2 rate, which can make results look better
than they are. They're reported as an error rate, overall and per
category, instead. An incomplete run must not be used as a baseline or
comparison point until the errored samples are resolved and rerun.

See the "Errored Samples and Run Validity" section of
[`rubric.md`](rubric.md) for the full definitions.
