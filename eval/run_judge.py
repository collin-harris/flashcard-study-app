#!/usr/bin/env python3
"""Scores a run's cards with the LLM judge.

The judge grades the judgment-based criteria in eval/rubric.md (atomic,
supported, no leakage, unambiguous, and near-duplicates) for every card
scored in Stage 2. The input gate, card count, and source check are computed
by run_eval.py and recompute_run.py, so the judge doesn't score them. It makes
one call per sample, with the sample's notes and all of its cards, and never
sees the hand scores or their notes, the cards' source excerpts, or the
automated source check.

Writes a judge run folder inside the run folder, judge/<judge_run_id>/
(judge/partial/<judge_run_id>/ for a --samples run), with judge_run.json,
judge_results.json, judge_summary.md, and, for a complete run,
judge_scores.csv in the same format as scores.csv, for score_run.py. It never
writes scores.csv.

With --seeded, it judges the seeded examples in eval/judge/seeded_examples.json
instead. Each seed is placed in a copy of its sample's batch from the given
run, one seed per call, and the output goes to eval/judge/seeded_runs/.

Requires ANTHROPIC_API_KEY, like run_eval.py. See eval/README.md.

Usage:
    .venv/bin/python eval/run_judge.py eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
    .venv/bin/python eval/run_judge.py --samples sample_001,sample_018 eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
    .venv/bin/python eval/run_judge.py --seeded eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import anthropic
from dotenv import dotenv_values

from score_run import CRITERIA, README_PATH, RUBRIC_PATH, check_run_validity, format_rate, rate, read_version, write_json

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "eval"
JUDGE_DIR = EVAL_DIR / "judge"
TEST_SET_PATH = EVAL_DIR / "test_set" / "test_set.json"
SEEDED_EXAMPLES_PATH = JUDGE_DIR / "seeded_examples.json"
SEEDED_RUNS_DIR = JUDGE_DIR / "seeded_runs"
ENV_PATH = REPO_ROOT / ".env"

# Every judge run records these settings in its judge_run.json. The model and
# effort are also covered by the judge hash, since both change the grades.
JUDGE_MODEL = "claude-opus-5-5"
JUDGE_PROMPT_VERSION = "v1"
# Opus 5.5 always thinks; effort is the only control over how much.
JUDGE_EFFORT = "low"
# The scorer label for score_run.py names the judge's model and prompt version.
SCORER = f"judge:opus-5.5:{JUDGE_PROMPT_VERSION}"
# Thinking counts toward max_tokens, so this leaves room for it as well as
# the grades.
MAX_TOKENS = 16000
REQUEST_TIMEOUT_SECONDS = 300
# The SDK's own default, set explicitly as in card_generation.py.
MAX_RETRIES = 2

# Opus 5.5 rates in USD per million tokens, from
# https://platform.claude.com/docs/en/about-claude/pricing (checked 2026-10-12).
# Thinking tokens are billed as output. Cache writes use the 5-minute rate.
INPUT_COST_PER_MTOK = 4.00
CACHE_WRITE_COST_PER_MTOK = 5.00
CACHE_READ_COST_PER_MTOK = 0.20
OUTPUT_COST_PER_MTOK = 20.00

PROMPT_PATH = JUDGE_DIR / f"judge_prompt_{JUDGE_PROMPT_VERSION}.txt"
RUBRIC_MARKER = "{{RUBRIC_CRITERIA}}"
# The judge's definitions are copied from the rubric between these headings:
# the four per-card criteria and near-duplicates, with their examples.
CRITERIA_START = "### Per-card criteria"
CRITERIA_END = "#### 6. Card Count"

# The notes and cards are joined with concatenation, never str.format,
# because notes can contain literal braces.
NOTES_PREFIX = "<notes>\n"
CARDS_PREFIX = "\n</notes>\n\n<cards>\n"
CARDS_SUFFIX = "\n</cards>"

REASON_KEYS = [*CRITERIA, "duplicate"]
ERROR_KINDS = ("api_error", "truncated", "refusal", "invalid_output", "unexpected_error")


def _nullable_string() -> dict:
    return {"anyOf": [{"type": "string"}, {"type": "null"}]}


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "cards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    **{criterion: {"type": "string", "enum": ["Y", "N"]} for criterion in CRITERIA},
                    "duplicate_of": _nullable_string(),
                    "reasons": {
                        "type": "object",
                        "properties": {key: _nullable_string() for key in REASON_KEYS},
                        "required": REASON_KEYS,
                        "additionalProperties": False,
                    },
                },
                "required": ["id", *CRITERIA, "duplicate_of", "reasons"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["cards"],
    "additionalProperties": False,
}


class JudgeSetupError(Exception):
    """A problem found before any API call, such as an invalid run folder."""


class JudgeError(Exception):
    # raw_text, metadata, and thinking are set whenever a response actually
    # came back, so a failed call's output and cost can still be recorded.
    def __init__(self, kind: str, message: str, raw_text=None, metadata=None, thinking=None):
        super().__init__(message)
        self.kind = kind
        self.raw_text = raw_text
        self.metadata = metadata
        self.thinking = thinking


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def extract_rubric_criteria(rubric_text: str) -> str:
    # Loaded from the rubric at run time, so the judge's definitions can't
    # drift from the rubric's. Card count stops the extract because it's
    # computed by code.
    lines = rubric_text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == CRITERIA_START]
    ends = [i for i, line in enumerate(lines) if line.strip() == CRITERIA_END]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise JudgeSetupError(
            f"Could not find exactly one '{CRITERIA_START}' heading followed by exactly one "
            f"'{CRITERIA_END}' heading in rubric.md, so the judge's criteria can't be loaded."
        )
    return "\n".join(lines[starts[0]:ends[0]]).strip()


def build_system_prompt(prompt_text: str, criteria: str) -> str:
    if prompt_text.count(RUBRIC_MARKER) != 1:
        raise JudgeSetupError(f"The judge prompt must contain {RUBRIC_MARKER} exactly once.")
    return prompt_text.replace(RUBRIC_MARKER, criteria)


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    criteria = extract_rubric_criteria(RUBRIC_PATH.read_text(encoding="utf-8"))
    return build_system_prompt(PROMPT_PATH.read_text(encoding="utf-8"), criteria)


def compute_judge_hash(system_prompt: str, model: str, effort: str) -> str:
    # Covers everything that can change the grades: the system prompt (which
    # includes the rubric's criteria), the text wrapped around the notes and
    # cards, the output schema, the model, and the effort level. Unlike the
    # generation prompt hash, the model and effort are included, because
    # the hash is what identifies a validated judge. Encoded as a JSON list
    # like the generation prompt hash.
    parts = [system_prompt, NOTES_PREFIX, CARDS_PREFIX, CARDS_SUFFIX, OUTPUT_SCHEMA, model, effort]
    encoded = json.dumps(parts, sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]


def get_judge_hash() -> str:
    return compute_judge_hash(load_system_prompt(), JUDGE_MODEL, JUDGE_EFFORT)


def build_user_message(notes: str, cards: list[dict]) -> tuple[str, dict]:
    """Returns the user message and a map from the judge's card IDs to real ones.

    Cards are renumbered c01, c02, ... in batch order, so sample IDs and
    seed IDs never reach the judge. Only the question and answer are sent;
    the source excerpts are left out.
    """
    shown = [
        {"id": f"c{number:02d}", "question": card["question"], "answer": card["answer"]}
        for number, card in enumerate(cards, start=1)
    ]
    id_map = {item["id"]: card["card_id"] for item, card in zip(shown, cards)}
    message = NOTES_PREFIX + notes + CARDS_PREFIX + json.dumps(shown, indent=2, ensure_ascii=False) + CARDS_SUFFIX
    return message, id_map


# ---------------------------------------------------------------------------
# Calling the judge
# ---------------------------------------------------------------------------

def estimate_cost(input_tokens: int, cache_write_tokens: int, cache_read_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * INPUT_COST_PER_MTOK
        + cache_write_tokens * CACHE_WRITE_COST_PER_MTOK
        + cache_read_tokens * CACHE_READ_COST_PER_MTOK
        + output_tokens * OUTPUT_COST_PER_MTOK
    ) / 1_000_000


def parse_grades(raw_text: str, id_map: dict) -> tuple[list[dict], list[str]]:
    """Checks the judge's output against the batch and maps it back to real card IDs.

    Raises ValueError listing every problem if the output can't be used.
    Returns the grades in batch order, and warnings for problems that don't
    affect the grades (an N or a duplicate with no reason).
    """
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Output is not valid JSON: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("cards"), list):
        raise ValueError("Output has no 'cards' list.")

    position = {judge_id: index for index, judge_id in enumerate(id_map)}
    graded, problems = {}, []
    for item in data["cards"]:
        judge_id = item.get("id") if isinstance(item, dict) else None
        if judge_id not in position:
            problems.append(f"Grade for an unknown card ID: {judge_id!r}.")
            continue
        if judge_id in graded:
            problems.append(f"{judge_id} is graded more than once.")
            continue
        for criterion in CRITERIA:
            if item.get(criterion) not in ("Y", "N"):
                problems.append(f"{judge_id}: {criterion} is {item.get(criterion)!r}, expected Y or N.")
        duplicate_of = item.get("duplicate_of")
        if duplicate_of is not None:
            if duplicate_of not in position:
                problems.append(f"{judge_id}: duplicate_of {duplicate_of!r} is not a card in the batch.")
            elif position[duplicate_of] >= position[judge_id]:
                problems.append(f"{judge_id}: duplicate_of {duplicate_of} is not an earlier card.")
        if not isinstance(item.get("reasons"), dict):
            problems.append(f"{judge_id}: reasons is missing.")
        graded[judge_id] = item
    missing = [judge_id for judge_id in id_map if judge_id not in graded]
    if missing:
        problems.append(f"No grade for {', '.join(missing)}.")
    if problems:
        raise ValueError(" ".join(problems))

    grades, warnings = [], []
    for judge_id, card_id in id_map.items():
        item = graded[judge_id]
        reasons = {key: (item["reasons"].get(key) or "").strip() or None for key in REASON_KEYS}
        for criterion in CRITERIA:
            if item[criterion] == "N" and not reasons[criterion]:
                warnings.append(f"{card_id}: {criterion} is N with no reason.")
        if item["duplicate_of"] and not reasons["duplicate"]:
            warnings.append(f"{card_id}: marked as a duplicate with no reason.")
        grades.append({
            "card_id": card_id,
            **{criterion: item[criterion] for criterion in CRITERIA},
            "duplicate_of": id_map[item["duplicate_of"]] if item["duplicate_of"] else None,
            "reasons": reasons,
        })
    return grades, warnings


def judge_batch(client, notes: str, cards: list[dict]) -> dict:
    """Grades one batch of cards. Raises JudgeError if no usable grades came back."""
    user_message, id_map = build_user_message(notes, cards)

    # Latency covers the whole call, including any automatic SDK retries.
    start = time.perf_counter()
    try:
        response = client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=MAX_TOKENS,
            # The same on every call, so it's cached after the first.
            system=[{"type": "text", "text": load_system_prompt(), "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_message}],
            # A readable summary of the judge's reasoning, saved for reviewing
            # disagreements. Thinking is billed the same either way.
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": JUDGE_EFFORT, "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )
    except anthropic.APITimeoutError as e:
        raise JudgeError("api_error", f"Request timed out: {e}") from e
    except anthropic.APIConnectionError as e:
        raise JudgeError("api_error", f"Could not reach the Anthropic API: {e}") from e
    except anthropic.RateLimitError as e:
        raise JudgeError("api_error", f"Rate limited by the Anthropic API: {e}") from e
    except anthropic.APIStatusError as e:
        raise JudgeError("api_error", f"Anthropic API returned {e.status_code}: {e}") from e
    latency = time.perf_counter() - start

    usage = response.usage
    cache_write = usage.cache_creation_input_tokens or 0
    cache_read = usage.cache_read_input_tokens or 0
    metadata = {
        "model": response.model,
        "input_tokens": usage.input_tokens,
        "cache_write_tokens": cache_write,
        "cache_read_tokens": cache_read,
        "output_tokens": usage.output_tokens,
        "cost_usd": estimate_cost(usage.input_tokens, cache_write, cache_read, usage.output_tokens),
        "latency_seconds": latency,
        "stop_reason": response.stop_reason,
    }
    raw_text = "".join(block.text for block in response.content if block.type == "text")
    thinking = "\n\n".join(block.thinking for block in response.content if block.type == "thinking" and block.thinking)

    # Structured outputs only guarantee valid JSON when generation finishes
    # normally, so these are checked before parsing.
    if response.stop_reason == "max_tokens":
        raise JudgeError("truncated", f"Output hit the {MAX_TOKENS}-token limit before finishing.", raw_text, metadata, thinking)
    if response.stop_reason == "refusal":
        # No fallback model: a refusal is recorded, never re-graded by a
        # different model.
        raise JudgeError("refusal", "The judge declined to respond.", raw_text, metadata, thinking)
    if not response.model.startswith(JUDGE_MODEL):
        raise JudgeError(
            "unexpected_error", f"The response came from {response.model}, not {JUDGE_MODEL}.", raw_text, metadata, thinking
        )

    try:
        grades, warnings = parse_grades(raw_text, id_map)
    except ValueError as e:
        raise JudgeError("invalid_output", f"Output did not match the batch: {e}", raw_text, metadata, thinking) from e
    return {"grades": grades, "warnings": warnings, "raw_text": raw_text, "thinking": thinking, "metadata": metadata}


def judge_item(client, item_id: str, notes: str, cards: list[dict]) -> dict:
    """Grades one batch and returns its record for judge_results.json."""
    record = {
        "id": item_id,
        "outcome": None,  # "judged" or "error"
        "error": None,
        "card_ids": [card["card_id"] for card in cards],
        "grades": [],
        "warnings": [],
        "raw_text": None,
        "thinking": None,
        "metadata": None,
    }
    try:
        result = judge_batch(client, notes, cards)
    except JudgeError as e:
        record.update(outcome="error", error={"kind": e.kind, "message": str(e)},
                      raw_text=e.raw_text, thinking=e.thinking, metadata=e.metadata)
        return record
    except Exception as e:
        # Most likely a bug, but one bad sample shouldn't throw away the
        # results (and cost) of the rest of the run.
        record.update(outcome="error", error={"kind": "unexpected_error", "message": repr(e)})
        return record
    record.update(outcome="judged", grades=result["grades"], warnings=result["warnings"],
                  raw_text=result["raw_text"], thinking=result["thinking"], metadata=result["metadata"])
    return record


# ---------------------------------------------------------------------------
# Loading runs and seeds
# ---------------------------------------------------------------------------

def hash_json(data) -> str:
    # The same hash run_eval.py uses for source_text_hash.
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def load_base_run(run_dir: Path) -> tuple[dict, list[dict], dict]:
    """Loads and checks the run being judged. Returns run.json, results.json, and the notes by sample ID."""
    if not run_dir.is_dir():
        raise JudgeSetupError(f"{run_dir} is not a folder.")
    for name in ("run.json", "results.json"):
        if not (run_dir / name).exists():
            raise JudgeSetupError(f"Missing {run_dir / name}.")
    run_info = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    records = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))

    # The same checks score_run.py makes, since judge scores are logged with it.
    problems = check_run_validity(run_info, records)
    rubric_version = read_version(RUBRIC_PATH, "Rubric Version")
    if run_info.get("rubric_version") != rubric_version:
        problems.append(
            f"The run was made under rubric {run_info.get('rubric_version')}, but rubric.md is now "
            f"{rubric_version}. Recompute it with recompute_run.py and judge the recomputed run."
        )
    test_set_version = read_version(README_PATH, "Test Set Version")
    if run_info.get("test_set_version", "1") != test_set_version:
        problems.append(
            f"The run was made under test set {run_info.get('test_set_version', '1')}, but the test set is "
            f"now {test_set_version}. Recompute it with recompute_run.py and judge the recomputed run."
        )

    # The judge reads the notes from the test set, so they must be the notes
    # the run's cards were generated from.
    samples = {s["id"]: s for s in json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))}
    run_samples = [samples.get(sample_id) for sample_id in run_info.get("sample_ids", [])]
    if None in run_samples:
        problems.append("The run includes samples that are no longer in the test set.")
    elif run_info.get("source_text_hash") != hash_json([[s["id"], s["source_text"]] for s in run_samples]):
        problems.append("The test set's notes no longer match the notes this run was generated from (source_text_hash).")
    if problems:
        raise JudgeSetupError(
            f"The run can't be judged ({len(problems)} problem(s)):\n" + "\n".join(f"- {p}" for p in problems)
        )
    notes = {sample_id: samples[sample_id]["source_text"] for sample_id in run_info["sample_ids"]}
    return run_info, records, notes


def batch_cards(record: dict) -> list[dict]:
    return [{"card_id": c["card_id"], "question": c["question"], "answer": c["answer"]} for c in record["cards"]]


def load_seeds(path: Path, records: list[dict]) -> list[dict]:
    """Loads the seeded examples and builds each one's batch. Raises JudgeSetupError on any problem."""
    seeds = json.loads(path.read_text(encoding="utf-8"))
    batches = {r["id"]: batch_cards(r) for r in records if r["scored_in_stage2"]}
    problems, seen = [], set()
    for seed in seeds:
        seed_id = seed.get("id")
        if seed_id in seen:
            problems.append(f"{seed_id}: duplicate seed ID.")
            continue
        seen.add(seed_id)
        criterion, expected = seed.get("criterion"), seed.get("expected", {})
        if criterion not in (*CRITERIA, "duplicate"):
            problems.append(f"{seed_id}: unknown criterion {criterion!r}.")
            continue
        if any(expected.get(c) not in ("Y", "N") for c in CRITERIA):
            problems.append(f"{seed_id}: expected must give Y or N for {', '.join(CRITERIA)}.")
            continue
        # Exactly one known defect, on the seed's own criterion; none for a control.
        defects = [c for c in CRITERIA if expected[c] == "N"] + (["duplicate"] if expected.get("duplicate_of") else [])
        wanted = [] if seed.get("control") else [criterion]
        if defects != wanted:
            problems.append(f"{seed_id}: expected labels have defects {defects}, but the seed calls for {wanted}.")
        batch = batches.get(seed.get("sample_id"))
        if batch is None:
            problems.append(f"{seed_id}: {seed.get('sample_id')} has no cards scored in Stage 2 in the run.")
            continue
        try:
            seed["batch"] = build_seeded_batch(seed, batch)
        except ValueError as e:
            problems.append(f"{seed_id}: {e}")
            continue
        if expected.get("duplicate_of"):
            ids = [card["card_id"] for card in seed["batch"]]
            if expected["duplicate_of"] not in ids or ids.index(expected["duplicate_of"]) >= ids.index(seed_id):
                problems.append(f"{seed_id}: expected duplicate_of {expected['duplicate_of']} is not an earlier card in its batch.")
    if problems:
        raise JudgeSetupError(f"{path.name} has {len(problems)} problem(s):\n" + "\n".join(f"- {p}" for p in problems))
    return seeds


