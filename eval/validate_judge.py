#!/usr/bin/env python3
"""Compares LLM judge runs with the hand scores and decides whether the judge is validated.

Takes two judge runs on Run 1 under rubric 1.6 and two judge runs on the
seeded examples, all made with the same judge hash, and checks them against
the definition in eval/README.md ("Validating the judge"). Writes a report to
eval/judge/validation/<scorer>.md, with the same results in a .json file
beside it.

The hand scores are the run's scores.csv. If the run folder has a
score_changes.csv, every change it lists as prompted by a judge run is
reverted to rebuild the original scores, and the report compares the judge
against both. The verdict is decided on the corrected scores; changes marked
pre-judge are part of both. Uses only the standard library and makes no API
calls.

Usage:
    .venv/bin/python eval/validate_judge.py \\
        --runs <judge_run_A> <judge_run_B> --seeded <seeded_run_A> <seeded_run_B> \\
        [--discarded <judge_run>...] [--agreement-sample <agreement_sample.csv>]
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from score_run import CRITERIA, PRE_JUDGE, format_rate, load_json, rate, read_scores, write_json

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "eval"
JUDGE_DIR = EVAL_DIR / "judge"
SEEDED_EXAMPLES_PATH = JUDGE_DIR / "seeded_examples.json"
VALIDATION_DIR = JUDGE_DIR / "validation"

# The validation definition in eval/README.md. Changing any of these means
# changing that definition too.
VALIDATION_RUN_ID = "2026-10-02_215109"
VALIDATION_RUBRIC_VERSION = "1.6"
VALIDATION_TEST_SET_VERSION = "2"
# "Catches at least 10 of my 12" and so on, written as the number of hand-
# scored failures the judge may miss, so the rule still applies if a hand
# score is corrected.
MAX_MISSES = {"unambiguous": 2, "atomic": 2, "no_leakage": 1}
MAX_FALSE_ALARM_RATE = 0.05
CLEAN_RATE_TOLERANCE = 0.03
SEEDED_TOTALS = {"supported": 5, "atomic": 5, "no_leakage": 5, "unambiguous": 5, "duplicate": 6}
SEEDED_MIN_CORRECT = {"supported": 4, "atomic": 4, "no_leakage": 4, "unambiguous": 4, "duplicate": 5}

# Duplicates are compared alongside the four criteria, as "is this card a
# duplicate?"
LABELS = [*CRITERIA, "duplicate"]
LABEL_NAMES = {
    "atomic": "Atomic", "supported": "Supported", "no_leakage": "No leakage",
    "unambiguous": "Unambiguous", "duplicate": "Duplicates",
}

# What made each change in score_changes.csv, read from its provenance (and
# prompted_by for a pre-judge change). Only a judge review change was
# prompted by the judge: decided while reviewing its disagreements, blind
# (before reading its reason), after reading it, or after rereading the notes.
JUDGE_REVIEW_PROVENANCES = ("blind", "after judge", "after recheck")
CHANGE_KINDS = ["pre-judge", "judge review", "agreement check", "consistency check"]
CHANGE_KIND_TEXT = {
    "pre-judge": "pre-judge", "judge review": "from the judge review",
    "agreement check": "from the agreement check", "consistency check": "from the consistency check",
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def hash_json(data) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def load_judge_run(path: Path, mode: str) -> tuple[dict, dict]:
    """Returns a judge run's info and its grades by card ID."""
    info = load_json(path / "judge_run.json")
    results = load_json(path / "judge_results.json")
    problems = []
    if info.get("mode") != mode:
        problems.append(f"{path} is a {info.get('mode')} judge run, expected {mode}.")
    for flag in ("partial", "interrupted", "incomplete"):
        if info.get(flag) is not False:
            problems.append(f"{path} is marked {flag}, so it can't be used for validation.")
    if problems:
        sys.exit("\n".join(problems))
    grades = {g["card_id"]: g for record in results for g in record["grades"]}
    return info, grades


def retry_stats(name: str, path: Path, discarded: bool = False) -> dict:
    """API calls, retries, invalid outputs, and cost for one judge run."""
    info = load_json(path / "judge_run.json")
    results = load_json(path / "judge_results.json")
    # A retried attempt is in failed_attempts; a sample's last attempt is
    # its top-level error (only in an incomplete run, or one made before
    # retries were added).
    invalid = []
    for r in results:
        for attempt in [*r.get("failed_attempts", []), r]:
            if attempt["error"] and attempt["error"]["kind"] == "invalid_output":
                invalid.append({"id": r["id"], "message": attempt["error"]["message"]})
    flags = [flag for flag in ("incomplete", "interrupted") if info.get(flag) is not False]
    return {
        "pass": name,
        "judge_run_id": info["judge_run_id"],
        "discarded": discarded,
        "status": f"discarded ({', '.join(flags) or 'complete'})" if discarded else "",
        # A run made before retries were added has no attempts field and
        # made one call per sample.
        "api_calls": sum(r.get("attempts", 1) for r in results),
        "retries": sum(r.get("attempts", 1) - 1 for r in results),
        "invalid_outputs": invalid,
        "recorded_retries": all("attempts" in r for r in results),
        "cost_usd": info["metrics"]["total_cost_usd"],
    }


