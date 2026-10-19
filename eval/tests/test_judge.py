"""Offline tests for the LLM judge (run_judge.py), its validation (validate_judge.py), and
scoring corrected hand scores (score_run.py).

Every test uses a stubbed client in place of the Anthropic client, so no API
call is ever made. The end-to-end tests judge a copy of Run 1 (rubric 1.6) in
a temporary folder, so the real run folder is never written to.

Run from the repository root:
    .venv/bin/python -m unittest discover -s eval/tests -v
"""
import contextlib
import csv
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR))

import anthropic  # noqa: E402
import httpx2  # noqa: E402  (the HTTP library anthropic 1.x uses)

import run_judge  # noqa: E402
import score_run  # noqa: E402
import validate_judge  # noqa: E402
from run_judge import CRITERIA, JUDGE_MODEL, JudgeError, JudgeSetupError  # noqa: E402

RUN1_DIR = EVAL_DIR / "runs" / "2026-10-02_215109" / "rescored" / "rubric-1.6_test-set-2"
RUN1_V15_DIR = EVAL_DIR / "runs" / "2026-10-02_215109" / "rescored" / "rubric-1.5_test-set-2"


# ---------------------------------------------------------------------------
# Stubbed client
# ---------------------------------------------------------------------------

DEFAULT_USAGE = {"input_tokens": 600, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 4500, "output_tokens": 900}


def make_response(text: str, model: str = JUDGE_MODEL, stop_reason: str = "end_turn", usage: dict = DEFAULT_USAGE):
    return SimpleNamespace(
        model=model,
        stop_reason=stop_reason,
        usage=SimpleNamespace(**usage),
        content=[
            SimpleNamespace(type="thinking", thinking="Checked each card against the notes."),
            SimpleNamespace(type="text", text=text),
        ],
    )


class FakeClient:
    """Stands in for anthropic.Anthropic. Records every request and answers with respond(request)."""

    def __init__(self, respond):
        self.calls = []

        def create(**kwargs):
            self.calls.append(kwargs)
            return respond(kwargs)

        self.messages = SimpleNamespace(create=create)


def shown_cards(request: dict) -> list[dict]:
    message = request["messages"][0]["content"]
    return json.loads(message.split("<cards>\n", 1)[1].rsplit("\n</cards>", 1)[0])


class Oracle:
    """Grades each card with the labels given for it, found by the card's question and answer."""

    def __init__(self, labels: dict, texts: dict):
        self.labels = labels  # card ID -> {criterion: Y/N, duplicate_of}
        self.ids = texts  # (question, answer) -> card ID

    def __call__(self, request):
        shown = shown_cards(request)
        real_ids = [self.ids[(c["question"], c["answer"])] for c in shown]
        judge_ids = {real: c["id"] for real, c in zip(real_ids, shown)}
        grades = []
        for c, real in zip(shown, real_ids):
            labels = self.labels[real]
            duplicate = judge_ids.get(labels["duplicate_of"]) if labels["duplicate_of"] else None
            grades.append({
                "id": c["id"],
                **{k: labels[k] for k in CRITERIA},
                "duplicate_of": duplicate,
                "reasons": {
                    **{k: f"Fails {k}." if labels[k] == "N" else None for k in CRITERIA},
                    "duplicate": "Tests the same fact." if duplicate else None,
                },
            })
        return make_response(json.dumps({"cards": grades}))


def load_run(run_dir: Path):
    records = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    cards = {
        card["card_id"]: {"sample_id": r["id"], "index": i, "question": card["question"], "answer": card["answer"]}
        for r in records if r["scored_in_stage2"]
        for i, card in enumerate(r["cards"])
    }
    return records, cards


def rewind_to_pre_judge(run_dir: Path) -> None:
    """Reverts the real judge-prompted score changes in a copy of a run, keeping its pre-judge ones.

    The validation tests are written against the scores before any judge
    review, so later corrections to the real scores don't change them.
    """
    _, cards = load_run(run_dir)
    corrected, _ = validate_judge.load_hand_scores(run_dir, cards)
    changes = validate_judge.load_score_changes(run_dir)
    original = validate_judge.rebuild_original(corrected, changes)

    fields, rows = read_csv(run_dir / "scores.csv")
    for row in rows:
        labels = original[row["card_id"]]
        row.update({k: labels[k] for k in CRITERIA}, duplicate_of=labels["duplicate_of"] or "")
    write_csv(run_dir / "scores.csv", fields, rows)

    fields, rows = read_csv(run_dir / "score_changes.csv")
    write_csv(run_dir / "score_changes.csv", fields,
              [row for row in rows if row["prompted_by"].strip() == validate_judge.PRE_JUDGE])


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def oracle_for(run_dir: Path, overrides: dict | None = None) -> Oracle:
    """An oracle that returns the run's hand scores (and each seed's expected labels), with optional overrides."""
    _, cards = load_run(run_dir)
    labels, _ = validate_judge.load_hand_scores(run_dir, cards)
    texts = {(c["question"], c["answer"]): card_id for card_id, c in cards.items()}
    for seed in json.loads(run_judge.SEEDED_EXAMPLES_PATH.read_text(encoding="utf-8")):
        labels[seed["id"]] = dict(seed["expected"])
        texts[(seed["question"], seed["answer"])] = seed["id"]
    for card_id, changes in (overrides or {}).items():
        labels[card_id] = {**labels[card_id], **changes}
    return Oracle(labels, texts)


