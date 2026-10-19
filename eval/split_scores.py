#!/usr/bin/env python3
"""Split scoring: judge v1 grades atomic, supported, no leakage, and duplicates; a person scores unambiguous.

Judge v1 wasn't validated (it failed only on unambiguous catches), so its
unambiguous grades are never used. One subcommand per step:

    sheet   Writes split/unambiguous_sheet.csv in the run folder, for scoring
            unambiguous by hand from the question and answer alone.
    review  Writes split/<judge_run_id>/review_fails.csv, every pair the judge
            failed with its reason, and review_passes.csv, a blind, seeded
            sample of the pairs it passed.
    merge   Combines the judge's four criteria, with the review changes in
            split/<judge_run_id>/score_changes.csv applied, and the hand-scored
            unambiguous column into split_scores.csv, for score_run.py.

Uses only the standard library and makes no API calls. See eval/README.md,
"Split scoring".

Usage:
    .venv/bin/python eval/split_scores.py sheet <run>
    .venv/bin/python eval/split_scores.py review --judge-run <judge_run> <run>
    .venv/bin/python eval/split_scores.py merge --judge-run <judge_run> <run>
"""
import argparse
import csv
import hashlib
import os
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path

from score_run import CRITERIA, REPO_ROOT, check_run_validity, load_json, read_scores, write_json
from validate_judge import VALIDATION_RUBRIC_VERSION, VALIDATION_RUN_ID, VALIDATION_TEST_SET_VERSION

# The only judge whose grades split scoring uses (README, "Split scoring"). A
# judge with any other hash is a different judge.
JUDGE_V1_HASH = "d21413e84dec"
# The judge's criteria under split scoring, in sheet order, and the scores
# file column each one is stored in. Unambiguous is scored by hand.
JUDGE_LABELS = ["atomic", "supported", "no_leakage", "duplicate"]
FIELDS = {"atomic": "atomic", "supported": "supported", "no_leakage": "no_leakage", "duplicate": "duplicate_of"}
RUBRIC_RULES = {
    "atomic": "Atomic", "supported": "Supported", "no_leakage": "No Answer Leakage", "duplicate": "No Near-Duplicates",
}
PASS_SAMPLE_PER_LABEL = 5
# A pass sample decision that a card isn't a duplicate, so a blank decision
# always means it hasn't been filled in.
NOT_DUPLICATE = "none"
REVIEW_PROMPTED_BY = "review"
FROM_HAND_PROVENANCE = "from hand scores"

SPLIT_DIR = "split"
UNAMBIGUOUS_SHEET = "unambiguous_sheet.csv"
REVIEW_FAILS = "review_fails.csv"
REVIEW_PASSES = "review_passes.csv"
REVIEW_PASSES_NOTES = "review_passes.md"
CHANGE_LOG = "score_changes.csv"
MERGED_SCORES = "split_scores.csv"
MERGED_INFO = "split_scores.json"

UNAMBIGUOUS_COLUMNS = ["card_id", "question", "answer", "unambiguous", "note"]
FAILS_COLUMNS = ["card_id", "criterion", "judge_score", "question", "answer", "original_card", "judge_reason",
                 "decision", "decision_reason"]
PASSES_COLUMNS = ["card_id", "criterion", "question", "answer", "decision", "decision_reason"]
CHANGE_LOG_COLUMNS = ["date", "card_id", "field", "old", "new", "prompted_by", "rubric_rule", "reason", "provenance"]
MERGED_COLUMNS = ["card_id", "sample_id", "category", "question", "answer", *CRITERIA, "duplicate_of", "notes"]


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [{k: (v or "").strip() for k, v in row.items() if k is not None} for row in csv.DictReader(f)]
    # Excel sometimes saves trailing rows with every cell empty.
    return [row for row in rows if any(row.values())]