def label_of(scores: dict, key: str):
    # The value compared for each label: Y or N, or the card a duplicate
    # points to (None for a card that isn't a duplicate).
    return scores["duplicate_of"] if key == "duplicate" else scores[key]


def load_hand_scores(run_dir: Path, cards: dict) -> tuple[dict, dict]:
    """Returns the hand labels and notes from scores.csv, by card ID."""
    path = run_dir / "scores.csv"
    parsed, problems = read_scores(path, cards)
    if problems:
        sys.exit(f"{path} has {len(problems)} problem(s):\n" + "\n".join(f"- {p}" for p in problems))
    labels = {
        card_id: {**{c: "Y" if s[c] else "N" for c in CRITERIA}, "duplicate_of": s["duplicate_of"]}
        for card_id, s in parsed.items()
    }
    with path.open(encoding="utf-8-sig", newline="") as f:
        notes = {row["card_id"].strip(): (row.get("notes") or "").strip() for row in csv.DictReader(f) if row.get("card_id")}
    return labels, notes


def change_kind(change: dict) -> str | None:
    if change["prompted_by"] == PRE_JUDGE:
        return "pre-judge"
    provenance = change.get("provenance", "")
    if provenance in JUDGE_REVIEW_PROVENANCES:
        return "judge review"
    return provenance if provenance in CHANGE_KINDS else None


def load_score_changes(run_dir: Path) -> list[dict]:
    path = run_dir / "score_changes.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        changes = [{k: (v or "").strip() for k, v in row.items() if k is not None} for row in csv.DictReader(f)]
    # Every change is counted and marked by what made it, so one without a
    # known provenance is refused rather than guessed.
    unknown = [c for c in changes if change_kind(c) is None]
    if unknown:
        known = ", ".join(f"'{p}'" for p in (*JUDGE_REVIEW_PROVENANCES, *CHANGE_KINDS[2:]))
        sys.exit(f"{path} has {len(unknown)} change(s) with an unknown provenance (expected {known}, "
                 f"or prompted_by '{PRE_JUDGE}'):\n"
                 + "\n".join(f"- {c['card_id']} {c['field']}: '{c.get('provenance', '')}'" for c in unknown))
    return changes


def rebuild_original(corrected: dict, changes: list[dict]) -> dict:
    """Reverts every change not marked pre-judge, newest first, to get the scores as first made."""
    original = {card_id: dict(labels) for card_id, labels in corrected.items()}
    problems = []
    for change in reversed(changes):
        if change["prompted_by"] == PRE_JUDGE:
            continue
        card_id, field = change["card_id"], change["field"]
        if card_id not in original or field not in (*CRITERIA, "duplicate_of"):
            problems.append(f"score_changes.csv: unknown card or field ({card_id}, {field}).")
            continue
        current = original[card_id][field] or ""
        if current != change["new"]:
            problems.append(
                f"score_changes.csv: {card_id} {field} is '{current}' in scores.csv, but the log says it was "
                f"changed to '{change['new']}'. The log and scores.csv are out of sync."
            )
            continue
        if field == "duplicate_of":
            original[card_id][field] = change["old"] or None
        else:
            original[card_id][field] = change["old"]
    if problems:
        sys.exit("\n".join(problems))
    return original