SAMPLE_005_NOTES = "In ecology, energy flows through ecosystems"


def short_list_first(respond, marker: str, times: int = 1):
    """Wraps a responder so the first `times` requests containing `marker` grade only the first card."""
    shortened = {"count": 0}

    def wrapped(request):
        response = respond(request)
        if marker in request["messages"][0]["content"] and shortened["count"] < times:
            shortened["count"] += 1
            data = json.loads(response.content[1].text)
            data["cards"] = data["cards"][:1]
            return make_response(json.dumps(data))
        return response

    return wrapped


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

class PromptTests(unittest.TestCase):
    def test_criteria_come_from_the_rubric(self):
        criteria = run_judge.extract_rubric_criteria(run_judge.RUBRIC_PATH.read_text(encoding="utf-8"))
        for heading in ("#### 1. Atomic", "#### 2. Supported", "#### 3. No Answer Leakage", "#### 4. Unambiguous",
                        "#### 5. No Near-Duplicates"):
            self.assertIn(heading, criteria)
        self.assertIn("already contained", criteria)  # the rubric 1.6 rule
        self.assertNotIn("Card Count", criteria)
        self.assertNotIn("Source Check", criteria)

    def test_missing_or_repeated_heading_fails(self):
        with self.assertRaises(JudgeSetupError):
            run_judge.extract_rubric_criteria("# A rubric with no criteria headings")
        rubric = run_judge.RUBRIC_PATH.read_text(encoding="utf-8")
        with self.assertRaises(JudgeSetupError):
            run_judge.extract_rubric_criteria(rubric + "\n### Per-card criteria\n")

    def test_criteria_replace_the_marker(self):
        prompt = run_judge.load_system_prompt()
        self.assertNotIn(run_judge.RUBRIC_MARKER, prompt)
        self.assertIn("<rubric>\n### Per-card criteria", prompt)
        with self.assertRaises(JudgeSetupError):
            run_judge.build_system_prompt("no marker", "criteria")
        with self.assertRaises(JudgeSetupError):
            run_judge.build_system_prompt(f"{run_judge.RUBRIC_MARKER} {run_judge.RUBRIC_MARKER}", "criteria")

    def test_hash_covers_prompt_model_and_effort(self):
        prompt = run_judge.load_system_prompt()
        base = run_judge.compute_judge_hash(prompt, JUDGE_MODEL, "low")
        self.assertEqual(base, run_judge.compute_judge_hash(prompt, JUDGE_MODEL, "low"))
        self.assertEqual(base, run_judge.get_judge_hash())
        self.assertNotEqual(base, run_judge.compute_judge_hash(prompt, JUDGE_MODEL, "medium"))
        self.assertNotEqual(base, run_judge.compute_judge_hash(prompt, "claude-sonnet-5", "low"))
        self.assertNotEqual(base, run_judge.compute_judge_hash(prompt + " ", JUDGE_MODEL, "low"))

    def test_judge_v1_is_unchanged(self):
        # Split scoring uses judge v1's grades only while its hash is
        # d21413e84dec (README, "Split scoring"). Editing the prompt, the
        # rubric criteria it loads, the model, or the effort fails this.
        self.assertEqual(run_judge.get_judge_hash(), "d21413e84dec")

    def test_user_message_is_blind(self):
        notes = "int main() { return 0; }"
        cards = [
            {"card_id": "sample_017-c01", "question": "Q1?", "answer": "A1", "source": ["excerpt one"]},
            {"card_id": "seed-x", "question": "Q2?", "answer": "A2", "source": ["excerpt two"]},
        ]
        message, id_map = run_judge.build_user_message(notes, cards)
        self.assertIn(notes, message)  # braces survive
        self.assertEqual(id_map, {"c01": "sample_017-c01", "c02": "seed-x"})
        for hidden in ("sample_", "seed-x", "excerpt", "source"):
            self.assertNotIn(hidden, message)


# ---------------------------------------------------------------------------
# One call
# ---------------------------------------------------------------------------

CARDS = [
    {"card_id": "s-c01", "question": "What is X?", "answer": "X"},
    {"card_id": "s-c02", "question": "Is X Y?", "answer": "No"},
    {"card_id": "s-c03", "question": "What else is X?", "answer": "X"},
]