def write_csv(path: Path, columns: list[str], rows: list[list[str]]) -> None:
    # A byte order mark, like scores.csv, so Excel shows non-ASCII characters.
    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    os.replace(temp_path, path)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def display(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def refuse_overwrite(paths: list[Path]) -> None:
    # These files hold a person's scores or decisions, so they're never rewritten.
    existing = [p for p in paths if p.exists()]
    if existing:
        sys.exit("Not overwriting files that may hold your scores or decisions:\n"
                 + "\n".join(f"- {display(p)}" for p in existing))


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_run(run_dir: Path) -> tuple[dict, dict]:
    """Returns run.json and the Stage 2 cards by ID, in results.json order."""
    if not run_dir.is_dir():
        sys.exit(f"{run_dir} is not a folder.")
    run_info = load_json(run_dir / "run.json")
    records = load_json(run_dir / "results.json")
    problems = check_run_validity(run_info, records)
    if problems:
        sys.exit("The run can't be split-scored:\n" + "\n".join(f"- {p}" for p in problems))
    cards = {
        card["card_id"]: {
            "sample_id": r["id"], "index": index, "tags": r["tags"],
            "question": card["question"], "answer": card["answer"],
        }
        for r in records if r["scored_in_stage2"]
        for index, card in enumerate(r["cards"])
    }
    return run_info, cards


def judge_value(grade: dict, label: str) -> str:
    # Y or N, or for duplicates the earlier card's ID ("" for none), as the
    # change log stores them.
    return (grade["duplicate_of"] or "") if label == "duplicate" else grade[label]


def load_judge_run(path: Path, run_dir: Path, cards: dict) -> tuple[dict, dict]:
    """Returns a judge v1 run of this run's cards and its grades by card ID. Exits on any problem."""
    info = load_json(path / "judge_run.json")
    problems = []
    if info.get("mode") != "run":
        problems.append(f"{display(path)} is a {info.get('mode')} judge run, not a judge run of a run's cards.")
    for flag in ("partial", "interrupted", "incomplete"):
        if info.get(flag) is not False:
            problems.append(f"{display(path)} is marked {flag}.")
    if info.get("judge_hash") != JUDGE_V1_HASH:
        problems.append(
            f"{display(path)} has judge hash {info.get('judge_hash')}; split scoring uses only judge v1 "
            f"({JUDGE_V1_HASH})."
        )
    # Recorded relative to the repo root (absolute only for a run outside it).
    if (REPO_ROOT / info.get("base_run_dir", "")).resolve() != run_dir.resolve():
        problems.append(f"{display(path)} judged {info.get('base_run_dir')}, not {display(run_dir)}.")
    if problems:
        sys.exit("Can't use this judge run:\n" + "\n".join(f"- {p}" for p in problems))
    grades = {g["card_id"]: g for record in load_json(path / "judge_results.json") for g in record["grades"]}
    missing = [c for c in cards if c not in grades]
    if missing:
        sys.exit(f"{display(path)} has no grade for {len(missing)} card(s), starting with {missing[0]}.")
    return info, grades


def unambiguous_path(args, run_dir: Path) -> Path:
    return Path(args.unambiguous) if args.unambiguous else run_dir / SPLIT_DIR / UNAMBIGUOUS_SHEET


def read_unambiguous(path: Path, cards: dict) -> dict:
    """Returns the hand-scored unambiguous column by card ID. Exits until every card has a Y or N."""
    if not path.exists():
        sys.exit(f"Missing {display(path)}. Write it with: split_scores.py sheet <run>")
    rows = read_csv(path)
    if rows and not {"card_id", "unambiguous"} <= rows[0].keys():
        sys.exit(f"{display(path)} needs card_id and unambiguous columns.")
    problems, scores, seen = [], {}, set()
    for row in rows:
        card_id, value = row["card_id"], row["unambiguous"]
        if card_id not in cards:
            problems.append(f"{card_id or '(blank card_id)'} is not a card scored in Stage 2.")
            continue
        if card_id in seen:
            problems.append(f"{card_id} has more than one row.")
            continue
        seen.add(card_id)
        if not value:
            problems.append(f"{card_id}: unambiguous is blank.")
        elif value not in ("Y", "N"):
            problems.append(f"{card_id}: unambiguous is '{value}', expected Y or N.")
        else:
            scores[card_id] = value
    problems += [f"{c} has no row." for c in cards if c not in seen]
    if problems:
        sys.exit(f"{display(path)} isn't complete ({len(problems)} problem(s)):\n"
                 + "\n".join(f"- {p}" for p in problems))
    return scores


def read_hand_labels(run_dir: Path, cards: dict) -> dict:
    """The run's scores.csv as change log values, for --decisions-from-hand."""
    parsed, problems = read_scores(run_dir / "scores.csv", cards)
    if problems:
        sys.exit("scores.csv has problems:\n" + "\n".join(f"- {p}" for p in problems))
    return {
        card_id: {**{k: "Y" if s[k] else "N" for k in CRITERIA}, "duplicate": s["duplicate_of"] or ""}
        for card_id, s in parsed.items()
    }


# ---------------------------------------------------------------------------
# Review sample
# ---------------------------------------------------------------------------

def failed_pairs(grades: dict, cards: dict) -> list[tuple[str, str]]:
    return [
        (card_id, label) for card_id in cards for label in JUDGE_LABELS
        if judge_value(grades[card_id], label) not in ("Y", "")
    ]


def passed_pairs(grades: dict, cards: dict) -> dict:
    # Every pair the judge passed, by criterion, including pairs on cards it
    # failed on another criterion: a miss there still lowers that
    # criterion's rate, and a card that fails something is where the judge
    # is most likely to be wrong elsewhere.
    failed = set(failed_pairs(grades, cards))
    return {label: [c for c in cards if (c, label) not in failed] for label in JUDGE_LABELS}


def draw_pass_sample(seed: int, pools: dict) -> list[tuple[str, str]]:
    short = [label for label in JUDGE_LABELS if len(pools[label]) < PASS_SAMPLE_PER_LABEL]
    if short:
        sys.exit(f"Too few passed pairs to sample {PASS_SAMPLE_PER_LABEL} for: {', '.join(short)}.")
    rng = random.Random(seed)
    return [
        (card_id, label) for label in JUDGE_LABELS
        for card_id in sorted(rng.sample(sorted(pools[label]), PASS_SAMPLE_PER_LABEL))
    ]


def read_seed(path: Path) -> int:
    match = re.search(r"\*\*Random seed:\*\*\s*(\d+)", path.read_text(encoding="utf-8")) if path.exists() else None
    if not match:
        sys.exit(f"{display(path)} doesn't record the pass sample's random seed.")
    return int(match.group(1))


def check_validation_run(run_info: dict) -> None:
    # Every card of the validation run is already hand-scored, so its review
    # decisions can be read from scores.csv. Any other run is reviewed by hand.
    found = (run_info["run_id"], run_info["rubric_version"], run_info.get("test_set_version"))
    if found != (VALIDATION_RUN_ID, VALIDATION_RUBRIC_VERSION, VALIDATION_TEST_SET_VERSION):
        sys.exit(
            f"--decisions-from-hand is only for run {VALIDATION_RUN_ID} under rubric {VALIDATION_RUBRIC_VERSION} "
            f"and test set {VALIDATION_TEST_SET_VERSION}, where every card is already hand-scored."
        )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_sheet(args) -> None:
    run_dir = Path(args.run_dir)
    _, cards = load_run(run_dir)
    path = run_dir / SPLIT_DIR / UNAMBIGUOUS_SHEET
    refuse_overwrite([path])
    path.parent.mkdir(exist_ok=True)
    # No hand-scoring notes and no judge grades, so the score is blind.
    write_csv(path, UNAMBIGUOUS_COLUMNS, [[c, card["question"], card["answer"], "", ""] for c, card in cards.items()])
    print(f"Wrote {display(path)} ({len(cards)} cards). Score unambiguous from the question and answer alone, "
          "before opening any judge output.")


def cmd_review(args) -> None:
    run_dir = Path(args.run_dir)
    run_info, cards = load_run(run_dir)
    judge_info, grades = load_judge_run(Path(args.judge_run), run_dir, cards)
    read_unambiguous(unambiguous_path(args, run_dir), cards)
    if args.decisions_from_hand:
        check_validation_run(run_info)

    out_dir = run_dir / SPLIT_DIR / judge_info["judge_run_id"]
    outputs = [out_dir / REVIEW_FAILS, out_dir / REVIEW_PASSES, out_dir / REVIEW_PASSES_NOTES]
    refuse_overwrite(outputs + ([out_dir / CHANGE_LOG] if args.decisions_from_hand else []))
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(10**7, 10**8)
    pools = passed_pairs(grades, cards)
    fails, sample = failed_pairs(grades, cards), draw_pass_sample(seed, pools)
    hand = read_hand_labels(run_dir, cards) if args.decisions_from_hand else None
    today = date.today().isoformat()

    fail_rows, pass_rows, changes = [], [], []

    def change(card_id, label, old, new, reason):
        changes.append([today, card_id, FIELDS[label], old, new, REVIEW_PROMPTED_BY,
                        f"Rubric {run_info['rubric_version']}, {RUBRIC_RULES[label]}", reason, FROM_HAND_PROVENANCE])

    for card_id, label in fails:
        card, old = cards[card_id], judge_value(grades[card_id], label)
        original = cards.get(old) if label == "duplicate" else None
        decision = reason = ""
        if hand:
            new = hand[card_id][label]
            decision = "keep" if new == old else "change"
            reason = f"From the corrected hand score in scores.csv: {new or NOT_DUPLICATE}."
            if decision == "change":
                change(card_id, label, old, new, reason)
        fail_rows.append([
            card_id, label, old, card["question"], card["answer"],
            f"{old}: {original['question']} / {original['answer']}" if original else "",
            grades[card_id]["reasons"].get(label) or "", decision, reason,
        ])
    for card_id, label in sample:
        card, decision, reason = cards[card_id], "", ""
        if hand:
            new = hand[card_id][label]
            decision = (new or NOT_DUPLICATE) if label == "duplicate" else new
            reason = "From the corrected hand score in scores.csv."
            if new != judge_value(grades[card_id], label):
                change(card_id, label, judge_value(grades[card_id], label), new, reason)
        # No judge grade or reason: this sheet is scored blind.
        pass_rows.append([card_id, label, card["question"], card["answer"], decision, reason])

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / REVIEW_FAILS, FAILS_COLUMNS, fail_rows)
    write_csv(out_dir / REVIEW_PASSES, PASSES_COLUMNS, pass_rows)
    if hand:
        write_csv(out_dir / CHANGE_LOG, CHANGE_LOG_COLUMNS, changes)
    (out_dir / REVIEW_PASSES_NOTES).write_text("\n".join([
        f"# Pass Sample: {judge_info['judge_run_id']}",
        "",
        f"`{REVIEW_PASSES}` is a blind check of card+criterion pairs that judge run {judge_info['judge_run_id']}",
        "passed, on any card and any of its four criteria (atomic, supported, no leakage, and duplicates). It's",
        "there to catch a judge that does badly on new kinds of cards. It doesn't measure how often the judge",
        "misses, because 20 pairs can't pin down a low miss rate. The judge's grades are left out so the check",
        "is blind.",
        "",
        f"- **Random seed:** {seed}",
        f"- **Drawn:** {today}",
        f"- **Run:** {display(run_dir)}",
        f"- **Judge run:** {judge_info['judge_run_id']} (judge hash {judge_info['judge_hash']})",
        f"- **Population:** every pair the judge passed, out of {len(cards)} cards per criterion: "
        + ", ".join(f"{label} {len(pools[label])}" for label in JUDGE_LABELS),
        f"- **Sample:** {PASS_SAMPLE_PER_LABEL} per criterion, drawn in the order {', '.join(JUDGE_LABELS)} from one",
        f"  `random.Random({seed})`, each with `rng.sample(sorted(pool), {PASS_SAMPLE_PER_LABEL})`, then sorted by",
        "  card ID within the criterion. A card can be drawn for more than one criterion.",
        f"- **Decisions:** `Y` or `N`; for duplicate, the ID of the earlier card it duplicates, or `{NOT_DUPLICATE}`.",
        *([f"- **Decisions filled from hand scores:** `--decisions-from-hand`, from the corrected",
           f"  `scores.csv`, which already covers every card of this run."] if hand else []),
        "",
    ]), encoding="utf-8")

    print(f"{len(fail_rows)} failed pair(s) in {display(out_dir / REVIEW_FAILS)}")
    print(f"{len(pass_rows)} sampled pass pair(s) in {display(out_dir / REVIEW_PASSES)} (seed {seed})")
    if hand:
        print(f"{len(changes)} change(s) from hand scores in {display(out_dir / CHANGE_LOG)}")