def check_agreement_sample(path: Path, original: dict, run_grades: list[dict]) -> dict:
    """A blind recheck of pairs where the original hand score and both judge runs agreed.

    A pair whose recheck differs is a shared error: the hand score and both
    runs were wrong together, which no catch or false alarm check can see.
    The random seed is read from the sample's .md file beside it.
    """
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]
    notes_path = path.with_suffix(".md")
    seed = re.search(r"\*\*Random seed:\*\*\s*(\d+)", notes_path.read_text(encoding="utf-8")) if notes_path.exists() else None
    problems = [] if seed else [f"{notes_path} doesn't record the sample's random seed (a '**Random seed:** <n>' line)."]
    pairs = []
    for row in rows:
        card_id, key = row["card_id"], row["criterion"]
        if card_id not in original or key not in CRITERIA:
            problems.append(f"{path.name}: unknown card or criterion ({card_id}, {key}).")
            continue
        agreed = {original[card_id][key], *(g[card_id][key] for g in run_grades)}
        if len(agreed) != 1:
            problems.append(f"{path.name}: {card_id} {key} isn't an agreed pair; the original hand score and the judge runs differ.")
            continue
        if row["decision"].upper() not in ("Y", "N"):
            problems.append(f"{path.name}: {card_id} {key} has no Y or N decision.")
            continue
        pairs.append({"card_id": card_id, "criterion": key, "agreed": agreed.pop(),
                      "recheck": row["decision"].upper(), "reason": row["decision_reason"]})
    if problems:
        sys.exit("\n".join(problems))
    shared = [p for p in pairs if p["recheck"] != p["agreed"]]
    return {
        "file": path.resolve().relative_to(REPO_ROOT).as_posix() if path.resolve().is_relative_to(REPO_ROOT) else str(path),
        "seed": int(seed.group(1)),
        "per_criterion": {key: sum(p["criterion"] == key for p in pairs) for key in CRITERIA},
        "pairs": pairs,
        "matched": len(pairs) - len(shared),
        "shared_errors": shared,
    }


# ---------------------------------------------------------------------------
# Comparing
# ---------------------------------------------------------------------------

def compare(hand: dict, judge: dict) -> dict:
    """Catch rate, false alarm rate, and clean card rate of one judge run against one set of hand scores."""
    by_label = {}
    for key in LABELS:
        if key == "duplicate":
            hand_fails = [c for c in hand if hand[c]["duplicate_of"]]
            judge_fails = {c for c in hand if judge[c]["duplicate_of"]}
        else:
            hand_fails = [c for c in hand if hand[c][key] == "N"]
            judge_fails = {c for c in hand if judge[c][key] == "N"}
        failed_by_hand = set(hand_fails)
        hand_passes = [c for c in hand if c not in failed_by_hand]
        caught = [c for c in hand_fails if c in judge_fails]
        false_alarms = [c for c in hand_passes if c in judge_fails]
        by_label[key] = {
            "catch": rate(len(caught), len(hand_fails)),
            "false_alarm": rate(len(false_alarms), len(hand_passes)),
            "missed": [c for c in hand_fails if c not in judge_fails],
            "false_alarms": false_alarms,
        }
    # A card both scorers call a duplicate, of different earlier cards.
    by_label["duplicate"]["different_original"] = [
        c for c in hand if hand[c]["duplicate_of"] and judge[c]["duplicate_of"]
        and hand[c]["duplicate_of"] != judge[c]["duplicate_of"]
    ]
    def clean(labels: dict) -> dict:
        # Duplicates don't count against the clean card rate (rubric, "Metrics").
        return rate(sum(all(labels[c][k] == "Y" for k in CRITERIA) for c in hand), len(hand))

    return {"labels": by_label, "clean_hand": clean(hand), "clean_judge": clean(judge)}


def score_seeds(seeds: list[dict], grades: dict) -> dict:
    """Whether the judge got each seed's own criterion right, plus any other labels that differ."""
    results = {}
    for seed in seeds:
        expected, got = seed["expected"], grades[seed["id"]]
        key = seed["criterion"]
        expected_value = expected["duplicate_of"] if key == "duplicate" else expected[key]
        off_target = [
            k for k in LABELS
            if k != key and (got["duplicate_of"] if k == "duplicate" else got[k]) != (expected["duplicate_of"] if k == "duplicate" else expected[k])
        ]
        results[seed["id"]] = {
            "correct": label_of(got, key) == expected_value,
            "got": label_of(got, key),
            "off_target": off_target,
        }
    return results


def seeded_counts(seeds: list[dict], scored: dict) -> dict:
    return {
        key: sum(scored[s["id"]]["correct"] for s in seeds if s["criterion"] == key)
        for key in SEEDED_TOTALS
    }


