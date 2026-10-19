#!/usr/bin/env python3
"""Turns a run's scores into final metrics and records them in the results log.

Reads the scored criteria from the run's scores.csv (or the file given with
--scores), validates them against
results.json, computes the hand-scored metrics defined in eval/rubric.md
(overall and per category), and writes them to <scorer>_scores.json in the
run folder alongside the automated metrics from run.json. Then adds or
updates the run's row in eval/results_log.md.

With --automated-only, scores.csv is not read: the run's automated metrics
are logged with the scored columns marked "not scored".

Only valid runs (not partial, interrupted, or incomplete) are accepted, and a
scored run must have been made or recomputed under the current rubric and
test set versions. Uses only the standard library and makes no API calls. See
eval/README.md.

Usage:
    .venv/bin/python eval/score_run.py eval/runs/2026-10-02_215109/rescored/rubric-1.5_test-set-2
    .venv/bin/python eval/score_run.py --automated-only eval/runs/2026-10-02_215610/rescored/rubric-1.5_test-set-2
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "eval"
RUBRIC_PATH = EVAL_DIR / "rubric.md"
README_PATH = EVAL_DIR / "README.md"
RESULTS_LOG_PATH = EVAL_DIR / "results_log.md"

CRITERIA = ["atomic", "supported", "no_leakage", "unambiguous"]
# Only these columns are read. Excel auto-converts some values in the
# question and answer columns (dates, for example), so card text always comes
# from results.json instead.
REQUIRED_COLUMNS = ["card_id", *CRITERIA, "duplicate_of"]

# In the order they appear in the log and the printed summary.
SCORED_METRICS = [
    ("clean_card_rate", "Clean card rate"),
    ("atomic_rate", "Atomic rate"),
    ("supported_rate", "Supported rate"),
    ("no_leakage_rate", "No-leakage rate"),
    ("unambiguous_rate", "Unambiguous rate"),
    ("duplicate_free_rate", "Duplicate-free rate"),
]

DEFAULT_SCORER = "hand"
NOT_SCORED = "not scored"
# How score_changes.csv marks a hand score change made before any judge
# output. Any other change means scores.csv is no longer the original scoring.
PRE_JUDGE = "pre-judge"
# Runs made before the test set was versioned used version 1.
UNVERSIONED_TEST_SET = "1"

LOG_COLUMNS = [
    "Run ID", "Date", "Model", "Prompt", "Prompt hash", "Rubric", "Test set", "Scorer",
    "Clean card", "Atomic", "Supported", "No leakage", "Unambiguous", "Duplicate-free",
    "False rejection", "False acceptance", "Card count pass", "Source match", "Avg cost",
]
# A row is identified by its run, the versions it was scored under, and its
# scorer, so rescoring a run under a new rubric or test set adds rows rather
# than replacing the old ones.
RUN_COLUMNS = [LOG_COLUMNS.index(c) for c in ("Run ID", "Rubric", "Test set")]
SCORER_COLUMN = LOG_COLUMNS.index("Scorer")

LOG_INTRO = """# Evaluation Results Log

One row per valid evaluation run, rubric and test set version, and scorer,
written by `eval/score_run.py`.
Only runs that are not partial, interrupted, or incomplete appear here. The
definition of every metric is in [`rubric.md`](rubric.md), and each run's
full metrics, overall and per category, are in its folder in `runs/`.

- **Scorer:** who scored the judgment-based criteria. `hand` is a person;
  an LLM judge's label names its model and judge prompt version. A run can
  have one row per scorer. `not scored` means only the automated metrics
  were logged.
- **Rates** are shown as a percentage with the count behind it, for example
  `97.3% (181/186)`.
- **Rubric** and **Test set** are the versions the run was scored under.
  Rows scored under different versions are not directly comparable. A run
  recomputed under new versions gets new rows, and its earlier rows are
  kept.