def build_seeded_batch(seed: dict, batch: list[dict]) -> list[dict]:
    ids = [card["card_id"] for card in batch]
    if seed.get("target_card") not in ids:
        raise ValueError(f"target card {seed.get('target_card')!r} is not in the batch.")
    index = ids.index(seed["target_card"])
    seeded_card = {"card_id": seed["id"], "question": seed["question"], "answer": seed["answer"]}
    if seed.get("action") == "replace":
        return batch[:index] + [seeded_card] + batch[index + 1:]
    if seed.get("action") == "insert_after":
        return batch[:index + 1] + [seeded_card] + batch[index + 1:]
    raise ValueError(f"unknown action {seed.get('action')!r}.")


# ---------------------------------------------------------------------------
# Output files
# ---------------------------------------------------------------------------

def compute_judge_metrics(items: list[dict]) -> dict:
    with_response = [r for r in items if r["metadata"]]
    total_cost = sum(r["metadata"]["cost_usd"] for r in with_response)
    total_latency = sum(r["metadata"]["latency_seconds"] for r in with_response)
    return {
        "calls": len(items),
        "error_rate": rate(sum(r["outcome"] == "error" for r in items), len(items)),
        "cards_judged": sum(len(r["grades"]) for r in items),
        "warnings": sum(len(r["warnings"]) for r in items),
        "total_input_tokens": sum(r["metadata"]["input_tokens"] for r in with_response),
        "total_cache_write_tokens": sum(r["metadata"]["cache_write_tokens"] for r in with_response),
        "total_cache_read_tokens": sum(r["metadata"]["cache_read_tokens"] for r in with_response),
        "total_output_tokens": sum(r["metadata"]["output_tokens"] for r in with_response),
        "total_cost_usd": total_cost,
        "average_cost_usd": total_cost / len(items) if items else None,
        "average_latency_seconds": total_latency / len(with_response) if with_response else None,
    }