def build_checks(comparisons: list[dict], seed_counts: list[dict]) -> list[dict]:
    """Every threshold in the validation definition, for each judge run."""
    checks = []
    for key, allowed in MAX_MISSES.items():
        fails = comparisons[0]["labels"][key]["catch"]["total"]
        checks.append({
            "check": f"{LABEL_NAMES[key]}: catches",
            "threshold": f"≥ {fails - allowed} of {fails}",
            "values": [format_rate(c["labels"][key]["catch"]) for c in comparisons],
            "passed": [len(c["labels"][key]["missed"]) <= allowed for c in comparisons],
        })
    for key in LABELS:
        checks.append({
            "check": f"{LABEL_NAMES[key]}: false alarm rate",
            "threshold": f"≤ {MAX_FALSE_ALARM_RATE:.0%}",
            "values": [format_rate(c["labels"][key]["false_alarm"]) for c in comparisons],
            "passed": [(c["labels"][key]["false_alarm"]["rate"] or 0) <= MAX_FALSE_ALARM_RATE + 1e-9 for c in comparisons],
        })
    hand_clean = comparisons[0]["clean_hand"]
    checks.append({
        "check": "Clean card rate",
        "threshold": f"within ±{CLEAN_RATE_TOLERANCE * 100:.0f} points of {format_rate(hand_clean)}",
        "values": [format_rate(c["clean_judge"]) for c in comparisons],
        "passed": [abs(c["clean_judge"]["rate"] - hand_clean["rate"]) <= CLEAN_RATE_TOLERANCE + 1e-9 for c in comparisons],
    })
    for key, needed in SEEDED_MIN_CORRECT.items():
        checks.append({
            "check": f"Seeded {LABEL_NAMES[key].lower()}: correct",
            "threshold": f"≥ {needed} of {SEEDED_TOTALS[key]}",
            "values": [f"{counts[key]} of {SEEDED_TOTALS[key]}" for counts in seed_counts],
            "passed": [counts[key] >= needed for counts in seed_counts],
        })
    return checks


def is_validated(checks: list[dict]) -> bool:
    # Every threshold must hold in both runs.
    return all(all(c["passed"]) for c in checks)


def consistency(grades_a: dict, grades_b: dict, card_ids: list[str]) -> dict:
    result = {}
    for key in LABELS:
        flips = [c for c in card_ids if label_of(grades_a[c], key) != label_of(grades_b[c], key)]
        result[key] = {"agreement": rate(len(card_ids) - len(flips), len(card_ids)), "flips": flips}
    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def cell(text) -> str:
    return "—" if text in (None, "") else str(text).replace("|", "\\|").replace("\n", " ")


def verdict_text(validated: bool) -> str:
    return "VALIDATED" if validated else "NOT VALIDATED"


def checks_table(checks: list[dict]) -> list[str]:
    lines = ["| Check | Threshold | Run A | Run B | Result |", "|---|---|---|---|---|"]
    for c in checks:
        result = "pass" if all(c["passed"]) else "**FAIL**"
        values = [v if ok else f"**{v}**" for v, ok in zip(c["values"], c["passed"])]
        lines.append(f"| {c['check']} | {c['threshold']} | {values[0]} | {values[1]} | {result} |")
    return lines


def agreement_summary(agreement: dict | None) -> list[str]:
    if agreement is None:
        return []
    shared = len(agreement["shared_errors"])
    return [
        f"- **Agreement check:** {agreement['matched']} of {len(agreement['pairs'])} matched, "
        f"{shared} shared error{'' if shared == 1 else 's'} (see [Agreement check](#agreement-check))"
    ]


def agreement_section(agreement: dict | None) -> list[str]:
    lines = ["## Agreement check", ""]
    if agreement is None:
        return lines + ["No agreement sample was given (`--agreement-sample`)."]
    n, shared = len(agreement["pairs"]), agreement["shared_errors"]
    per = ", ".join(f"{count} {LABEL_NAMES[key].lower()}" for key, count in agreement["per_criterion"].items())
    lines += [
        f"A blind recheck of {n} card+criterion pairs where the original hand score and both judge runs agreed: "
        f"{agreement['file']}, random seed {agreement['seed']}, {per}. A pair whose recheck differs is a shared "
        "error, where the hand score and both runs were wrong together. Until it's corrected in scores.csv, no "
        "catch or false alarm check can see it. The check is reported only; it isn't part of the verdict.",
        "",
        f"**{agreement['matched']} of {n} matched; {len(shared)} shared error{'' if len(shared) == 1 else 's'}.**",
        "",
    ]
    if not shared:
        return lines + [f"No shared errors in this sample, which doesn't rule them out: {n} pairs can't pin down a low rate."]
    lines += ["| Card | Criterion | Agreed | Recheck | Reason |", "|---|---|---|---|---|"]
    for p in shared:
        lines.append(f"| {p['card_id']} | {p['criterion']} | {p['agreed']} | {p['recheck']} | {cell(p['reason'])} |")
    criteria = sorted({p["criterion"] for p in shared}, key=CRITERIA.index)
    names = " and ".join(LABEL_NAMES[k].lower() for k in criteria)
    lines += [
        "",
        f"**Caveat:** shared errors exist at a rate this sample can't pin down ({len(shared)}/{n}), and the "
        f"{names} result{'s are' if len(criteria) > 1 else ' is'} likely optimistic.",
    ]
    return lines