The table is rewritten by the script, so don't edit its rows by hand.
Rerunning the script on a run updates that run's row for the same versions
and scorer.
"""


# ---------------------------------------------------------------------------
# Shared helpers (same output shape as run_eval.py, which isn't imported
# because it loads the Anthropic SDK and the backend)
# ---------------------------------------------------------------------------

def rate(count: int, total: int) -> dict:
    return {"count": count, "total": total, "rate": count / total if total else None}


def format_rate(r: dict) -> str:
    if r["rate"] is None:
        return "n/a (0/0)"
    return f"{r['rate']:.1%} ({r['count']}/{r['total']})"


def write_json(path: Path, data) -> None:
    # Written to a temporary file and then renamed over the target, so an
    # interruption mid-write leaves the previous version intact.
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def load_json(path: Path):
    if not path.exists():
        sys.exit(f"Missing {path}.")
    return json.loads(path.read_text(encoding="utf-8"))


def read_version(path: Path, label: str) -> str:
    match = re.search(rf"^\*\*{label}:\*\*\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        sys.exit(f"Could not find a '**{label}:**' line in {path}.")
    return match.group(1)


def version_key(version: str) -> tuple:
    # Sorts 1.10 after 1.9.
    return tuple(int(part) for part in version.split("."))


def scores_filename(scorer: str) -> str:
    # Colons (as in judge:sonnet-5:v1) aren't allowed in Windows file names.
    return re.sub(r"[^A-Za-z0-9._-]", "_", scorer) + "_scores.json"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def check_run_validity(run_info: dict, records: list[dict]) -> list[str]:
    problems = []
    # A run killed outright can leave incomplete as null, so anything other
    # than an explicit false counts as set.
    for flag in ("partial", "interrupted", "incomplete"):
        if run_info.get(flag) is not False:
            problems.append(
                f"run.json marks the run {flag} ({flag}: {json.dumps(run_info.get(flag))}). "
                "Partial, interrupted, and incomplete runs aren't valid as a baseline or comparison point."
            )

    # A cross-check on the flags, from the per-sample records themselves.
    finished = {r["id"] for r in records}
    missing = [s for s in run_info.get("sample_ids", []) if s not in finished]
    if missing:
        problems.append(f"results.json has no record for {len(missing)} selected sample(s): {', '.join(missing)}.")
    errored = [r["id"] for r in records if r["outcome"] == "error"]
    if errored:
        problems.append(f"{len(errored)} sample(s) errored in results.json: {', '.join(errored)}.")
    return problems


def check_original_scores(run_dir: Path) -> list[str]:
    """Problems with scoring the run as plain 'hand': its scores.csv may hold corrections made after judge output."""
    path = run_dir / "score_changes.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        corrected = [row for row in csv.DictReader(f) if (row.get("prompted_by") or "").strip() != PRE_JUDGE]
    if not corrected:
        return []
    # A change both judge runs prompted lists their IDs joined with " + ".
    prompted_by = sorted({p.strip() for row in corrected for p in row["prompted_by"].split("+")})
    return [
        f"{path.name} lists {len(corrected)} score change(s) made after judge output "
        f"(prompted by {', '.join(prompted_by)}), so scores.csv no longer holds the original hand scores. "
        f"Scoring it as '{DEFAULT_SCORER}' would replace the original row in results_log.md. "
        f"Score the corrected file with --scorer {DEFAULT_SCORER}:corrected:<judge> instead, "
        "for example hand:corrected:judge-v1."
    ]


def describe(card_id: str, cards: dict) -> str:
    # The question comes from results.json, so the card is easy to find in
    # the spreadsheet even though the CSV's question column isn't read.
    question = cards[card_id]["question"]
    if len(question) > 70:
        question = question[:67] + "..."
    return f'{card_id} ("{question}")'


def read_scores(path: Path, cards: dict) -> tuple[dict, list[str]]:
    """Reads and validates scores.csv against the Stage 2 cards in results.json.

    Returns the parsed scores keyed by card ID, and a list of every problem
    found. The scores are only usable if the list is empty.
    """
    if not path.exists():
        return {}, [f"Missing {path}."]

    # utf-8-sig drops the byte order mark that Excel's "CSV UTF-8" adds.
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing_columns = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing_columns:
            return {}, [f"{path.name} is missing column(s): {', '.join(missing_columns)}."]
        rows = list(reader)

    problems = []
    scores = {}
    for row_number, row in enumerate(rows, start=2):  # matches Excel's row numbers; row 1 is the header
        values = {c: (row.get(c) or "").strip() for c in REQUIRED_COLUMNS}
        # Excel sometimes saves trailing rows with every cell empty.
        if not any((v or "").strip() for k, v in row.items() if k is not None):
            continue

        card_id = values["card_id"]
        if not card_id:
            problems.append(f"Row {row_number}: card_id is blank.")
            continue
        if card_id not in cards:
            problems.append(f"Row {row_number}: {card_id} is not a card scored in Stage 2 in results.json.")
            continue
        if card_id in scores:
            problems.append(f"Row {row_number}: {card_id} already has a row (row {scores[card_id]['row']}).")
            continue

        label = describe(card_id, cards)
        for criterion in CRITERIA:
            value = values[criterion]
            if not value:
                problems.append(f"{label}: {criterion} is blank.")
            elif value not in ("Y", "N"):
                problems.append(f"{label}: {criterion} is '{value}', expected Y or N.")

        duplicate_of = values["duplicate_of"]
        if duplicate_of:
            card, original = cards[card_id], cards.get(duplicate_of)
            if original is None:
                problems.append(f"{label}: duplicate_of '{duplicate_of}' is not a card scored in Stage 2.")
            elif original["sample_id"] != card["sample_id"]:
                problems.append(f"{label}: duplicate_of '{duplicate_of}' is in a different sample.")
            elif original["index"] >= card["index"]:
                problems.append(f"{label}: duplicate_of '{duplicate_of}' is not an earlier card in the batch.")

        scores[card_id] = {
            "row": row_number,
            **{criterion: values[criterion] == "Y" for criterion in CRITERIA},
            "duplicate_of": duplicate_of or None,
        }

    for card_id in cards:
        if card_id not in scores:
            problems.append(f"{describe(card_id, cards)} has no row in {path.name}.")
    return scores, problems


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_scored_metrics(card_scores: list[dict]) -> dict:
    total = len(card_scores)
    return {
        "cards_scored": total,
        # Duplicates don't count against the clean card rate; they have their
        # own duplicate-free rate (rubric, "Metrics").
        "clean_card_rate": rate(sum(all(s[c] for c in CRITERIA) for s in card_scores), total),
        "atomic_rate": rate(sum(s["atomic"] for s in card_scores), total),
        "supported_rate": rate(sum(s["supported"] for s in card_scores), total),
        "no_leakage_rate": rate(sum(s["no_leakage"] for s in card_scores), total),
        "unambiguous_rate": rate(sum(s["unambiguous"] for s in card_scores), total),
        "duplicate_free_rate": rate(sum(s["duplicate_of"] is None for s in card_scores), total),
    }


def relative_to_run(path: Path, run_dir: Path) -> str:
    # Relative to the run folder, so scores files in different subfolders
    # (judge/<id>/, split/<id>/) can be told apart. A file outside the run
    # folder keeps the path it was given.
    try:
        return path.resolve().relative_to(run_dir.resolve()).as_posix()
    except ValueError:
        return str(path)


def build_scores_record(run_info: dict, scorer: str, scores_path: Path, run_dir: Path, records: list[dict],
                        scores: dict) -> dict:
    # Per-card rates are pooled across every card in the scored batches. A
    # sample counts toward every tag it carries, as in run_eval.py.
    by_tag = defaultdict(list)
    for r in records:
        for tag in r["tags"]:
            by_tag[tag].extend(scores[card["card_id"]] for card in r["cards"] if r["scored_in_stage2"])

    return {
        "run_id": run_info["run_id"],
        "date": run_info["date"],
        "model": run_info["model"],
        "prompt_version": run_info["prompt_version"],
        "prompt_hash": run_info["prompt_hash"],
        "rubric_version": run_info["rubric_version"],
        "test_set_version": run_info.get("test_set_version", UNVERSIONED_TEST_SET),
        "test_set_hash": run_info.get("test_set_hash"),
        "scorer": scorer,
        "scores_file": relative_to_run(scores_path, run_dir),
        "metrics": {
            "scored": compute_scored_metrics(list(scores.values())),
            "automated": run_info["metrics"],
        },
        "metrics_by_category": {
            tag: {
                "scored": compute_scored_metrics(by_tag[tag]),
                "automated": run_info["metrics_by_category"].get(tag),
            }
            for tag in sorted(by_tag)
        },
    }


# ---------------------------------------------------------------------------
# Results log
# ---------------------------------------------------------------------------

def format_log_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def build_log_row(run_info: dict, scorer: str, scored: dict | None) -> list[str]:
    m = run_info["metrics"]
    if scored is None:
        scored_cells = [NOT_SCORED] * len(SCORED_METRICS)
    else:
        scored_cells = [format_rate(scored[key]) for key, _ in SCORED_METRICS]
    return [
        run_info["run_id"],
        run_info["date"][:10],
        run_info["model"],
        run_info["prompt_version"],
        run_info["prompt_hash"],
        run_info["rubric_version"],
        run_info.get("test_set_version", UNVERSIONED_TEST_SET),
        scorer,
        *scored_cells,
        format_rate(m["stage1"]["false_rejection_rate"]),
        format_rate(m["stage1"]["false_acceptance_rate"]),
        format_rate(m["stage2"]["card_count_pass_rate"]),
        format_rate(m["stage2"]["source_match_rate"]),
        f"${m['operational']['average_cost_usd']:.4f}",
    ]


def read_log(path: Path) -> tuple[list[str], list[list[str]], list[str]]:
    """Splits the log into the lines before the table, its rows, and the lines after."""
    if not path.exists():
        return LOG_INTRO.splitlines() + [""], [], []

    lines = path.read_text(encoding="utf-8").splitlines()
    header = format_log_row(LOG_COLUMNS)
    if header not in lines:
        # Most likely the columns changed. Stop rather than rewrite a table
        # this version of the script doesn't understand.
        sys.exit(f"Could not find the expected table header in {path}. Expected:\n{header}")
    start = lines.index(header)

    rows = []
    end = start + 2  # skips the header and its separator row
    while end < len(lines) and lines[end].startswith("|"):
        cells = [cell.strip() for cell in lines[end].strip().strip("|").split("|")]
        if len(cells) != len(LOG_COLUMNS):
            sys.exit(f"{path} line {end + 1} has {len(cells)} cells, expected {len(LOG_COLUMNS)}:\n{lines[end]}")
        rows.append(cells)
        end += 1
    return lines[:start], rows, lines[end:]


def run_key(row: list[str]) -> tuple:
    return tuple(row[i] for i in RUN_COLUMNS)


def upsert_log_row(rows: list[list[str]], new_row: list[str]) -> tuple[list[list[str]], str]:
    run_id, rubric, test_set = run_key(new_row)
    scorer = new_row[SCORER_COLUMN]
    same_run = [r for r in rows if run_key(r) == run_key(new_row)]

    if scorer == NOT_SCORED:
        scored_by = [r[SCORER_COLUMN] for r in same_run if r[SCORER_COLUMN] != NOT_SCORED]
        if scored_by:
            sys.exit(
                f"Run {run_id} already has a scored row under rubric {rubric} and test set {test_set} "
                f"(scorer: {', '.join(scored_by)}), which includes its automated metrics. "
                "Not adding a 'not scored' row."
            )
        replaced = same_run
    else:
        # A scored row replaces this scorer's previous row, and the run's
        # 'not scored' row if it had one. Other scorers' rows are kept.
        replaced = [r for r in same_run if r[SCORER_COLUMN] in (scorer, NOT_SCORED)]

    kept = [r for r in rows if r not in replaced]
    # Run IDs are start times, so this is chronological, with each run's
    # rows in version order.
    updated = sorted(kept + [new_row], key=lambda r: (
        r[RUN_COLUMNS[0]], version_key(r[RUN_COLUMNS[1]]), version_key(r[RUN_COLUMNS[2]]), r[SCORER_COLUMN],
    ))
    action = f"Replaced the '{replaced[0][SCORER_COLUMN]}' row" if replaced else "Added a row"
    return updated, action


def write_log(path: Path, before: list[str], rows: list[list[str]], after: list[str]) -> None:
    table = [
        format_log_row(LOG_COLUMNS),
        format_log_row(["---"] * len(LOG_COLUMNS)),
        *(format_log_row(r) for r in rows),
    ]
    path.write_text("\n".join(before + table + after).rstrip("\n") + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Compute a run's scored metrics and record them in the results log.")
    parser.add_argument("run_dir", help="the run folder, e.g. eval/runs/2026-10-02_215109")
    parser.add_argument(
        "--scorer",
        help=f"who scored the run (default: {DEFAULT_SCORER}). An LLM judge's label must name its model "
        "and judge prompt version, e.g. judge:sonnet-5:v1",
    )
    parser.add_argument("--scores", help="the scores CSV (default: scores.csv in the run folder)")
    parser.add_argument(
        "--automated-only", action="store_true",
        help="log the run's automated metrics without reading any scores",
    )
    args = parser.parse_args()

    if args.automated_only and (args.scorer or args.scores):
        parser.error("--scorer and --scores don't apply with --automated-only; nothing is scored")
    scorer = NOT_SCORED if args.automated_only else (args.scorer or DEFAULT_SCORER).strip()
    if not args.automated_only and (not scorer or "|" in scorer or scorer == NOT_SCORED):
        parser.error(f"--scorer must be non-empty, can't contain '|', and can't be '{NOT_SCORED}'")

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        sys.exit(f"{run_dir} is not a folder.")
    run_info = load_json(run_dir / "run.json")
    records = load_json(run_dir / "results.json")

    problems = check_run_validity(run_info, records)
    scores = None
    if not args.automated_only:
        # The automated metrics in run.json were computed under the run's
        # rubric and test set versions, so scores under different versions
        # can't be mixed in with them. recompute_run.py brings a run's
        # automated metrics up to the current versions.
        rubric_version = read_version(RUBRIC_PATH, "Rubric Version")
        if run_info.get("rubric_version") != rubric_version:
            problems.append(
                f"The run was made under rubric {run_info.get('rubric_version')}, but rubric.md is now "
                f"{rubric_version}. Recompute it with recompute_run.py and score the recomputed run."
            )
        test_set_version = read_version(README_PATH, "Test Set Version")
        run_test_set = run_info.get("test_set_version", UNVERSIONED_TEST_SET)
        if run_test_set != test_set_version:
            problems.append(
                f"The run was made under test set {run_test_set}, but the test set is now "
                f"{test_set_version}. Recompute it with recompute_run.py and score the recomputed run."
            )
        cards = {
            card["card_id"]: {"sample_id": r["id"], "index": index, "question": card["question"]}
            for r in records if r["scored_in_stage2"]
            for index, card in enumerate(r["cards"])
        }
        scores_path = Path(args.scores) if args.scores else run_dir / "scores.csv"
        scores, score_problems = read_scores(scores_path, cards)
        problems += score_problems
        if scorer == DEFAULT_SCORER:
            problems += check_original_scores(run_dir)

    if problems:
        sys.exit(f"Validation failed with {len(problems)} problem(s). Nothing was written.\n\n"
                 + "\n".join(f"- {p}" for p in problems))

    # Read the log before writing anything, so a log this script can't parse
    # doesn't leave the scores file updated and the log not.
    before, rows, after = read_log(RESULTS_LOG_PATH)

    scored_metrics = None
    if scores is not None:
        record = build_scores_record(run_info, scorer, scores_path, run_dir, records, scores)
        scored_metrics = record["metrics"]["scored"]

    rows, action = upsert_log_row(rows, build_log_row(run_info, scorer, scored_metrics))

    if scores is not None:
        output_path = run_dir / scores_filename(scorer)
        write_json(output_path, record)
        print(
            f"Run {run_info['run_id']} under rubric {run_info['rubric_version']} and test set "
            f"{run_info.get('test_set_version', UNVERSIONED_TEST_SET)}, scored by {scorer} "
            f"from {scores_path.name}: {scored_metrics['cards_scored']} cards"
        )
        for key, label in SCORED_METRICS:
            print(f"  {label}: {format_rate(scored_metrics[key])}")
        print(f"Wrote {output_path}")
    write_log(RESULTS_LOG_PATH, before, rows, after)
    print(f"{action} for run {run_info['run_id']} in {RESULTS_LOG_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