def grade(judge_id, duplicate_of=None, **labels):
    labels = {**{k: "Y" for k in CRITERIA}, **labels}
    return {
        "id": judge_id, **labels, "duplicate_of": duplicate_of,
        "reasons": {**{k: "Reason." if labels[k] == "N" else None for k in CRITERIA},
                    "duplicate": "Same fact." if duplicate_of else None},
    }


def respond_with(grades, **kwargs):
    return lambda request: make_response(json.dumps({"cards": grades}), **kwargs)


class JudgeBatchTests(unittest.TestCase):
    def test_request_settings(self):
        client = FakeClient(respond_with([grade("c01"), grade("c02"), grade("c03")]))
        run_judge.judge_batch(client, "notes", CARDS)
        request = client.calls[0]
        self.assertEqual(request["model"], "claude-opus-5-5")
        self.assertEqual(request["max_tokens"], run_judge.MAX_TOKENS)
        self.assertEqual(request["output_config"]["effort"], "low")
        self.assertEqual(request["output_config"]["format"], {"type": "json_schema", "schema": run_judge.OUTPUT_SCHEMA})
        self.assertEqual(request["thinking"], {"type": "adaptive", "display": "summarized"})
        self.assertEqual(request["system"][0]["cache_control"], {"type": "ephemeral"})
        # No refusal fallback, betas, or sampling parameters.
        self.assertEqual(set(request), {"model", "max_tokens", "system", "messages", "thinking", "output_config"})

    def test_grades_map_back_to_real_ids(self):
        client = FakeClient(respond_with([grade("c01"), grade("c02", no_leakage="N"), grade("c03", duplicate_of="c01")]))
        result = run_judge.judge_batch(client, "notes", CARDS)
        grades = {g["card_id"]: g for g in result["grades"]}
        self.assertEqual(grades["s-c02"]["no_leakage"], "N")
        self.assertEqual(grades["s-c03"]["duplicate_of"], "s-c01")
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["thinking"], "Checked each card against the notes.")

    def test_grades_in_any_order_are_accepted(self):
        client = FakeClient(respond_with([grade("c03"), grade("c01"), grade("c02")]))
        result = run_judge.judge_batch(client, "notes", CARDS)
        self.assertEqual([g["card_id"] for g in result["grades"]], ["s-c01", "s-c02", "s-c03"])

    def test_cost(self):
        usage = {"input_tokens": 1000, "cache_creation_input_tokens": 4000, "cache_read_input_tokens": 0, "output_tokens": 2000}
        client = FakeClient(respond_with([grade("c01"), grade("c02"), grade("c03")], usage=usage))
        metadata = run_judge.judge_batch(client, "notes", CARDS)["metadata"]
        # $4 input, $5 cache write, $20 output per million tokens.
        self.assertAlmostEqual(metadata["cost_usd"], (1000 * 4 + 4000 * 5 + 2000 * 20) / 1_000_000)
        self.assertEqual(metadata["cache_write_tokens"], 4000)

    def test_invalid_outputs(self):
        cases = {
            "missing card": [grade("c01"), grade("c02")],
            "unknown card": [grade("c01"), grade("c02"), grade("c03"), grade("c04")],
            "graded twice": [grade("c01"), grade("c01"), grade("c02"), grade("c03")],
            "later duplicate": [grade("c01", duplicate_of="c03"), grade("c02"), grade("c03")],
            "self duplicate": [grade("c01"), grade("c02", duplicate_of="c02"), grade("c03")],
            "bad label": [grade("c01", atomic="maybe"), grade("c02"), grade("c03")],
        }
        for name, grades in cases.items():
            with self.subTest(name):
                with self.assertRaises(JudgeError) as caught:
                    run_judge.judge_batch(FakeClient(respond_with(grades)), "notes", CARDS)
                self.assertEqual(caught.exception.kind, "invalid_output")
                self.assertIsNotNone(caught.exception.metadata)  # the call's cost is still recorded
        with self.assertRaises(JudgeError) as caught:
            run_judge.judge_batch(FakeClient(lambda r: make_response("not json")), "notes", CARDS)
        self.assertEqual(caught.exception.kind, "invalid_output")

    def test_stop_reasons_and_model(self):
        ok = [grade("c01"), grade("c02"), grade("c03")]
        for kwargs, kind in (
            ({"stop_reason": "max_tokens"}, "truncated"),
            ({"stop_reason": "refusal"}, "refusal"),
            ({"model": "claude-opus-4-8"}, "unexpected_error"),
        ):
            with self.subTest(kind):
                with self.assertRaises(JudgeError) as caught:
                    run_judge.judge_batch(FakeClient(respond_with(ok, **kwargs)), "notes", CARDS)
                self.assertEqual(caught.exception.kind, kind)

    def test_api_errors(self):
        def fail(request):
            raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))

        with self.assertRaises(JudgeError) as caught:
            run_judge.judge_batch(FakeClient(fail), "notes", CARDS)
        self.assertEqual(caught.exception.kind, "api_error")

    def test_short_grade_list_is_retried_once(self):
        full = [grade("c01"), grade("c02"), grade("c03")]
        client = FakeClient(short_list_first(respond_with(full), "What is X?"))
        record = run_judge.judge_item(client, "s", "notes", CARDS)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual((record["outcome"], record["attempts"]), ("judged", 2))
        self.assertEqual(len(record["grades"]), 3)
        [failed] = record["failed_attempts"]
        self.assertEqual(failed["error"]["kind"], "invalid_output")
        self.assertIn("No grade for c02, c03", failed["error"]["message"])
        self.assertIsNotNone(failed["metadata"])  # the failed attempt's cost is kept
        self.assertEqual(len(run_judge.call_metadata(record)), 2)

    def test_other_errors_are_not_retried(self):
        ok = [grade("c01"), grade("c02"), grade("c03")]

        def fail(request):
            raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"))

        for respond, kind in (
            (respond_with(ok, stop_reason="max_tokens"), "truncated"),
            (respond_with(ok, stop_reason="refusal"), "refusal"),
            (fail, "api_error"),
        ):
            with self.subTest(kind):
                client = FakeClient(respond)
                record = run_judge.judge_item(client, "s", "notes", CARDS)
                self.assertEqual(len(client.calls), 1)
                self.assertEqual((record["outcome"], record["attempts"], record["error"]["kind"]), ("error", 1, kind))
                self.assertEqual(record["failed_attempts"], [])

    def test_missing_reason_is_a_warning(self):
        no_reason = grade("c02", unambiguous="N")
        no_reason["reasons"]["unambiguous"] = None
        result = run_judge.judge_batch(FakeClient(respond_with([grade("c01"), no_reason, grade("c03")])), "notes", CARDS)
        self.assertEqual(result["warnings"], ["s-c02: unambiguous is N with no reason."])