def write_report(path: Path, data: dict) -> None:
    info = data["judge"]
    corrected_ok, original_ok = data["validated"]["corrected"], data["validated"]["original"]
    counts = data["score_change_counts"]
    later_changes = sum(n for kind, n in counts.items() if kind != "pre-judge")
    change_summary = ", ".join(f"{counts[k]} {CHANGE_KIND_TEXT[k]}" for k in CHANGE_KINDS if counts[k]) or "none"
    lines = [f"# Judge Validation: {info['scorer']}", ""]
    if corrected_ok != original_ok:
        lines += [
            f"> ⚠️ **The verdict differs between your original and corrected scores:** "
            f"{verdict_text(corrected_ok)} against the corrected scores, {verdict_text(original_ok)} against "
            "the original ones. The verdict below uses the corrected scores.",
            "",
        ]
    lines += [
        f"**Verdict (corrected hand scores): {verdict_text(corrected_ok)}**",
        "",
        f"- **Judge:** {info['judge_model']}, prompt {info['judge_prompt_version']}, effort {info['effort']}, "
        f"judge hash {info['judge_hash']}",
        f"- **Ground truth:** {data['hand_scores_file']}, run {VALIDATION_RUN_ID} under rubric "
        f"{VALIDATION_RUBRIC_VERSION} and test set {VALIDATION_TEST_SET_VERSION}",
        f"- **Judge runs:** A = {data['runs'][0]}, B = {data['runs'][1]}",
        f"- **Seeded runs:** A = {data['seeded_runs'][0]}, B = {data['seeded_runs'][1]}",
        f"- **Judge cost:** " + ", ".join(f"${c:.4f}" for c in data["costs"]) + " (runs A, B, seeded A, seeded B)",
        f"- **Total spent, including discarded runs:** ${data['total_spent_usd']:.4f}",
        f"- **Retries:** {data['retries']['total_retries']}; drop rate "
        f"{format_rate(data['retries']['drop_rate'])} of API calls, including discarded runs (see [Retries](#retries))",
        f"- **Score changes:** {change_summary} (see [Score changes](#score-changes))",
        *agreement_summary(data["agreement"]),
        "",
        "Every threshold must hold in both runs. Catch thresholds allow a fixed number of misses "
        "(unambiguous 2, atomic 2, no leakage 1), so they still apply if a hand score is corrected.",
        "",
        "## Checks against the corrected hand scores",
        "",
        *checks_table(data["checks"]["corrected"]),
        "",
        "## Checks against the original hand scores",
        "",
    ]
    if later_changes:
        lines += [*checks_table(data["checks"]["original"]), ""]
    else:
        lines += ["No score has been changed since it was first made, so these are the same as above.", ""]

    lines += [
        "## Per criterion (corrected hand scores)",
        "",
        "| Criterion | Run | My fails | Caught | Catch rate | My passes | False alarms | False alarm rate |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key in LABELS:
        for name, comparison in zip("AB", data["comparisons"]["corrected"]):
            r = comparison["labels"][key]
            lines.append(
                f"| {LABEL_NAMES[key]} | {name} | {r['catch']['total']} | {r['catch']['count']} | {format_rate(r['catch'])} "
                f"| {r['false_alarm']['total']} | {r['false_alarm']['count']} | {format_rate(r['false_alarm'])} |"
            )
    different = sorted({c for comp in data["comparisons"]["corrected"] for c in comp["labels"]["duplicate"]["different_original"]})
    lines += ["", f"Duplicates both of us flagged, with a different original card: {', '.join(different) or 'none'}.", ""]

    clean = data["comparisons"]["corrected"]
    lines += [
        "## Clean card rate",
        "",
        "| Scorer | Clean card rate |",
        "|---|---|",
        f"| Hand (corrected) | {format_rate(clean[0]['clean_hand'])} |",
        f"| Hand (original) | {format_rate(data['comparisons']['original'][0]['clean_hand'])} |",
        f"| Judge run A | {format_rate(clean[0]['clean_judge'])} |",
        f"| Judge run B | {format_rate(clean[1]['clean_judge'])} |",
        "",
        "## Seeded examples",
        "",
        "| Criterion | Run A correct | Run B correct | Needed |",
        "|---|---|---|---|",
    ]
    for key in SEEDED_TOTALS:
        lines.append(
            f"| {LABEL_NAMES[key]} | {data['seeded_counts'][0][key]} of {SEEDED_TOTALS[key]} "
            f"| {data['seeded_counts'][1][key]} of {SEEDED_TOTALS[key]} | {SEEDED_MIN_CORRECT[key]} |"
        )
    lines += [
        "",
        "| Seed | Criterion | Subtlety | Control | Expected | Run A | Run B | Other labels that differ (A / B) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for seed in data["seeds"]:
        a, b = (scored[seed["id"]] for scored in data["seeded"])
        key = seed["criterion"]
        expected = seed["expected"]["duplicate_of"] if key == "duplicate" else seed["expected"][key]
        mark = lambda r: cell(r["got"]) if r["correct"] else f"**{cell(r['got'])}** ✗"  # noqa: E731
        lines.append(
            f"| {seed['id']} | {key} | {seed['subtlety']} | {'yes' if seed['control'] else 'no'} | {cell(expected)} "
            f"| {mark(a)} | {mark(b)} | {', '.join(a['off_target']) or '—'} / {', '.join(b['off_target']) or '—'} |"
        )

    lines += [
        "",
        "## Self-consistency (run A vs run B)",
        "",
        "| Criterion | Agreement | Flipped cards |",
        "|---|---|---|",
    ]
    for key in LABELS:
        r = data["consistency"]["runs"][key]
        lines.append(f"| {LABEL_NAMES[key]} | {format_rate(r['agreement'])} | {', '.join(r['flips']) or '—'} |")
    lines += ["", "| Seeded criterion | Agreement | Flipped seeds |", "|---|---|---|"]
    for key in LABELS:
        r = data["consistency"]["seeded"][key]
        lines.append(f"| {LABEL_NAMES[key]} | {format_rate(r['agreement'])} | {', '.join(r['flips']) or '—'} |")

    retries = data["retries"]
    lines += [
        "",
        "## Retries",
        "",
        "A response that doesn't match the batch, such as a grade list that stops short, is retried once. "
        "The drop rate is those responses as a share of every API call, including discarded runs. "
        "Discarded runs are never graded or compared.",
        "",
        "| Pass | Judge run | Status | API calls | Retries | Dropped outputs | Cost |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in retries["passes"]:
        status = p["status"] or ("used" if p["recorded_retries"] else "used; run before retries existed, so it had none")
        lines.append(
            f"| {p['pass']} | {p['judge_run_id']} | {status} | {p['api_calls']} | {p['retries']} "
            f"| {len(p['invalid_outputs'])} | ${p['cost_usd']:.4f} |"
        )
    lines.append(
        f"| **Total** | | | {retries['drop_rate']['total']} | {retries['total_retries']} "
        f"| {retries['drop_rate']['count']} | ${data['total_spent_usd']:.4f} |"
    )
    lines += ["", f"**Drop rate:** {format_rate(retries['drop_rate'])}", ""]
    for p in retries["passes"]:
        for d in p["invalid_outputs"]:
            lines.append(f"- {p['pass']}, {d['id']}: {cell(d['message'])}")

    lines += ["", *agreement_section(data["agreement"])]

    lines += ["", "## Score changes", ""]
    if data["score_changes"]:
        lines += [
            "| Date | Card | Field | Old | New | Prompted by | Provenance | Rubric rule | Reason |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for c in data["score_changes"]:
            lines.append(
                f"| {c['date']} | {c['card_id']} | {c['field']} | {cell(c['old'])} | {cell(c['new'])} "
                f"| {c['prompted_by']} | {cell(c.get('provenance'))} | {cell(c['rubric_rule'])} | {cell(c['reason'])} |"
            )
    else:
        lines.append("None.")

    lines += [
        "",
        "## Disagreements (corrected hand scores)",
        "",
        "Every card where either judge run differs from the corrected hand score. "
        "A card is marked † where its hand score for that criterion was corrected in the judge review.",
        "",
    ]
    for key in LABELS:
        rows = data["disagreements"][key]
        lines += [f"### {LABEL_NAMES[key]} ({len(rows)})", ""]
        if not rows:
            lines += ["None.", ""]
            continue
        lines += [
            "| Card | Question | Answer | Mine | Run A | Run B | Judge's reason | My note |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            lines.append(
                f"| {r['card_id']}{' †' if r['corrected'] else ''} | {cell(r['question'])} | {cell(r['answer'])} "
                f"| {cell(r['mine'])} | {cell(r['run_a'])} | {cell(r['run_b'])} | {cell(r['reason'])} | {cell(r['note'])} |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def list_disagreements(hand: dict, notes: dict, grades: list[dict], cards: dict, corrected_pairs: set) -> dict:
    result = {}
    for key in LABELS:
        reason_key = key
        rows = []
        for card_id in cards:
            mine = label_of(hand[card_id], key)
            values = [label_of(g[card_id], key) for g in grades]
            if key == "duplicate":
                differs = [bool(v) != bool(mine) or (v and mine and v != mine) for v in values]
            else:
                differs = [v != mine for v in values]
            if not any(differs):
                continue
            reasons = [g[card_id]["reasons"].get(reason_key) for g in grades]
            shown = [f"{name}: {r}" for name, r, d in zip("AB", reasons, differs) if d and r]
            rows.append({
                "card_id": card_id,
                "question": cards[card_id]["question"],
                "answer": cards[card_id]["answer"],
                "mine": mine,
                "run_a": values[0],
                "run_b": values[1],
                "reason": " / ".join(shown) if shown else None,
                "note": notes.get(card_id),
                # Marked per criterion, so a card corrected on one criterion
                # isn't marked under another.
                "corrected": (card_id, "duplicate_of" if key == "duplicate" else key) in corrected_pairs,
            })
        result[key] = rows
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def validate(run_paths: list[Path], seeded_paths: list[Path], output_dir: Path = VALIDATION_DIR,
             discarded_paths: list[Path] = (), agreement_path: Path | None = None) -> dict:
    runs = [load_judge_run(p, "run") for p in run_paths]
    seeded_runs = [load_judge_run(p, "seeded") for p in seeded_paths]
    infos = [info for info, _ in runs + seeded_runs]

    problems = []
    for path in discarded_paths:
        discarded = load_json(path / "judge_run.json")
        if discarded["judge_hash"] != infos[0]["judge_hash"]:
            problems.append(f"Discarded run {discarded['judge_run_id']} was made with a different judge hash.")
        if discarded.get("incomplete") is False and discarded.get("interrupted") is False:
            problems.append(f"Discarded run {discarded['judge_run_id']} is complete; only incomplete or interrupted runs are discarded.")
    if len({info["judge_hash"] for info in infos}) != 1:
        problems.append("The judge runs don't all have the same judge hash, so they aren't the same judge.")
    if run_paths[0].resolve() == run_paths[1].resolve() or seeded_paths[0].resolve() == seeded_paths[1].resolve():
        problems.append("Runs A and B must be two different judge runs.")
    for info in infos:
        if (info["base_run_id"], info["rubric_version"], info["test_set_version"]) != (
            VALIDATION_RUN_ID, VALIDATION_RUBRIC_VERSION, VALIDATION_TEST_SET_VERSION
        ):
            problems.append(
                f"Judge run {info['judge_run_id']} judged run {info['base_run_id']} under rubric "
                f"{info['rubric_version']} and test set {info['test_set_version']}; validation uses run "
                f"{VALIDATION_RUN_ID} under rubric {VALIDATION_RUBRIC_VERSION} and test set {VALIDATION_TEST_SET_VERSION}."
            )
    if len({info["base_run_dir"] for info in infos}) != 1:
        problems.append("The judge runs don't all come from the same run folder.")
    seeds = json.loads(SEEDED_EXAMPLES_PATH.read_text(encoding="utf-8"))
    for info, _ in seeded_runs:
        if info.get("seeded_examples_hash") != hash_json(seeds):
            problems.append(f"Seeded run {info['judge_run_id']} used a different version of seeded_examples.json.")
    counts = {key: sum(s["criterion"] == key for s in seeds) for key in SEEDED_TOTALS}
    if counts != SEEDED_TOTALS:
        problems.append(f"seeded_examples.json has {counts} seeds per criterion; the validation definition expects {SEEDED_TOTALS}.")
    if problems:
        sys.exit(f"Can't validate ({len(problems)} problem(s)):\n" + "\n".join(f"- {p}" for p in problems))

    # Recorded relative to the repo root (absolute only for a run outside it).
    run_dir = REPO_ROOT / infos[0]["base_run_dir"]
    records = load_json(run_dir / "results.json")
    cards = {
        card["card_id"]: {"sample_id": r["id"], "index": index, "question": card["question"], "answer": card["answer"]}
        for r in records if r["scored_in_stage2"]
        for index, card in enumerate(r["cards"])
    }
    corrected, notes = load_hand_scores(run_dir, cards)
    changes = load_score_changes(run_dir)
    original = rebuild_original(corrected, changes)
    # Only judge review changes were prompted by the judge, so only they are
    # marked in the disagreements.
    corrected_pairs = {(c["card_id"], c["field"]) for c in changes if change_kind(c) == "judge review"}

    run_grades = [grades for _, grades in runs]
    for name, grades in zip("AB", run_grades):
        missing = [c for c in cards if c not in grades]
        if missing:
            sys.exit(f"Judge run {name} has no grade for {len(missing)} card(s), starting with {missing[0]}.")
    seeded_grades = [grades for _, grades in seeded_runs]
    seeded = [score_seeds(seeds, grades) for grades in seeded_grades]
    seed_counts = [seeded_counts(seeds, scored) for scored in seeded]

    comparisons = {
        "corrected": [compare(corrected, g) for g in run_grades],
        "original": [compare(original, g) for g in run_grades],
    }
    checks = {name: build_checks(comparisons[name], seed_counts) for name in comparisons}
    seed_ids = [s["id"] for s in seeds]
    # Discarded runs count toward API calls, the drop rate, and money spent,
    # and toward nothing else: they're never graded or compared.
    passes = [
        retry_stats(name, path)
        for name, path in zip(("Run A", "Run B", "Seeded A", "Seeded B"), [*run_paths, *seeded_paths])
    ] + [
        retry_stats(f"Discarded {n}", path, discarded=True) for n, path in enumerate(discarded_paths, start=1)
    ]
    calls = sum(p["api_calls"] for p in passes)
    data = {
        "judge": {k: infos[0][k] for k in ("scorer", "judge_model", "judge_prompt_version", "effort", "judge_hash")},
        "hand_scores_file": infos[0]["base_run_dir"] + "/scores.csv",
        "runs": [info["judge_run_id"] for info, _ in runs],
        "seeded_runs": [info["judge_run_id"] for info, _ in seeded_runs],
        "costs": [info["metrics"]["total_cost_usd"] for info in infos],
        "retries": {
            "passes": passes,
            "total_retries": sum(p["retries"] for p in passes),
            # Responses that didn't match the batch (such as a grade list
            # that stops short), as a share of every API call, including
            # discarded runs.
            "drop_rate": rate(sum(len(p["invalid_outputs"]) for p in passes), calls),
        },
        "total_spent_usd": sum(p["cost_usd"] for p in passes),
        "score_changes": changes,
        "score_change_counts": {kind: sum(change_kind(c) == kind for c in changes) for kind in CHANGE_KINDS},
        "validated": {name: is_validated(checks[name]) for name in checks},
        "checks": checks,
        "comparisons": comparisons,
        "seeds": seeds,
        "seeded": seeded,
        "seeded_counts": seed_counts,
        "consistency": {
            "runs": consistency(run_grades[0], run_grades[1], list(cards)),
            "seeded": consistency(
                {s: seeded_grades[0][s] for s in seed_ids}, {s: seeded_grades[1][s] for s in seed_ids}, seed_ids
            ),
        },
        "disagreements": list_disagreements(corrected, notes, run_grades, cards, corrected_pairs),
        "agreement": check_agreement_sample(Path(agreement_path), original, run_grades) if agreement_path else None,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", data["judge"]["scorer"])
    write_report(output_dir / f"{name}.md", data)
    write_json(output_dir / f"{name}.json", data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare LLM judge runs with the hand scores and decide whether the judge is validated.")
    parser.add_argument("--runs", nargs=2, required=True, metavar=("RUN_A", "RUN_B"), help="two judge run folders on Run 1")
    parser.add_argument("--seeded", nargs=2, required=True, metavar=("SEEDED_A", "SEEDED_B"), help="two seeded judge run folders")
    parser.add_argument(
        "--discarded", nargs="+", default=[], metavar="RUN",
        help="incomplete or interrupted judge runs of the same judge; counted toward API calls, "
        "the drop rate, and money spent, never graded",
    )
    parser.add_argument(
        "--agreement-sample", metavar="CSV",
        help="a blind recheck of pairs where the hand score and both judge runs agreed, with its seed in the "
        ".md file beside it; reported, never part of the verdict",
    )
    args = parser.parse_args()

    data = validate([Path(p) for p in args.runs], [Path(p) for p in args.seeded],
                    discarded_paths=[Path(p) for p in args.discarded],
                    agreement_path=Path(args.agreement_sample) if args.agreement_sample else None)
    corrected, original = data["validated"]["corrected"], data["validated"]["original"]
    if corrected != original:
        print(f"NOTE: the verdict differs: {verdict_text(corrected)} against the corrected scores, "
              f"{verdict_text(original)} against the original ones.")
    print(f"Verdict (corrected hand scores): {verdict_text(corrected)}")
    print(f"Retries: {data['retries']['total_retries']}, drop rate {format_rate(data['retries']['drop_rate'])}")
    for check in data["checks"]["corrected"]:
        if not all(check["passed"]):
            print(f"  FAIL {check['check']}: {', '.join(check['values'])} (needs {check['threshold']})")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", data["judge"]["scorer"])
    print(f"Report written to {(VALIDATION_DIR / f'{name}.md').relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
