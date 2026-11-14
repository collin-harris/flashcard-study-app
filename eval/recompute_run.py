#!/usr/bin/env python3
"""Recomputes a run's automated metrics under the current test set and rubric.

Makes no API calls. Reads the run's original results.json and run.json, which
are never modified, and writes the recomputed run to its own folder:
<run_dir>/rescored/rubric-<version>_test-set-<version>/. The model's recorded
outputs are copied unchanged. Only the fields derived from them and from the
test set's labels are recomputed: the expected outcome and card range, Stage 1
correctness, which samples are scored in Stage 2, the card count check, and the
source check.

The recomputed folder gets results.json, run.json, summary.md, and
scoring_sheet.md. It never gets a scores.csv, so hand scores saved there are
never overwritten. Score the recomputed run with score_run.py. See
eval/README.md.

Usage:
    .venv/bin/python eval/recompute_run.py eval/runs/2026-10-02_215109
"""
import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

# Reuses the runner's derivation and metric code, so a recomputed run is
# scored exactly the way a new run is. Importing it doesn't call the API.
from run_eval import (
    TEST_SET_PATH,
    compute_metrics,
    compute_metrics_by_category,
    derive_fields,
    format_rate,
    get_source_text_hash,
    get_test_set_hash,
    list_errored_samples,
    read_rubric_version,
    read_test_set_version,
    write_json,
    write_scoring_sheet,
    write_summary,
)

RESCORED_DIRNAME = "rescored"
# Runs made before the test set was versioned used version 1.
UNVERSIONED_TEST_SET = "1"

# What the model produced. Copied from the original record and checked to be
# unchanged before anything is written.
RECORDED_FIELDS = ["id", "outcome", "error", "raw_text", "output", "metadata"]
RECORDED_CARD_FIELDS = ["card_id", "question", "answer", "source"]
# Rebuilt from the recomputed records rather than copied.
REBUILT_RUN_FIELDS = ["errored_samples", "metrics", "metrics_by_category"]


def recorded_parts(record: dict) -> tuple:
    return (
        {k: record[k] for k in RECORDED_FIELDS},
        [{k: card[k] for k in RECORDED_CARD_FIELDS} for card in record["cards"]],
    )


def build_run_info(run_info: dict, all_samples: list[dict], samples: list[dict], records: list[dict]) -> dict:
    # Keeps the original key order, with the version fields after
    # rubric_version as in a new run.
    new_info = {}
    for key, value in run_info.items():
        if key in REBUILT_RUN_FIELDS or key in ("test_set_version", "test_set_hash", "source_text_hash"):
            continue
        new_info[key] = value
        if key == "rubric_version":
            new_info["rubric_version"] = read_rubric_version()
            new_info["test_set_version"] = read_test_set_version()
            new_info["test_set_hash"] = get_test_set_hash(all_samples)
            new_info["source_text_hash"] = get_source_text_hash(samples)

    # A run that covers fewer samples than the current test set (for
    # example, after a sample is added) is partial under it.
    new_info["partial"] = len(samples) < len(all_samples)
    new_info["test_set_size"] = len(all_samples)
    new_info["incomplete"] = any(r["outcome"] == "error" for r in records)
    new_info["recomputed_from"] = {
        "rubric_version": run_info["rubric_version"],
        "test_set_version": run_info.get("test_set_version", UNVERSIONED_TEST_SET),
        "test_set_hash": run_info.get("test_set_hash"),
        "recomputed_at": datetime.now().isoformat(timespec="seconds"),
    }
    return new_info


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute a run's automated metrics under the current test set and rubric.")
    parser.add_argument("run_dir", help="the original run folder, e.g. eval/runs/2026-10-02_215109")
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        sys.exit(f"{run_dir} is not a folder.")
    if run_dir.parent.name == RESCORED_DIRNAME:
        sys.exit(f"{run_dir} is already a recomputed run. Pass the original run folder.")
    run_info = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    records = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))

    all_samples = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
    samples_by_id = {s["id"]: s for s in all_samples}
    missing = [sid for sid in run_info["sample_ids"] if sid not in samples_by_id]
    if missing:
        sys.exit(f"The current test set has no sample with ID {', '.join(missing)}, so this run can't be recomputed.")
    samples = [samples_by_id[sid] for sid in run_info["sample_ids"]]

    # Recomputing is only valid against the notes the run was generated from.
    recorded_hash = run_info.get("source_text_hash")
    if recorded_hash is None:
        print("Note: this run predates source_text_hash, so its notes can't be checked against the current test set.")
    elif recorded_hash != get_source_text_hash(samples):
        sys.exit(
            "The source text of one or more of this run's samples has changed since the run, so its "
            "outputs can't be rescored against the current test set."
        )

    new_records = []
    for record in records:
        new_record = copy.deepcopy(record)
        derive_fields(new_record, samples_by_id[record["id"]])
        # A safeguard: derive_fields should never touch the model's output.
        if recorded_parts(new_record) != recorded_parts(record):
            sys.exit(f"Recomputing changed recorded fields of {record['id']}. Nothing was written.")
        new_records.append(new_record)

    new_info = build_run_info(run_info, all_samples, samples, new_records)
    metrics = compute_metrics(new_records)
    by_category = compute_metrics_by_category(new_records)

    out_dir = run_dir / RESCORED_DIRNAME / f"rubric-{new_info['rubric_version']}_test-set-{new_info['test_set_version']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "results.json", new_records)
    write_summary(out_dir / "summary.md", new_info, metrics, by_category, new_records)
    write_scoring_sheet(out_dir / "scoring_sheet.md", new_info["run_id"], new_records, samples_by_id)
    write_json(out_dir / "run.json", {
        **new_info,
        "errored_samples": list_errored_samples(new_records),
        "metrics": metrics,
        "metrics_by_category": by_category,
    })

    old = run_info.get("metrics", {}).get("stage2", {})
    for name in ("card_count_pass_rate", "source_match_rate"):
        before = format_rate(old[name]) if name in old else "n/a"
        print(f"{name.replace('_', ' ').capitalize()}: {before} -> {format_rate(metrics['stage2'][name])}")
    print(f"Recomputed run written to {out_dir}")


if __name__ == "__main__":
    main()