# ---------------------------------------------------------------------------
# Judge runs
# ---------------------------------------------------------------------------

class RunJudgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_complete_run(self):
        before = {name: file_hash(RUN1_DIR / name) for name in ("scores.csv", "results.json", "run.json")}
        client = FakeClient(oracle_for(RUN1_DIR))
        out_dir = quiet(run_judge.run_judge, client, RUN1_DIR, output_root=self.tmp)

        self.assertEqual(len(client.calls), 30)
        info = json.loads((out_dir / "judge_run.json").read_text(encoding="utf-8"))
        self.assertEqual((info["partial"], info["interrupted"], info["incomplete"]), (False, False, False))
        self.assertEqual(info["effort"], "low")
        self.assertEqual(info["judge_hash"], run_judge.get_judge_hash())
        self.assertEqual(info["scorer"], "judge:opus-5.5:v1")
        self.assertEqual(info["metrics"]["cards_judged"], 186)

        # judge_scores.csv passes score_run.py's own validation and matches the oracle's labels.
        _, cards = load_run(RUN1_DIR)
        judge_labels, _ = validate_judge.load_hand_scores(self._as_scores_dir(out_dir), cards)
        hand_labels, _ = validate_judge.load_hand_scores(RUN1_DIR, cards)
        self.assertEqual(judge_labels, hand_labels)
        with (out_dir / "judge_scores.csv").open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
        with (RUN1_DIR / "scores.csv").open(encoding="utf-8-sig", newline="") as f:
            self.assertEqual(header, next(csv.reader(f)))
        self.assertTrue((out_dir / "judge_scores.csv").read_bytes().startswith(b"\xef\xbb\xbf"))

        # The run folder being judged is never written to.
        self.assertEqual(before, {name: file_hash(RUN1_DIR / name) for name in before})

    def _as_scores_dir(self, out_dir: Path) -> Path:
        # load_hand_scores reads scores.csv, so the judge's file is copied under that name in a scratch folder.
        scratch = self.tmp / "as_scores"
        scratch.mkdir(exist_ok=True)
        shutil.copy(out_dir / "judge_scores.csv", scratch / "scores.csv")
        return scratch

    def test_partial_run_writes_no_scores_csv(self):
        out_dir = quiet(run_judge.run_judge, FakeClient(oracle_for(RUN1_DIR)), RUN1_DIR,
                        selected={"sample_001", "sample_018"}, output_root=self.tmp)
        self.assertEqual(out_dir.parent.name, "partial")
        self.assertFalse((out_dir / "judge_scores.csv").exists())
        info = json.loads((out_dir / "judge_run.json").read_text(encoding="utf-8"))
        self.assertTrue(info["partial"])
        self.assertEqual(info["selected"], ["sample_001", "sample_018"])

    def test_errored_sample_makes_the_run_incomplete(self):
        oracle = oracle_for(RUN1_DIR)

        def respond(request):
            if "Python list slicing" in request["messages"][0]["content"]:
                return make_response("{}")
            return oracle(request)

        out_dir = quiet(run_judge.run_judge, FakeClient(respond), RUN1_DIR, output_root=self.tmp)
        info = json.loads((out_dir / "judge_run.json").read_text(encoding="utf-8"))
        self.assertTrue(info["incomplete"])
        self.assertEqual([e["id"] for e in info["errored"]], ["sample_016"])
        self.assertFalse((out_dir / "judge_scores.csv").exists())

    def test_retried_sample_completes_the_run(self):
        client = FakeClient(short_list_first(oracle_for(RUN1_DIR), SAMPLE_005_NOTES))
        out_dir = quiet(run_judge.run_judge, client, RUN1_DIR, output_root=self.tmp)
        self.assertEqual(len(client.calls), 31)
        info = json.loads((out_dir / "judge_run.json").read_text(encoding="utf-8"))
        self.assertEqual((info["incomplete"], info["interrupted"]), (False, False))
        self.assertEqual((info["metrics"]["api_calls"], info["metrics"]["retries"]), (31, 1))
        self.assertEqual(info["metrics"]["retried"], ["sample_005"])
        self.assertEqual(info["max_attempts"], 2)
        # Cost covers every call, including the retried one.
        per_call = run_judge.estimate_cost(600, 0, 4500, 900)
        self.assertAlmostEqual(info["metrics"]["total_cost_usd"], 31 * per_call)
        self.assertTrue((out_dir / "judge_scores.csv").exists())
        results = {r["id"]: r for r in json.loads((out_dir / "judge_results.json").read_text(encoding="utf-8"))}
        self.assertEqual(results["sample_005"]["attempts"], 2)
        self.assertEqual(results["sample_001"]["attempts"], 1)
        self.assertIn("## Retried attempts", (out_dir / "judge_summary.md").read_text(encoding="utf-8"))

    def test_both_attempts_failing_makes_the_run_incomplete(self):
        client = FakeClient(short_list_first(oracle_for(RUN1_DIR), SAMPLE_005_NOTES, times=2))
        out_dir = quiet(run_judge.run_judge, client, RUN1_DIR, output_root=self.tmp)
        self.assertEqual(len(client.calls), 31)  # one retry, then it gives up
        info = json.loads((out_dir / "judge_run.json").read_text(encoding="utf-8"))
        self.assertTrue(info["incomplete"])
        self.assertEqual([e["id"] for e in info["errored"]], ["sample_005"])
        self.assertEqual(info["metrics"]["retries"], 1)
        self.assertFalse((out_dir / "judge_scores.csv").exists())
        results = {r["id"]: r for r in json.loads((out_dir / "judge_results.json").read_text(encoding="utf-8"))}
        record = results["sample_005"]
        self.assertEqual((record["outcome"], record["attempts"], len(record["failed_attempts"])), ("error", 2, 1))
        self.assertEqual(record["error"]["kind"], "invalid_output")

    def test_refuses_a_run_under_an_older_rubric(self):
        with self.assertRaises(JudgeSetupError):
            run_judge.run_judge(FakeClient(oracle_for(RUN1_DIR)), RUN1_V15_DIR, output_root=self.tmp)

    def test_seeded_batches(self):
        records, _ = load_run(RUN1_DIR)
        seeds = {s["id"]: s for s in run_judge.load_seeds(run_judge.SEEDED_EXAMPLES_PATH, records)}
        self.assertEqual(len(seeds), 26)
        ids = lambda seed: [c["card_id"] for c in seeds[seed]["batch"]]  # noqa: E731
        self.assertEqual(ids("sup-1")[-1], "sup-1")  # replaced sample_012-c09, the last card
        self.assertNotIn("sample_012-c09", ids("sup-1"))
        self.assertEqual(ids("dup-6")[-2:], ["sample_009-c09", "dup-6"])
        self.assertEqual(ids("dup-1").index("dup-1"), ids("dup-1").index("sample_029-c03") + 1)
        self.assertEqual(len(ids("dup-1")), 5)  # inserted, nothing removed

    def test_seed_file_problems_are_caught(self):
        records, _ = load_run(RUN1_DIR)
        seeds = json.loads(run_judge.SEEDED_EXAMPLES_PATH.read_text(encoding="utf-8"))
        bad = [dict(s) for s in seeds]
        bad[4] = {**bad[4], "expected": {**bad[4]["expected"], "supported": "N"}}  # sup-5 is a control
        bad[20] = {**bad[20], "target_card": "sample_029-c99"}
        path = self.tmp / "seeds.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(JudgeSetupError) as caught:
            run_judge.load_seeds(path, records)
        self.assertIn("sup-5", str(caught.exception))
        self.assertIn("dup-1", str(caught.exception))

    def test_seeded_run(self):
        client = FakeClient(oracle_for(RUN1_DIR))
        out_dir = quiet(run_judge.run_judge, client, RUN1_DIR, seeded=True, output_root=self.tmp)
        self.assertEqual(len(client.calls), 26)
        info = json.loads((out_dir / "judge_run.json").read_text(encoding="utf-8"))
        self.assertEqual(info["mode"], "seeded")
        self.assertFalse((out_dir / "judge_scores.csv").exists())
        # Seed IDs never reach the judge.
        self.assertFalse(any("dup-" in c["messages"][0]["content"] for c in client.calls))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        # A copy, so score corrections in these tests never touch the real scores.
        self.run_dir = self.tmp / "run"
        shutil.copytree(RUN1_DIR, self.run_dir)
        rewind_to_pre_judge(self.run_dir)

    def judge_all(self, overrides=None, seeded_overrides=None, wrap_run_a=None):
        runs = []
        for n in "ab":
            respond = oracle_for(self.run_dir, overrides)
            if n == "a" and wrap_run_a:
                respond = wrap_run_a(respond)
            runs.append(quiet(run_judge.run_judge, FakeClient(respond), self.run_dir, output_root=self.tmp / f"run_{n}"))
        seeded = [
            quiet(run_judge.run_judge, FakeClient(oracle_for(self.run_dir, seeded_overrides)), self.run_dir, seeded=True,
                  output_root=self.tmp / f"seeded_{n}")
            for n in "ab"
        ]
        return runs, seeded

    def validate(self, runs, seeded):
        return validate_judge.validate(runs, seeded, output_dir=self.tmp / "validation")

    def report(self) -> str:
        return (self.tmp / "validation" / "judge_opus-5.5_v1.md").read_text(encoding="utf-8")

    def test_a_judge_that_agrees_is_validated(self):
        data = self.validate(*self.judge_all())
        self.assertEqual(data["validated"], {"corrected": True, "original": True})
        self.assertIn("**Verdict (corrected hand scores): VALIDATED**", self.report())
        self.assertNotIn("The verdict differs", self.report())
        # The pre-judge change is part of the ground truth, not reverted.
        self.assertIn("pre-judge", self.report())
        self.assertEqual(data["comparisons"]["original"][0]["labels"]["duplicate"]["catch"]["total"], 4)

    def test_retries_and_drop_rate_are_reported(self):
        data = self.validate(*self.judge_all(wrap_run_a=lambda r: short_list_first(r, SAMPLE_005_NOTES)))
        self.assertTrue(data["validated"]["corrected"])  # a retried sample's grades count as usual
        retries = data["retries"]
        self.assertEqual(retries["total_retries"], 1)
        self.assertEqual([p["api_calls"] for p in retries["passes"]], [31, 30, 26, 26])
        self.assertEqual((retries["drop_rate"]["count"], retries["drop_rate"]["total"]), (1, 113))
        report = self.report()
        self.assertIn("**Drop rate:** 0.9% (1/113)", report)
        self.assertIn("- Run A, sample_005: Output did not match the batch: No grade for c02", report)

    def test_discarded_run_counts_toward_drop_rate_and_cost_only(self):
        runs, seeded = self.judge_all()
        # Like the discarded run B: incomplete, made before retries were
        # added, with one invalid output as a sample's final error.
        client = FakeClient(short_list_first(oracle_for(self.run_dir), SAMPLE_005_NOTES, times=2))
        discarded = quiet(run_judge.run_judge, client, self.run_dir, output_root=self.tmp / "discarded")
        results_path = discarded / "judge_results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        for r in results:
            del r["attempts"], r["failed_attempts"]
        results_path.write_text(json.dumps(results), encoding="utf-8")

        without = validate_judge.validate(runs, seeded, output_dir=self.tmp / "without")
        data = self.validate_with_discarded(runs, seeded, [discarded])
        # Never graded or compared: every check and comparison is unchanged.
        for key in ("validated", "checks", "comparisons", "consistency", "seeded"):
            self.assertEqual(data[key], without[key], key)
        self.assertEqual((without["retries"]["drop_rate"]["count"], without["retries"]["drop_rate"]["total"]), (0, 112))
        self.assertEqual((data["retries"]["drop_rate"]["count"], data["retries"]["drop_rate"]["total"]), (1, 142))
        discarded_cost = json.loads((discarded / "judge_run.json").read_text(encoding="utf-8"))["metrics"]["total_cost_usd"]
        self.assertAlmostEqual(data["total_spent_usd"], without["total_spent_usd"] + discarded_cost)
        report = self.report()
        self.assertIn("| discarded (incomplete) |", report)
        self.assertIn("Total spent, including discarded runs", report)
        self.assertIn("- Discarded 1, sample_005: Output did not match the batch: No grade for c02", report)

    def test_a_complete_run_cant_be_discarded(self):
        runs, seeded = self.judge_all()
        with self.assertRaises(SystemExit):
            quiet(self.validate_with_discarded, runs, seeded, [runs[0]])

    def validate_with_discarded(self, runs, seeded, discarded):
        return validate_judge.validate(runs, seeded, output_dir=self.tmp / "validation", discarded_paths=discarded)

    def test_too_many_misses_fail(self):
        # The judge passes three of the twelve unambiguous failures; two misses are allowed.
        misses = {c: {"unambiguous": "Y"} for c in ("sample_001-c03", "sample_002-c01", "sample_011-c10")}
        data = self.validate(*self.judge_all(overrides=misses))
        self.assertFalse(data["validated"]["corrected"])
        failed = [c["check"] for c in data["checks"]["corrected"] if not all(c["passed"])]
        self.assertIn("Unambiguous: catches", failed)
        # Two of the three only failed unambiguous, so the judge's clean card
        # rate rises to 162/186 (87.1%), still within 3 points of 86.0%.
        self.assertNotIn("Clean card rate", failed)
        self.assertIn("### Unambiguous (3)", self.report())

    def test_false_alarms_and_seeded_misses_fail(self):
        alarms = {c: {"supported": "N"} for c in (
            "sample_003-c01", "sample_003-c02", "sample_003-c03", "sample_003-c04", "sample_003-c05",
            "sample_003-c06", "sample_003-c07", "sample_012-c01", "sample_012-c02", "sample_012-c03",
        )}
        seeded_misses = {"dup-1": {"duplicate_of": None}, "dup-6": {"duplicate_of": None}}
        data = self.validate(*self.judge_all(overrides=alarms, seeded_overrides=seeded_misses))
        failed = [c["check"] for c in data["checks"]["corrected"] if not all(c["passed"])]
        self.assertIn("Supported: false alarm rate", failed)  # 10 of 184 = 5.4%
        self.assertIn("Seeded duplicates: correct", failed)  # 4 of 6
        self.assertNotIn("Seeded atomic: correct", failed)

    def test_judge_prompted_correction_changes_the_verdict(self):
        # Three misses fail against the original scores. After one hand score is
        # corrected (with the judge's reason citing a rule), two misses remain.
        misses = {c: {"unambiguous": "Y"} for c in ("sample_001-c03", "sample_002-c01", "sample_011-c10")}
        runs, seeded = self.judge_all(overrides=misses)

        scores = self.run_dir / "scores.csv"
        text = scores.read_text(encoding="utf-8-sig")
        old_row = next(line for line in text.splitlines() if line.startswith("sample_011-c10,"))
        new_row = old_row.replace(",Y,Y,Y,N,,", ",Y,Y,Y,Y,,", 1)
        self.assertNotEqual(old_row, new_row)
        scores.write_text(text.replace(old_row, new_row), encoding="utf-8-sig")
        with (self.run_dir / "score_changes.csv").open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["2026-10-13", "sample_011-c10", "unambiguous", "N", "Y", runs[0].name,
                                    "Notes are the only source of truth", "Test correction"])

        data = self.validate(runs, seeded)
        self.assertEqual(data["validated"], {"corrected": True, "original": False})
        report = self.report()
        self.assertTrue(report.splitlines()[2].startswith("> ⚠️ **The verdict differs"))
        # The corrected card now agrees with the judge, so it leaves the
        # disagreements and is listed under score changes instead.
        self.assertIn("| 2026-10-13 | sample_011-c10 | unambiguous | N | Y |", report)
        self.assertIn("### Unambiguous (2)", report)

    def test_score_log_out_of_sync_is_refused(self):
        runs, seeded = self.judge_all()
        with (self.run_dir / "score_changes.csv").open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["2026-10-13", "sample_011-c10", "unambiguous", "N", "Y", "some-run", "rule", "reason"])
        with self.assertRaises(SystemExit):
            quiet(self.validate, runs, seeded)

    def write_agreement_sample(self, decisions: dict) -> Path:
        path = self.tmp / "agreement_sample.csv"
        write_csv(path, ["card_id", "criterion", "question", "answer", "decision", "decision_reason"], [
            {"card_id": card_id, "criterion": key, "question": "", "answer": "", "decision": decision,
             "decision_reason": f"Recheck of {card_id}"}
            for (card_id, key), decision in decisions.items()
        ])
        path.with_suffix(".md").write_text("- **Random seed:** 7\n", encoding="utf-8")
        return path

    def test_agreement_sample_reports_shared_errors(self):
        runs, seeded = self.judge_all()
        sample = self.write_agreement_sample({
            ("sample_015-c05", "unambiguous"): "N",  # agreed Y: a shared error
            ("sample_001-c01", "atomic"): "Y",
        })
        data = validate_judge.validate(runs, seeded, output_dir=self.tmp / "validation", agreement_path=sample)
        self.assertEqual((data["agreement"]["matched"], data["agreement"]["seed"]), (1, 7))
        self.assertTrue(data["validated"]["corrected"])  # reported, never part of the verdict
        report = self.report()
        self.assertIn("- **Agreement check:** 1 of 2 matched, 1 shared error", report)
        self.assertIn("**1 of 2 matched; 1 shared error.**", report)
        self.assertIn("| sample_015-c05 | unambiguous | Y | N | Recheck of sample_015-c05 |", report)
        self.assertIn("rate this sample can't pin down (1/2), and the unambiguous result is likely optimistic.", report)

    def test_agreement_sample_with_a_disagreed_pair_is_refused(self):
        # The judge fails a card the hand scores pass, so it isn't an agreed pair.
        runs, seeded = self.judge_all(overrides={"sample_001-c01": {"atomic": "N"}})
        sample = self.write_agreement_sample({("sample_001-c01", "atomic"): "Y"})
        with self.assertRaises(SystemExit) as raised:
            quiet(validate_judge.validate, runs, seeded, output_dir=self.tmp / "validation", agreement_path=sample)
        self.assertIn("isn't an agreed pair", str(raised.exception.code))

    def test_different_judges_are_refused(self):
        runs, seeded = self.judge_all()
        info_path = runs[1] / "judge_run.json"
        info = json.loads(info_path.read_text(encoding="utf-8"))
        info["judge_hash"] = "000000000000"
        info_path.write_text(json.dumps(info), encoding="utf-8")
        with self.assertRaises(SystemExit):
            quiet(self.validate, runs, seeded)


