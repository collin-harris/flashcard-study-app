#!/usr/bin/env python3
"""Runs the card generation module against the evaluation test set.

Calls the same generate_cards() function the API endpoint will use, computes
the automated metrics defined in eval/rubric.md, and writes everything for the
run to its own folder in eval/runs/ (eval/runs/partial/ for a --samples run),
including a hand-scoring sheet for the judgment-based criteria. Each sample's
result is saved as soon as it finishes, so an interrupted run keeps the
samples that completed.

Requires ANTHROPIC_API_KEY, either exported in the shell or set in the
repo's .env file, and the eval dependencies installed into .venv
(uv pip install -r eval/requirements.txt). See eval/README.md.

Usage:
    .venv/bin/python eval/run_eval.py
    .venv/bin/python eval/run_eval.py --samples sample_001,sample_031
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "eval"

# Makes the backend's `app` package importable, so the runner calls the exact
# generation code the API will ship with rather than a copy of it.
sys.path.insert(0, str(REPO_ROOT / "backend"))

import anthropic  # noqa: E402
from dotenv import dotenv_values  # noqa: E402
from app.services import card_generation  # noqa: E402
from app.services.card_generation import CardGenerationError, GeneratedCards, generate_cards  # noqa: E402

TEST_SET_PATH = EVAL_DIR / "test_set" / "test_set.json"
RUBRIC_PATH = EVAL_DIR / "rubric.md"
RUNS_DIR = EVAL_DIR / "runs"
# Partial runs are smoke tests, kept apart from full runs and never committed
# (see .gitignore).
PARTIAL_RUNS_DIR = RUNS_DIR / "partial"
ENV_PATH = REPO_ROOT / ".env"

GATE_APPROACH = "single call"
REJECT_CATEGORY = "unusable_input"  # the only category expected to be rejected


# ---------------------------------------------------------------------------
# Running samples
# ---------------------------------------------------------------------------

def read_rubric_version() -> str:
    # Read from the rubric itself so the recorded version can't go stale.
    match = re.search(r"^\*\*Rubric Version:\*\*\s*(\S+)", RUBRIC_PATH.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        sys.exit(f"Could not find a '**Rubric Version:**' line in {RUBRIC_PATH}.")
    return match.group(1)


def expected_outcome(sample: dict) -> str:
    return "reject" if REJECT_CATEGORY in sample["tags"] else "accept"


def normalize_whitespace(text: str) -> str:
    # Collapses every run of whitespace (spaces, tabs, newlines) to one space.
    return " ".join(text.split())


def excerpt_matches(excerpt: str, normalized_source: str) -> bool:
    # An empty excerpt would be a substring of anything, so it never matches.
    normalized = normalize_whitespace(excerpt)
    return bool(normalized) and normalized in normalized_source


def run_sample(sample: dict) -> dict:
    record = {
        "id": sample["id"],
        "tags": sample["tags"],
        "expected_outcome": expected_outcome(sample),
        "expected_card_range": sample["expected_card_range"],
        "outcome": None,  # "accept", "reject", or "error"
        "stage1_correct": None,
        "scored_in_stage2": False,
        "error": None,
        "raw_text": None,
        "output": None,
        "metadata": None,
        "card_count": None,
        "card_count_in_range": None,
        "cards": [],
    }

    try:
        result = generate_cards(sample["source_text"])
    except CardGenerationError as e:
        record["outcome"] = "error"
        record["error"] = {"kind": e.kind, "message": str(e)}
        record["raw_text"] = e.raw_text
        record["metadata"] = e.metadata.model_dump() if e.metadata else None
        return record
    except Exception as e:
        # Anything else is most likely a bug, but one bad sample shouldn't
        # throw away the results (and cost) of the rest of the run.
        record["outcome"] = "error"
        record["error"] = {"kind": "unexpected_error", "message": repr(e)}
        return record

    record["raw_text"] = result.raw_text
    record["output"] = result.output.model_dump()
    record["metadata"] = result.metadata.model_dump()

    accepted = isinstance(result.output, GeneratedCards)
    record["outcome"] = "accept" if accepted else "reject"
    record["stage1_correct"] = record["outcome"] == record["expected_outcome"]
    record["scored_in_stage2"] = accepted and record["stage1_correct"]

    # Cards are checked for every accepted sample so false acceptances can be
    # inspected too, but only scored_in_stage2 samples count toward metrics.
    if accepted:
        low, high = sample["expected_card_range"]
        record["card_count"] = len(result.output.cards)
        record["card_count_in_range"] = low <= record["card_count"] <= high

        normalized_source = normalize_whitespace(sample["source_text"])
        for number, card in enumerate(result.output.cards, start=1):
            matches = [excerpt_matches(excerpt, normalized_source) for excerpt in card.source]
            record["cards"].append({
                "card_id": f"{sample['id']}-c{number:02d}",
                "question": card.question,
                "answer": card.answer,
                "source": card.source,
                "excerpt_matches": matches,
                "source_matches": bool(matches) and all(matches),
            })

    return record


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def rate(count: int, total: int) -> dict:
    return {"count": count, "total": total, "rate": count / total if total else None}


def compute_metrics(records: list[dict]) -> dict:
    # Errored samples are left out of the Stage 1 and Stage 2 rate
    # denominators and reported separately as the error rate; a run with
    # errors shouldn't be used as a baseline anyway.
    completed = [r for r in records if r["outcome"] != "error"]
    expected_accept = [r for r in completed if r["expected_outcome"] == "accept"]
    expected_reject = [r for r in completed if r["expected_outcome"] == "reject"]
    stage2 = [r for r in completed if r["scored_in_stage2"]]
    cards = [card for r in stage2 for card in r["cards"]]

    # Failed calls that still got a response were billed, so they count
    # toward cost. Calls that never reached the API have no metadata.
    with_response = [r for r in records if r["metadata"]]
    total_cost = sum(r["metadata"]["cost_usd"] for r in with_response)
    total_latency = sum(r["metadata"]["latency_seconds"] for r in with_response)

    return {
        "samples_run": len(records),
        "error_rate": rate(len(records) - len(completed), len(records)),
        "stage1": {
            "false_rejection_rate": rate(sum(r["outcome"] == "reject" for r in expected_accept), len(expected_accept)),
            "false_acceptance_rate": rate(sum(r["outcome"] == "accept" for r in expected_reject), len(expected_reject)),
        },
        "stage2": {
            "batches_scored": len(stage2),
            "cards_scored": len(cards),
            "card_count_pass_rate": rate(sum(r["card_count_in_range"] for r in stage2), len(stage2)),
            "source_match_rate": rate(sum(card["source_matches"] for card in cards), len(cards)),
        },
        "operational": {
            "total_input_tokens": sum(r["metadata"]["input_tokens"] for r in with_response),
            "total_output_tokens": sum(r["metadata"]["output_tokens"] for r in with_response),
            "total_cost_usd": total_cost,
            "average_cost_usd": total_cost / len(records) if records else None,
            "average_latency_seconds": total_latency / len(with_response) if with_response else None,
        },
    }


def compute_metrics_by_category(records: list[dict]) -> dict:
    # A sample counts toward every tag it carries.
    by_tag = defaultdict(list)
    for record in records:
        for tag in record["tags"]:
            by_tag[tag].append(record)
    return {tag: compute_metrics(by_tag[tag]) for tag in sorted(by_tag)}


def list_errored_samples(records: list[dict]) -> list[dict]:
    return [
        {
            "id": r["id"],
            "tags": r["tags"],
            "error_kind": r["error"]["kind"],
            "error_message": r["error"]["message"],
        }
        for r in records
        if r["outcome"] == "error"
    ]


# ---------------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------------

def format_rate(r: dict) -> str:
    if r["rate"] is None:
        return "n/a (0/0)"
    return f"{r['rate']:.1%} ({r['count']}/{r['total']})"


def format_optional(value, fmt: str) -> str:
    return "n/a" if value is None else format(value, fmt)


def fence_for(text: str) -> str:
    # A code fence longer than any run of backticks in the text, so code
    # samples containing ``` can't close the block early.
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def inline_code(text: str) -> str:
    # Shows an excerpt literally, with newlines made visible, so markdown
    # characters in notes (*, _, |) don't turn into formatting.
    text = text.replace("\n", " ↵ ")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    delimiter = "`" * (longest + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{delimiter}{padding}{text}{padding}{delimiter}"


def write_json(path: Path, data) -> None:
    # Written to a temporary file and then renamed over the target, so an
    # interruption mid-write leaves the previous version intact instead of a
    # half-written file.
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp_path, path)


def write_summary(path: Path, run_info: dict, metrics: dict, by_category: dict, records: list[dict]) -> None:
    error_rate = metrics["error_rate"]
    samples_run = metrics["samples_run"]
    samples_selected = len(run_info["sample_ids"])
    test_set_size = run_info["test_set_size"]

    # Partial (a --samples subset), interrupted (stopped before every selected
    # sample ran), and incomplete (some samples errored) are independent, so
    # all three are always stated, each with its own warning.
    lines = [
        f"# Evaluation Run {run_info['run_id']}",
        "",
        "## Run Status",
        "",
        f"- **Error rate:** {format_rate(error_rate)}",
    ]
    if run_info["partial"]:
        lines.append(
            f"- **Partial:** Yes. Only {samples_selected} of {test_set_size} test set samples were selected "
            "(`--samples`). Use for smoke testing only, not as a baseline."
        )
    else:
        lines.append(f"- **Partial:** No. All {test_set_size} test set samples were selected.")
    if run_info["interrupted"]:
        lines.append(f"- **Interrupted:** Yes. The run stopped after {samples_run} of {samples_selected} samples.")
    else:
        lines.append(f"- **Interrupted:** No. All {samples_selected} selected samples ran.")
    if run_info["incomplete"]:
        lines.append(f"- **Incomplete:** Yes. {error_rate['count']} of {samples_run} samples errored.")
    else:
        lines.append("- **Incomplete:** No. No samples errored.")
    lines.append("")

    if run_info["incomplete"]:
        lines += [
            f"> ⚠️ **Do not use this run as a baseline or comparison point.** {error_rate['count']} sample(s)",
            "> errored and were excluded from all Stage 1 and Stage 2 rates below, so",
            "> the results may look better than they are. Resolve the errored samples",
            "> and rerun first.",
            "",
        ]
    if run_info["interrupted"]:
        lines += [
            f"> ⚠️ **Interrupted run.** Only {samples_run} of {samples_selected} selected samples finished",
            "> before the run was stopped, so the rates below leave the rest out. Do not",
            "> use this run as a baseline or comparison point; rerun it in full.",
            "",
        ]
    if run_info["partial"]:
        lines += [
            "> ⚠️ **Partial run.** The rates below cover only the samples selected with",
            "> `--samples`, so they aren't comparable with full runs.",
            "",
        ]

    lines += ["## Run Details", ""]
    for key, value in run_info.items():
        if key not in ("sample_ids", "partial", "interrupted", "incomplete", "test_set_size"):
            lines.append(f"- **{key}:** {value}")
    lines.append("")

    errored = list_errored_samples(records)
    lines += ["## Errored Samples", ""]
    if errored:
        lines += [
            f"**{len(errored)} sample(s) errored and are excluded from all Stage 1 and Stage 2 rates below.**",
            "",
            "| Sample | Category | Error kind | Message |",
            "|---|---|---|---|",
        ]
        for e in errored:
            # First line only, with pipes escaped so the message can't break the table.
            message = e["error_message"].splitlines()[0].replace("|", "\\|") if e["error_message"] else ""
            lines.append(f"| {e['id']} | {', '.join(e['tags'])} | {e['error_kind']} | {message} |")
    else:
        lines.append("None.")
    lines.append("")

    s1, s2, op = metrics["stage1"], metrics["stage2"], metrics["operational"]
    lines += [
        "## Overall",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Samples run | {metrics['samples_run']} |",
        f"| Error rate | {format_rate(error_rate)} |",
        f"| False rejection rate | {format_rate(s1['false_rejection_rate'])} |",
        f"| False acceptance rate | {format_rate(s1['false_acceptance_rate'])} |",
        f"| Batches scored in Stage 2 | {s2['batches_scored']} |",
        f"| Cards scored in Stage 2 | {s2['cards_scored']} |",
        f"| Card count pass rate | {format_rate(s2['card_count_pass_rate'])} |",
        f"| Source match rate | {format_rate(s2['source_match_rate'])} |",
        f"| Total tokens (input / output) | {op['total_input_tokens']} / {op['total_output_tokens']} |",
        f"| Total cost | ${op['total_cost_usd']:.4f} |",
        f"| Average cost per generation | ${format_optional(op['average_cost_usd'], '.4f')} |",
        f"| Average latency per generation | {format_optional(op['average_latency_seconds'], '.2f')}s |",
        "",
        "## By Category",
        "",
        "| Category | Samples | Error rate | False rejection | False acceptance | Card count pass | Source match | Avg cost | Avg latency |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for tag, m in by_category.items():
        lines.append(
            f"| {tag} | {m['samples_run']} | {format_rate(m['error_rate'])} "
            f"| {format_rate(m['stage1']['false_rejection_rate'])} "
            f"| {format_rate(m['stage1']['false_acceptance_rate'])} "
            f"| {format_rate(m['stage2']['card_count_pass_rate'])} "
            f"| {format_rate(m['stage2']['source_match_rate'])} "
            f"| ${format_optional(m['operational']['average_cost_usd'], '.4f')} "
            f"| {format_optional(m['operational']['average_latency_seconds'], '.2f')}s |"
        )

    lines += [
        "",
        "## By Sample",
        "",
        "| Sample | Category | Expected | Outcome | Cards (expected) | Sources matching |",
        "|---|---|---|---|---|---|",
    ]
    for r in records:
        low, high = r["expected_card_range"]
        cards = "-" if r["card_count"] is None else f"{r['card_count']} ({low}–{high})"
        sources = "-" if not r["cards"] else f"{sum(c['source_matches'] for c in r['cards'])}/{len(r['cards'])}"
        outcome = r["outcome"] if r["outcome"] != "error" else f"error: {r['error']['kind']}"
        lines.append(f"| {r['id']} | {', '.join(r['tags'])} | {r['expected_outcome']} | {outcome} | {cards} | {sources} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_scoring_sheet(path: Path, run_id: str, records: list[dict], samples_by_id: dict) -> None:
    lines = [
        f"# Hand-Scoring Sheet: Run {run_id}",
        "",
        "Read-only reference. Record scores in `scores.csv` next to this file:",
        "",
        "- `atomic`, `supported`, `no_leakage`, `unambiguous`: `Y` or `N`",
        "- `duplicate_of`: the card ID of the earlier card it duplicates, or blank",
        "",
        "Definitions and examples for each criterion are in `eval/rubric.md`.",
        "✓/✗ beside each excerpt is the automated source check, which is evidence",
        "to verify, not proof that the card is supported.",
        "",
    ]
    for r in records:
        if not r["scored_in_stage2"]:
            continue
        sample = samples_by_id[r["id"]]
        low, high = r["expected_card_range"]
        fence = fence_for(sample["source_text"])
        lines += [
            "---",
            "",
            f"## {r['id']}: {', '.join(r['tags'])}",
            "",
            f"**Cards:** {r['card_count']} (expected {low}–{high})",
            "",
            f"**Test set note:** {sample['notes']}",
            "",
            "**Source text:**",
            "",
            f"{fence}text",
            sample["source_text"],
            fence,
            "",
        ]
        for card in r["cards"]:
            lines += [
                f"### {card['card_id']}",
                "",
                f"**Q:** {card['question']}",
                "",
                f"**A:** {card['answer']}",
                "",
                "**Source:**",
                "",
            ]
            for excerpt, matched in zip(card["source"], card["excerpt_matches"]):
                lines.append(f"- {'✓' if matched else '✗'} {inline_code(excerpt)}")
            lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_scores_csv(path: Path, records: list[dict]) -> None:
    # utf-8-sig adds a byte order mark so Excel detects UTF-8 instead of
    # garbling non-ASCII characters in questions and answers.
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "card_id", "sample_id", "category", "question", "answer",
            "atomic", "supported", "no_leakage", "unambiguous", "duplicate_of", "notes",
        ])
        for r in records:
            if not r["scored_in_stage2"]:
                continue
            for card in r["cards"]:
                writer.writerow([
                    card["card_id"], r["id"], ", ".join(r["tags"]), card["question"], card["answer"],
                    "", "", "", "", "", "",
                ])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def load_api_key() -> None:
    # Docker Compose loads .env automatically, but a local script doesn't.
    # A key already exported in the shell wins; otherwise only
    # ANTHROPIC_API_KEY is read from .env. The file's other values
    # (DATABASE_URL and so on) are never loaded into the environment.
    if os.environ.get("ANTHROPIC_API_KEY") or not ENV_PATH.exists():
        return
    key = dotenv_values(ENV_PATH).get("ANTHROPIC_API_KEY")
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the card generation evaluation.")
    parser.add_argument("--samples", help="comma-separated sample IDs to run (default: all)")
    args = parser.parse_args()

    # Checked up front so a missing key fails once, not once per sample.
    load_api_key()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Add it to .env at the repo root or export it in this shell.")

    all_samples = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
    samples = all_samples
    if args.samples:
        wanted = {s.strip() for s in args.samples.split(",") if s.strip()}
        unknown = wanted - {s["id"] for s in all_samples}
        if unknown:
            sys.exit(f"Unknown sample IDs: {', '.join(sorted(unknown))}")
        samples = [s for s in all_samples if s["id"] in wanted]

    # A partial run (--samples) is for smoke testing, never a baseline.
    partial = len(samples) < len(all_samples)
    now = datetime.now()
    run_id = now.strftime("%Y-%m-%d_%H%M%S")
    run_dir = (PARTIAL_RUNS_DIR if partial else RUNS_DIR) / run_id
    run_dir.mkdir(parents=True)

    run_info = {
        "run_id": run_id,
        "date": now.isoformat(timespec="seconds"),
        "rubric_version": read_rubric_version(),
        "model": card_generation.MODEL,
        "prompt_version": card_generation.PROMPT_VERSION,
        "prompt_hash": card_generation.get_prompt_hash(),
        "max_tokens": card_generation.MAX_TOKENS,
        "request_timeout_seconds": card_generation.REQUEST_TIMEOUT_SECONDS,
        "max_retries": card_generation.MAX_RETRIES,
        "gate_approach": GATE_APPROACH,
        "anthropic_sdk_version": anthropic.__version__,
        "partial": partial,
        # Starts true and is cleared only once every selected sample has run
        # and all output is written, so a run killed outright (not just by
        # Ctrl+C) is still marked interrupted.
        "interrupted": True,
        # An incomplete run had errored samples, so its rates leave some out
        # and it can't be a baseline either. Set once the run finishes.
        "incomplete": None,
        "test_set_size": len(all_samples),
        "sample_ids": [s["id"] for s in samples],
    }
    write_json(run_dir / "run.json", run_info)

    records = []
    interrupted = False
    try:
        for i, sample in enumerate(samples, start=1):
            record = run_sample(sample)
            records.append(record)
            # Saved after every sample, so an interrupted run keeps the
            # samples that finished.
            write_json(run_dir / "results.json", records)

            if record["outcome"] == "error":
                status = f"ERROR ({record['error']['kind']})"
            elif record["outcome"] == "accept":
                status = f"accept, {record['card_count']} cards"
            else:
                status = "reject"
            check = "" if record["stage1_correct"] is None else (" ok" if record["stage1_correct"] else " WRONG")
            cost = f" ${record['metadata']['cost_usd']:.4f}" if record["metadata"] else ""
            print(f"[{i}/{len(samples)}] {sample['id']}: {status}{check}{cost}")
    except KeyboardInterrupt:
        # The finished samples are still written up below, marked interrupted.
        interrupted = True
        print(f"\nInterrupted after {len(records)} of {len(samples)} samples. Writing results for those.")

    metrics = compute_metrics(records)
    by_category = compute_metrics_by_category(records)
    run_info["interrupted"] = interrupted
    run_info["incomplete"] = metrics["error_rate"]["count"] > 0

    run_record = {
        **run_info,
        "errored_samples": list_errored_samples(records),
        "metrics": metrics,
        "metrics_by_category": by_category,
    }
    write_json(run_dir / "results.json", records)
    write_summary(run_dir / "summary.md", run_info, metrics, by_category, records)
    write_scoring_sheet(run_dir / "scoring_sheet.md", run_id, records, {s["id"]: s for s in samples})
    write_scores_csv(run_dir / "scores.csv", records)
    # Written last, so run.json says the run wasn't interrupted only once
    # every other file is in place.
    write_json(run_dir / "run.json", run_record)

    print()
    print(f"Error rate: {format_rate(metrics['error_rate'])}")
    print(f"False rejection rate: {format_rate(metrics['stage1']['false_rejection_rate'])}")
    print(f"False acceptance rate: {format_rate(metrics['stage1']['false_acceptance_rate'])}")
    print(f"Card count pass rate: {format_rate(metrics['stage2']['card_count_pass_rate'])}")
    print(f"Source match rate: {format_rate(metrics['stage2']['source_match_rate'])}")
    print(f"Total cost: ${metrics['operational']['total_cost_usd']:.4f}")
    print(f"Results written to {run_dir}")
    if run_info["interrupted"]:
        print()
        print(
            "WARNING: this run was interrupted. Do not use it as a baseline or comparison "
            "point; rerun it in full."
        )
    if run_info["incomplete"]:
        print()
        print(
            "WARNING: this run is incomplete. Do not use it as a baseline or comparison "
            "point until the errored samples are resolved."
        )


if __name__ == "__main__":
    main()