def check_review(fails: list[dict], passes: list[dict], sample: list, changes: list[dict],
                 labels: dict, grades: dict, cards: dict) -> list[str]:
    """Problems with the review sheets and the change log, which must match exactly."""
    problems = []
    expected_fails = failed_pairs(grades, cards)
    found_fails = [(r["card_id"], r["criterion"]) for r in fails]
    if sorted(found_fails) != sorted(expected_fails):
        problems.append(f"{REVIEW_FAILS} doesn't list exactly the pairs the judge failed.")
    found_sample = [(r["card_id"], r["criterion"]) for r in passes]
    if sorted(found_sample) != sorted(sample):
        problems.append(f"{REVIEW_PASSES} doesn't match the sample drawn from the seed in {REVIEW_PASSES_NOTES}.")

    logged = {}
    for row in changes:
        key = (row["card_id"], next((label for label, field in FIELDS.items() if field == row["field"]), None))
        if key[1] is None:
            problems.append(f"{CHANGE_LOG}: {row['card_id']} field '{row['field']}' isn't one of the judge's criteria.")
        elif key in logged:
            problems.append(f"{CHANGE_LOG}: {row['card_id']} {row['field']} is changed more than once.")
        elif row["prompted_by"] != REVIEW_PROMPTED_BY:
            problems.append(f"{CHANGE_LOG}: {row['card_id']} {row['field']} has prompted_by '{row['prompted_by']}', "
                            f"expected '{REVIEW_PROMPTED_BY}'.")
        elif key[0] not in labels or row["old"] != labels[key[0]][key[1]]:
            problems.append(f"{CHANGE_LOG}: {row['card_id']} {row['field']} old value '{row['old']}' isn't the judge's grade.")
        elif row["new"] == row["old"]:
            problems.append(f"{CHANGE_LOG}: {row['card_id']} {row['field']} doesn't change anything.")
        elif key[1] != "duplicate" and row["new"] not in ("Y", "N"):
            problems.append(f"{CHANGE_LOG}: {row['card_id']} {row['field']} new value is '{row['new']}', expected Y or N.")
        else:
            logged[key] = row["new"]

    reviewed = set()
    for row in fails:
        key = (row["card_id"], row["criterion"])
        if key not in expected_fails:
            continue  # already reported above
        reviewed.add(key)
        if row["decision"] not in ("keep", "change"):
            problems.append(f"{REVIEW_FAILS}: {key[0]} {key[1]} decision is '{row['decision']}', expected keep or change.")
        elif (row["decision"] == "change") != (key in logged):
            problems.append(f"{REVIEW_FAILS}: {key[0]} {key[1]} is '{row['decision']}', but the change log "
                            f"{'has a' if key in logged else 'has no'} change for it.")
    for row in passes:
        key = (row["card_id"], row["criterion"])
        if key not in sample:
            continue  # already reported above
        reviewed.add(key)
        decision = row["decision"]
        if key[1] == "duplicate":
            valid = decision == NOT_DUPLICATE or decision in cards
            new = "" if decision == NOT_DUPLICATE else decision
        else:
            valid, new = decision in ("Y", "N"), decision
        if not valid:
            problems.append(f"{REVIEW_PASSES}: {key[0]} {key[1]} decision is '{decision}'.")
        elif new != labels[key[0]][key[1]] and logged.get(key) != new:
            problems.append(f"{REVIEW_PASSES}: {key[0]} {key[1]} is scored '{decision}', but the change log doesn't "
                            "change it to that.")
        elif new == labels[key[0]][key[1]] and key in logged:
            problems.append(f"{REVIEW_PASSES}: {key[0]} {key[1]} agrees with the judge, but the change log changes it.")
    problems += [f"{CHANGE_LOG}: {c} {l} isn't in either review sheet." for c, l in logged if (c, l) not in reviewed]
    return problems