def format_reasons(reasons: dict) -> str:
    return " | ".join(f"{key}: {reason}" for key, reason in reasons.items() if reason)


def cell(text) -> str:
    # Keeps a value on one table row: pipes escaped, newlines flattened.
    return "" if text is None else str(text).replace("|", "\\|").replace("\n", " ")


def write_judge_scores_csv(path: Path, records: list[dict], judged: dict) -> None:
    # Same columns and byte order mark as the hand-scoring scores.csv, so
    # score_run.py can read it with --scores. The judge's reasons go in notes.
    grades = {g["card_id"]: g for item in judged.values() for g in item["grades"]}
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
                g = grades[card["card_id"]]
                writer.writerow([
                    card["card_id"], r["id"], ", ".join(r["tags"]), card["question"], card["answer"],
                    *(g[c] for c in CRITERIA), g["duplicate_of"] or "", format_reasons(g["reasons"]),
                ])


def write_judge_summary(path: Path, judge_info: dict, items: list[dict], cards_by_id: dict, seeds=None) -> None:
    metrics = judge_info["metrics"]
    lines = [
        f"# Judge Run {judge_info['judge_run_id']}",
        "",
        f"- **Mode:** {judge_info['mode']}",
        f"- **Judged:** {relative(Path(judge_info['base_run_dir']))}",
        f"- **Scorer:** {judge_info['scorer']} (judge hash {judge_info['judge_hash']}, effort {judge_info['effort']})",
        f"- **Partial:** {'Yes' if judge_info['partial'] else 'No'}",
        f"- **Interrupted:** {'Yes' if judge_info['interrupted'] else 'No'}",
        f"- **Incomplete:** {'Yes' if judge_info['incomplete'] else 'No'} "
        f"(error rate {format_rate(metrics['error_rate'])})",
        f"- **Cost:** ${metrics['total_cost_usd']:.4f} total, "
        f"${metrics['average_cost_usd'] or 0:.4f} per call",
        f"- **Average latency:** {metrics['average_latency_seconds'] or 0:.1f}s",
        f"- **Tokens:** {metrics['total_input_tokens']} input, {metrics['total_cache_write_tokens']} cache write, "
        f"{metrics['total_cache_read_tokens']} cache read, {metrics['total_output_tokens']} output (includes thinking)",
        "",
        "Reasons may refer to cards by the judge's IDs (c01, c02, ...), which number the cards in batch order.",
        "",
    ]
    errored = [r for r in items if r["outcome"] == "error"]
    if errored:
        lines += ["## Errors", "", "| Item | Kind | Message |", "|---|---|---|"]
        lines += [f"| {r['id']} | {r['error']['kind']} | {cell(r['error']['message'])} |" for r in errored]
        lines.append("")
    warnings = [w for r in items for w in r["warnings"]]
    if warnings:
        lines += ["## Warnings", ""] + [f"- {cell(w)}" for w in warnings] + [""]

    lines += ["## Grades", ""]
    header = "| Card | Question | Answer | Atomic | Supported | No leakage | Unambiguous | Duplicate of | Reasons |"
    if seeds is None:
        for r in items:
            if r["outcome"] != "judged":
                continue
            lines += [f"### {r['id']}", "", header, "|---|---|---|---|---|---|---|---|---|"]
            for g in r["grades"]:
                card = cards_by_id[g["card_id"]]
                lines.append(
                    f"| {g['card_id']} | {cell(card['question'])} | {cell(card['answer'])} | "
                    + " | ".join(g[c] for c in CRITERIA)
                    + f" | {g['duplicate_of'] or ''} | {cell(format_reasons(g['reasons']))} |"
                )
            lines.append("")
    else:
        lines += [
            "Only each seed's own card is shown. Expected labels are in `seeded_examples.json`;",
            "`validate_judge.py` compares them.",
            "",
            "| Seed | Criterion | Question | Answer | Atomic | Supported | No leakage | Unambiguous | Duplicate of | Reasons |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in items:
            if r["outcome"] != "judged":
                continue
            seed = seeds[r["id"]]
            g = next(g for g in r["grades"] if g["card_id"] == r["id"])
            lines.append(
                f"| {r['id']} | {seed['criterion']} | {cell(seed['question'])} | {cell(seed['answer'])} | "
                + " | ".join(g[c] for c in CRITERIA)
                + f" | {g['duplicate_of'] or ''} | {cell(format_reasons(g['reasons']))} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Running the judge
# ---------------------------------------------------------------------------

def run_judge(client, run_dir: Path, seeded: bool = False, selected=None, output_root=None) -> Path:
    """Judges a run's cards (or the seeded examples) and writes a judge run folder. Returns the folder."""
    run_info, records, notes = load_base_run(run_dir)
    system_prompt = load_system_prompt()  # fails before any call if the prompt or rubric can't be read

    if seeded:
        seeds = load_seeds(SEEDED_EXAMPLES_PATH, records)
        all_items = [
            {"id": s["id"], "sample_id": s["sample_id"], "cards": s["batch"]} for s in seeds
        ]
    else:
        seeds = None
        all_items = [
            {"id": r["id"], "sample_id": r["id"], "cards": batch_cards(r)} for r in records if r["scored_in_stage2"]
        ]
    items = all_items
    if selected:
        unknown = set(selected) - {item["id"] for item in all_items}
        if unknown:
            kind = "seed" if seeded else "Stage 2 sample"
            raise JudgeSetupError(f"Unknown {kind} IDs: {', '.join(sorted(unknown))}")
        items = [item for item in all_items if item["id"] in selected]

    # A partial judge run (--samples or --seeds) is for smoke testing, never
    # for validation or logging.
    partial = len(items) < len(all_items)
    if output_root is None:
        output_root = SEEDED_RUNS_DIR if seeded else run_dir / "judge"
    now = datetime.now()
    judge_run_id = now.strftime("%Y-%m-%d_%H%M%S")
    out_dir = (output_root / "partial" if partial else output_root) / judge_run_id
    out_dir.mkdir(parents=True)

    judge_info = {
        "judge_run_id": judge_run_id,
        "date": now.isoformat(timespec="seconds"),
        "mode": "seeded" if seeded else "run",
        "scorer": SCORER,
        "judge_model": JUDGE_MODEL,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "judge_hash": compute_judge_hash(system_prompt, JUDGE_MODEL, JUDGE_EFFORT),
        "effort": JUDGE_EFFORT,
        "thinking_display": "summarized",
        "prompt_caching": True,
        "max_tokens": MAX_TOKENS,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "max_retries": MAX_RETRIES,
        "anthropic_sdk_version": anthropic.__version__,
        "rubric_version": run_info["rubric_version"],
        "test_set_version": run_info["test_set_version"],
        "base_run_id": run_info["run_id"],
        "base_run_dir": relative(run_dir),
        "seeded_examples_hash": hash_json(json.loads(SEEDED_EXAMPLES_PATH.read_text(encoding="utf-8"))) if seeded else None,
        "partial": partial,
        # Starts true and is cleared only once every item has been judged and
        # all output is written, as in run_eval.py.
        "interrupted": True,
        "incomplete": None,
        "selected": [item["id"] for item in items],
    }
    write_json(out_dir / "judge_run.json", judge_info)

    results, interrupted = [], False
    try:
        for i, item in enumerate(items, start=1):
            record = judge_item(client, item["id"], notes[item["sample_id"]], item["cards"])
            record["sample_id"] = item["sample_id"]
            results.append(record)
            write_json(out_dir / "judge_results.json", results)

            if record["outcome"] == "error":
                status = f"ERROR ({record['error']['kind']})"
            else:
                fails = sum(g[c] == "N" for g in record["grades"] for c in CRITERIA)
                duplicates = sum(bool(g["duplicate_of"]) for g in record["grades"])
                status = f"{len(record['grades'])} cards, {fails} N, {duplicates} duplicate(s)"
            cost = f" ${record['metadata']['cost_usd']:.4f}" if record["metadata"] else ""
            print(f"[{i}/{len(items)}] {item['id']}: {status}{cost}")
    except KeyboardInterrupt:
        interrupted = True
        print(f"\nInterrupted after {len(results)} of {len(items)} items. Writing results for those.")

    metrics = compute_judge_metrics(results)
    judge_info["interrupted"] = interrupted
    judge_info["incomplete"] = metrics["error_rate"]["count"] > 0
    judge_info["errored"] = [
        {"id": r["id"], "error_kind": r["error"]["kind"], "error_message": r["error"]["message"]}
        for r in results if r["outcome"] == "error"
    ]
    judge_info["metrics"] = metrics

    cards_by_id = {card["card_id"]: card for item in items for card in item["cards"]}
    write_json(out_dir / "judge_results.json", results)
    write_judge_summary(
        out_dir / "judge_summary.md", judge_info, results, cards_by_id,
        seeds={s["id"]: s for s in seeds} if seeds else None,
    )
    # Only a complete judge run of every card has a row for every card, which
    # score_run.py requires.
    if not seeded and not partial and not interrupted and not judge_info["incomplete"]:
        write_judge_scores_csv(out_dir / "judge_scores.csv", records, {r["id"]: r for r in results})
    # Written last, so judge_run.json says the run wasn't interrupted only
    # once every other file is in place.
    write_json(out_dir / "judge_run.json", judge_info)

    print()
    print(f"Error rate: {format_rate(metrics['error_rate'])}")
    print(f"Cards judged: {metrics['cards_judged']}, warnings: {metrics['warnings']}")
    print(f"Total cost: ${metrics['total_cost_usd']:.4f}")
    print(f"Results written to {out_dir}")
    if interrupted or judge_info["incomplete"]:
        print()
        print("WARNING: this judge run is interrupted or incomplete. It can't be validated or logged; rerun it.")
    return out_dir


def load_api_key() -> None:
    # Same as run_eval.py: a key exported in the shell wins, and only
    # ANTHROPIC_API_KEY is read from .env.
    if os.environ.get("ANTHROPIC_API_KEY") or not ENV_PATH.exists():
        return
    key = dotenv_values(ENV_PATH).get("ANTHROPIC_API_KEY")
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a run's cards with the LLM judge.")
    parser.add_argument("run_dir", help="the run folder to judge, e.g. eval/runs/2026-10-02_215109/rescored/rubric-1.6_test-set-2")
    parser.add_argument("--seeded", action="store_true", help="judge the seeded examples, built from this run's batches")
    parser.add_argument("--samples", help="comma-separated sample IDs to judge (default: all); makes a partial run")
    parser.add_argument("--seeds", help="with --seeded, comma-separated seed IDs to judge (default: all); makes a partial run")
    args = parser.parse_args()
    if args.seeds and not args.seeded:
        parser.error("--seeds needs --seeded")
    if args.samples and args.seeded:
        parser.error("--samples doesn't apply with --seeded; use --seeds")
    wanted = args.seeds if args.seeded else args.samples
    selected = {s.strip() for s in wanted.split(",") if s.strip()} if wanted else None

    load_api_key()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Add it to .env at the repo root or export it in this shell.")
    client = anthropic.Anthropic(timeout=REQUEST_TIMEOUT_SECONDS, max_retries=MAX_RETRIES)
    try:
        run_judge(client, Path(args.run_dir), seeded=args.seeded, selected=selected)
    except JudgeSetupError as e:
        sys.exit(f"{e}\n\nNothing was judged.")


if __name__ == "__main__":
    main()