# ---------------------------------------------------------------------------
# Scoring corrected hand scores
# ---------------------------------------------------------------------------

class ScoreCorrectedRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.run_dir = self.tmp / "run"
        shutil.copytree(RUN1_DIR, self.run_dir)
        # A copy of the log, so the real one is never written to.
        self.log = self.tmp / "results_log.md"
        shutil.copy(score_run.RESULTS_LOG_PATH, self.log)
        # The copy may carry the real judge-prompted changes; these tests set their own.
        rewind_to_pre_judge(self.run_dir)

    def score(self, *args):
        argv = ["score_run.py", *args, str(self.run_dir)]
        # REPO_ROOT too, since the script prints the log's path relative to it.
        with mock.patch.object(sys, "argv", argv), mock.patch.object(score_run, "RESULTS_LOG_PATH", self.log), \
                mock.patch.object(score_run, "REPO_ROOT", self.tmp):
            quiet(score_run.main)

    def add_judge_prompted_change(self):
        with (self.run_dir / "score_changes.csv").open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["2026-10-17", "sample_011-c10", "unambiguous", "N", "Y", "some-judge-run",
                                    "Rubric 1.6, Unambiguous", "Test correction", "blind"])

    def test_plain_hand_is_refused_after_judge_prompted_changes(self):
        self.add_judge_prompted_change()
        log_before = file_hash(self.log)
        hand_before = file_hash(self.run_dir / "hand_scores.json")
        with self.assertRaises(SystemExit) as raised:
            self.score()
        message = str(raised.exception.code)
        self.assertIn("1 score change(s) made after judge output", message)
        self.assertIn("--scorer hand:corrected:<judge>", message)
        # Nothing is written: the original row and its scores file stay as they were.
        self.assertEqual(file_hash(self.log), log_before)
        self.assertEqual(file_hash(self.run_dir / "hand_scores.json"), hand_before)

    def test_plain_hand_is_allowed_with_only_pre_judge_changes(self):
        (self.run_dir / "hand_scores.json").unlink()
        self.score()
        self.assertEqual(self.clean_count("hand_scores.json"), 160)
        self.assertIn("| 1.6 | 2 | hand | 86.0% (160/186) |", self.log.read_text(encoding="utf-8"))

    def clean_count(self, name: str) -> int:
        record = json.loads((self.run_dir / name).read_text(encoding="utf-8"))
        return record["metrics"]["scored"]["clean_card_rate"]["count"]

    def test_corrected_label_adds_a_row_beside_the_original(self):
        self.add_judge_prompted_change()
        scores = self.run_dir / "scores.csv"
        text = scores.read_text(encoding="utf-8-sig")
        old_row = next(line for line in text.splitlines() if line.startswith("sample_011-c10,"))
        scores.write_text(text.replace(old_row, old_row.replace(",Y,Y,Y,N,,", ",Y,Y,Y,Y,,", 1)), encoding="utf-8-sig")

        self.score("--scorer", "hand:corrected:judge-v1")
        log = self.log.read_text(encoding="utf-8")
        self.assertIn("| 1.6 | 2 | hand | 86.0% (160/186) |", log)
        self.assertIn("| 1.6 | 2 | hand:corrected:judge-v1 | 86.6% (161/186) |", log)
        self.assertEqual(self.clean_count("hand_corrected_judge-v1_scores.json"), 161)


if __name__ == "__main__":
    unittest.main()