def cmd_merge(args) -> None:
    run_dir = Path(args.run_dir)
    run_info, cards = load_run(run_dir)
    judge_info, grades = load_judge_run(Path(args.judge_run), run_dir, cards)
    unambiguous_file = unambiguous_path(args, run_dir)
    unambiguous = read_unambiguous(unambiguous_file, cards)
    out_dir = run_dir / SPLIT_DIR / judge_info["judge_run_id"]
    for name in (REVIEW_FAILS, REVIEW_PASSES):
        if not (out_dir / name).exists():
            sys.exit(f"Missing {display(out_dir / name)}. Write the review sheets with: split_scores.py review")
    seed = read_seed(out_dir / REVIEW_PASSES_NOTES)
    change_log = out_dir / CHANGE_LOG
    changes = read_csv(change_log) if change_log.exists() else []

    labels = {c: {label: judge_value(grades[c], label) for label in JUDGE_LABELS} for c in cards}
    sample = draw_pass_sample(seed, passed_pairs(grades, cards))
    problems = check_review(read_csv(out_dir / REVIEW_FAILS), read_csv(out_dir / REVIEW_PASSES), sample,
                            changes, labels, grades, cards)
    if problems:
        sys.exit(f"Can't merge ({len(problems)} problem(s)). Nothing was written.\n"
                 + "\n".join(f"- {p}" for p in problems))

    changed = {}
    for row in changes:
        label = next(label for label, field in FIELDS.items() if field == row["field"])
        labels[row["card_id"]][label] = row["new"]
        changed.setdefault(row["card_id"], []).append(row["field"])
    rows = [
        [card_id, card["sample_id"], ", ".join(card["tags"]), card["question"], card["answer"],
         labels[card_id]["atomic"], labels[card_id]["supported"], labels[card_id]["no_leakage"],
         unambiguous[card_id], labels[card_id]["duplicate"],
         f"changed in review: {', '.join(changed[card_id])}" if card_id in changed else ""]
        for card_id, card in cards.items()
    ]
    # Checked with score_run.py's own validator before it replaces anything,
    # so a changed duplicate_of must still be an earlier card in the batch.
    scores_path = out_dir / MERGED_SCORES
    check_path = out_dir / (MERGED_SCORES + ".check")
    write_csv(check_path, MERGED_COLUMNS, rows)
    _, score_problems = read_scores(check_path, cards)
    if score_problems:
        check_path.unlink()
        sys.exit("The merged scores aren't valid:\n" + "\n".join(f"- {p}" for p in score_problems))
    os.replace(check_path, scores_path)

    inputs = {
        "judge_results": Path(args.judge_run) / "judge_results.json",
        "unambiguous": unambiguous_file,
        "review_fails": out_dir / REVIEW_FAILS,
        "review_passes": out_dir / REVIEW_PASSES,
        **({"score_changes": change_log} if change_log.exists() else {}),
    }
    scorer = f"{judge_info['scorer']}+hand"
    write_json(out_dir / MERGED_INFO, {
        "run_id": run_info["run_id"],
        "rubric_version": run_info["rubric_version"],
        "test_set_version": run_info.get("test_set_version"),
        "scorer": scorer,
        "judge_run_id": judge_info["judge_run_id"],
        "judge_hash": judge_info["judge_hash"],
        "judge_criteria": [FIELDS[label] for label in JUDGE_LABELS],
        "hand_criteria": ["unambiguous"],
        "pass_sample_seed": seed,
        "failed_pairs": len(failed_pairs(grades, cards)),
        "sampled_pass_pairs": len(sample),
        "review_changes": len(changes),
        "inputs": {name: {"path": display(path), "sha256": file_hash(path)} for name, path in inputs.items()},
        "merged_at": datetime.now().isoformat(timespec="seconds"),
    })
    print(f"Merged {len(cards)} cards with {len(changes)} review change(s) into {display(scores_path)}")
    print("Log it with:")
    print(f"  .venv/bin/python eval/score_run.py --scorer {scorer} \\\n"
          f"      --scores {display(scores_path)} {display(run_dir)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Split scoring: judge v1 for four criteria, unambiguous by hand.")
    commands = parser.add_subparsers(dest="command", required=True)

    sheet = commands.add_parser("sheet", help="write the sheet for scoring unambiguous by hand")
    sheet.add_argument("run_dir")
    sheet.set_defaults(handler=cmd_sheet)

    for name, handler, help_text in (
        ("review", cmd_review, "write the review sheets for a judge run"),
        ("merge", cmd_merge, "merge the judge's grades, the review changes, and the hand unambiguous scores"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("run_dir")
        command.add_argument("--judge-run", required=True, help="the judge run folder, in the run's judge/ folder")
        command.add_argument("--unambiguous", metavar="CSV",
                             help=f"the hand unambiguous scores (default: {SPLIT_DIR}/{UNAMBIGUOUS_SHEET})")
        command.set_defaults(handler=handler)
        if name == "review":
            command.add_argument("--seed", type=int, help="the pass sample's random seed (default: drawn at random)")
            command.add_argument(
                "--decisions-from-hand", action="store_true",
                help=f"fill in the decisions from scores.csv; only for run {VALIDATION_RUN_ID}, which is fully hand-scored",
            )

    args = parser.parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
