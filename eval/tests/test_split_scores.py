"""Offline tests for split scoring (split_scores.py).

They use a copy of Run 1 (rubric 1.6) and its judge run A in a temporary
folder, so the real run folder is never written to and no judge is called.

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

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR))

import score_run  # noqa: E402
import split_scores  # noqa: E402

RUN1_DIR = EVAL_DIR / "runs" / "2026-10-02_215109" / "rescored" / "rubric-1.6_test-set-2"
JUDGE_RUN_A = "2026-10-13_214206"
SEED = 12345


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class SplitScoresTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.run_dir = self.tmp / "run"
        shutil.copytree(RUN1_DIR, self.run_dir)
        shutil.rmtree(self.run_dir / "split", ignore_errors=True)
        # The copied judge run still names the real run folder.
        self.judge_dir = self.run_dir / "judge" / JUDGE_RUN_A
        self.edit_json(self.judge_dir / "judge_run.json", lambda d: d.update(base_run_dir=str(self.run_dir)))
        self.split_dir = self.run_dir / "split" / JUDGE_RUN_A
        records = json.loads((self.run_dir / "results.json").read_text(encoding="utf-8"))
        self.cards = {
            c["card_id"]: {"sample_id": r["id"], "index": i, "question": c["question"]}
            for r in records if r["scored_in_stage2"] for i, c in enumerate(r["cards"])
        }

    def edit_json(self, path: Path, change) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def run_cli(self, *argv):
        quiet(split_scores.main, [*argv])

    def refused(self, *argv) -> str:
        with self.assertRaises(SystemExit) as raised:
            self.run_cli(*argv)
        return str(raised.exception.code)

    def review(self, *extra):
        self.run_cli("review", "--judge-run", str(self.judge_dir), "--unambiguous", str(self.run_dir / "scores.csv"),
                     "--seed", str(SEED), *extra, str(self.run_dir))

    def merge(self):
        self.run_cli("merge", "--judge-run", str(self.judge_dir), "--unambiguous", str(self.run_dir / "scores.csv"),
                     str(self.run_dir))

    def merge_refused(self) -> str:
        return self.refused("merge", "--judge-run", str(self.judge_dir), "--unambiguous",
                            str(self.run_dir / "scores.csv"), str(self.run_dir))

    def agree_with_judge(self):
        # A review that keeps every fail and agrees with every sampled pass.
        fails = read_rows(self.split_dir / "review_fails.csv")
        for row in fails:
            row["decision"] = "keep"
        write_rows(self.split_dir / "review_fails.csv", fails)
        passes = read_rows(self.split_dir / "review_passes.csv")
        for row in passes:
            row["decision"] = "none" if row["criterion"] == "duplicate" else "Y"
        write_rows(self.split_dir / "review_passes.csv", passes)

    def merged_clean(self) -> int:
        scores, problems = score_run.read_scores(self.split_dir / "split_scores.csv", self.cards)
        self.assertEqual(problems, [])
        return score_run.compute_scored_metrics(list(scores.values()))["clean_card_rate"]["count"]

    # --- sheet -------------------------------------------------------------

    def test_sheet_is_blind(self):
        self.run_cli("sheet", str(self.run_dir))
        path = self.run_dir / "split" / "unambiguous_sheet.csv"
        rows = read_rows(path)
        self.assertEqual(list(rows[0]), ["card_id", "question", "answer", "unambiguous", "note"])
        self.assertEqual(len(rows), 186)
        self.assertTrue(all(r["unambiguous"] == "" and r["note"] == "" for r in rows))
        self.assertIn("Not overwriting", self.refused("sheet", str(self.run_dir)))

    def test_review_waits_for_a_complete_unambiguous_sheet(self):
        self.run_cli("sheet", str(self.run_dir))
        message = self.refused("review", "--judge-run", str(self.judge_dir), str(self.run_dir))
        self.assertIn("unambiguous is blank", message)
        self.assertFalse(self.split_dir.exists())

    # --- review ------------------------------------------------------------

    def test_fails_sheet_lists_every_failed_pair_with_its_reason(self):
        self.review()
        rows = read_rows(self.split_dir / "review_fails.csv")
        self.assertEqual(len(rows), 47)
        self.assertNotIn("unambiguous", {r["criterion"] for r in rows})
        self.assertTrue(all(r["judge_reason"] for r in rows))
        self.assertTrue(all(r["decision"] == "" for r in rows))

    def test_pass_sample_is_blind_and_reproducible(self):
        self.review()
        rows = read_rows(self.split_dir / "review_passes.csv")
        self.assertEqual(list(rows[0]), ["card_id", "criterion", "question", "answer", "decision", "decision_reason"])
        self.assertEqual([r["criterion"] for r in rows], [k for k in split_scores.JUDGE_LABELS for _ in range(5)])
        self.assertEqual(split_scores.read_seed(self.split_dir / "review_passes.md"), SEED)
        grades = {g["card_id"]: g for r in json.loads((self.judge_dir / "judge_results.json").read_text(encoding="utf-8"))
                  for g in r["grades"]}
        pools = split_scores.passed_pairs(grades, self.cards)
        self.assertTrue(all(card_id in pools[label] for card_id, label in
                            ((r["card_id"], r["criterion"]) for r in rows)))
        self.assertIn("can't pin down a low miss rate", (self.split_dir / "review_passes.md").read_text())
        self.assertIn("Not overwriting", self.refused("review", "--judge-run", str(self.judge_dir), "--unambiguous",
                                                      str(self.run_dir / "scores.csv"), str(self.run_dir)))

    def test_pass_pool_includes_cards_failed_on_another_criterion(self):
        grades = {g["card_id"]: g for r in json.loads((self.judge_dir / "judge_results.json").read_text(encoding="utf-8"))
                  for g in r["grades"]}
        pools = split_scores.passed_pairs(grades, self.cards)
        failed = split_scores.failed_pairs(grades, self.cards)
        self.assertEqual(sum(len(pool) for pool in pools.values()), 4 * len(self.cards) - len(failed))
        card_id, label = next((c, l) for c, l in failed if l == "atomic")
        self.assertNotIn(card_id, pools["atomic"])
        self.assertIn(card_id, pools["supported"])

    def test_decisions_from_hand_only_on_the_validation_run(self):
        self.edit_json(self.run_dir / "run.json", lambda d: d.update(run_id="2026-11-01_120000"))
        message = self.refused("review", "--judge-run", str(self.judge_dir), "--unambiguous",
                               str(self.run_dir / "scores.csv"), "--decisions-from-hand", str(self.run_dir))
        self.assertIn("only for run 2026-10-02_215109", message)

    # --- merge -------------------------------------------------------------

    def test_run_1_from_hand_scores(self):
        log_before = file_hash(self.run_dir / "score_changes.csv")
        self.review("--decisions-from-hand")
        self.assertEqual(len(read_rows(self.split_dir / "score_changes.csv")), 8)
        self.merge()
        self.assertEqual(self.merged_clean(), 149)
        info = json.loads((self.split_dir / "split_scores.json").read_text(encoding="utf-8"))
        self.assertEqual(info["scorer"], "judge:opus-5.5:v1+hand")
        self.assertEqual(info["review_changes"], 8)
        # The run's own change log, which validate_judge.py reads, is never touched.
        self.assertEqual(file_hash(self.run_dir / "score_changes.csv"), log_before)

    def test_judge_unambiguous_grades_are_ignored(self):
        def all_unambiguous_n(results):
            for record in results:
                for g in record["grades"]:
                    g["unambiguous"] = "N"
        self.edit_json(self.judge_dir / "judge_results.json", all_unambiguous_n)
        self.review()
        self.agree_with_judge()
        self.merge()
        merged = {r["card_id"]: r["unambiguous"] for r in read_rows(self.split_dir / "split_scores.csv")}
        hand = {r["card_id"]: r["unambiguous"] for r in read_rows(self.run_dir / "scores.csv")}
        self.assertEqual(merged, hand)
        self.assertEqual(self.merged_clean(), 142)

    def test_other_judges_and_unusable_runs_are_refused(self):
        self.review()
        self.agree_with_judge()
        self.edit_json(self.judge_dir / "judge_run.json", lambda d: d.update(judge_hash="0123456789ab"))
        self.assertIn("split scoring uses only judge v1", self.merge_refused())
        self.edit_json(self.judge_dir / "judge_run.json",
                       lambda d: d.update(judge_hash=split_scores.JUDGE_V1_HASH, incomplete=True))
        self.assertIn("marked incomplete", self.merge_refused())

    def test_blank_decision_is_refused(self):
        self.review()
        self.agree_with_judge()
        rows = read_rows(self.split_dir / "review_fails.csv")
        rows[0]["decision"] = ""
        write_rows(self.split_dir / "review_fails.csv", rows)
        self.assertIn("expected keep or change", self.merge_refused())
        self.assertFalse((self.split_dir / "split_scores.csv").exists())

    def test_decisions_and_change_log_must_match(self):
        self.review("--decisions-from-hand")
        changes = read_rows(self.split_dir / "score_changes.csv")
        write_rows(self.split_dir / "score_changes.csv", changes[1:])
        self.assertIn("has no change for it", self.merge_refused())
        write_rows(self.split_dir / "score_changes.csv", changes)
        fails = read_rows(self.split_dir / "review_fails.csv")
        kept = next(r for r in fails if r["decision"] == "keep")
        write_rows(self.split_dir / "score_changes.csv", changes + [
            {**changes[0], "card_id": kept["card_id"], "field": split_scores.FIELDS[kept["criterion"]],
             "old": kept["judge_score"], "new": "Y" if kept["criterion"] != "duplicate" else ""},
        ])
        self.assertIn("but the change log has a change for it", self.merge_refused())

    def test_edited_pass_sample_is_refused(self):
        self.review()
        self.agree_with_judge()
        rows = read_rows(self.split_dir / "review_passes.csv")
        rows[0]["card_id"] = next(c for c in self.cards if c not in {r["card_id"] for r in rows})
        write_rows(self.split_dir / "review_passes.csv", rows)
        self.assertIn("doesn't match the sample drawn from the seed", self.merge_refused())

    # --- consistency checks ---------------------------------------------

    def consistency_row(self, card_id, field, old, new):
        return {"date": "2026-10-27", "card_id": card_id, "field": field, "old": old, "new": new,
                "prompted_by": "Sonnet review standards", "rubric_rule": "Rubric 1.6", "reason": "test",
                "provenance": "consistency check"}

    def merged_row(self, card_id):
        return next(r for r in read_rows(self.split_dir / "split_scores.csv") if r["card_id"] == card_id)

    def test_consistency_change_outside_the_sheets_applies(self):
        self.review("--decisions-from-hand")
        sheets = {r["card_id"] for n in ("review_fails.csv", "review_passes.csv") for r in read_rows(self.split_dir / n)}
        self.merge()
        card_id = next(r["card_id"] for r in read_rows(self.split_dir / "split_scores.csv")
                       if r["card_id"] not in sheets and r["supported"] == "Y")
        changes = read_rows(self.split_dir / "score_changes.csv")
        write_rows(self.split_dir / "score_changes.csv", changes + [self.consistency_row(card_id, "supported", "Y", "N")])
        self.merge()
        row = self.merged_row(card_id)
        self.assertEqual(row["supported"], "N")
        self.assertIn("changed in consistency check: supported", row["notes"])
        info = json.loads((self.split_dir / "split_scores.json").read_text(encoding="utf-8"))
        self.assertEqual((info["review_changes"], info["consistency_changes"]), (8, 1))

    def test_consistency_change_starts_from_the_reviewed_score(self):
        # sample_013-c02 atomic is a review change, N to Y. A later consistency
        # check must start from Y, not from the judge's N.
        self.review("--decisions-from-hand")
        changes = read_rows(self.split_dir / "score_changes.csv")
        self.assertIn(("sample_013-c02", "atomic", "N", "Y"), [(r["card_id"], r["field"], r["old"], r["new"]) for r in changes])
        write_rows(self.split_dir / "score_changes.csv", changes + [self.consistency_row("sample_013-c02", "atomic", "N", "Y")])
        self.assertIn("isn't the score at that point ('Y')", self.merge_refused())
        write_rows(self.split_dir / "score_changes.csv", changes + [self.consistency_row("sample_013-c02", "atomic", "Y", "N")])
        self.merge()
        self.assertEqual(self.merged_row("sample_013-c02")["atomic"], "N")

    def test_consistency_changes_apply_in_log_order(self):
        self.review("--decisions-from-hand")
        changes = read_rows(self.split_dir / "score_changes.csv")
        # Y to N, then N back to Y: valid only in this order.
        pair = [self.consistency_row("sample_001-c01", "supported", "Y", "N"),
                self.consistency_row("sample_001-c01", "supported", "N", "Y")]
        write_rows(self.split_dir / "score_changes.csv", changes + pair[::-1])
        self.assertIn("isn't the score at that point", self.merge_refused())
        write_rows(self.split_dir / "score_changes.csv", changes + pair)
        self.merge()
        self.assertEqual(self.merged_row("sample_001-c01")["supported"], "Y")

    def test_bad_consistency_change_is_refused(self):
        self.review("--decisions-from-hand")
        changes = read_rows(self.split_dir / "score_changes.csv")
        for bad, message in ((self.consistency_row("sample_001-c01", "supported", "Y", "Y"), "doesn't change anything"),
                             (self.consistency_row("sample_001-c01", "supported", "Y", "maybe"), "expected Y or N"),
                             (self.consistency_row("sample_001-c01", "unambiguous", "Y", "N"), "isn't one of the judge's criteria")):
            write_rows(self.split_dir / "score_changes.csv", changes + [bad])
            self.assertIn(message, self.merge_refused())
        self.assertFalse((self.split_dir / "split_scores.csv").exists())

    def test_review_change_outside_the_sheets_is_still_refused(self):
        self.review("--decisions-from-hand")
        changes = read_rows(self.split_dir / "score_changes.csv")
        row = {**self.consistency_row("sample_001-c01", "supported", "Y", "N"), "prompted_by": "review", "provenance": "blind"}
        write_rows(self.split_dir / "score_changes.csv", changes + [row])
        self.assertIn("isn't in either review sheet", self.merge_refused())

    def test_changed_duplicate_must_be_an_earlier_card(self):
        self.review()
        self.agree_with_judge()
        passes = read_rows(self.split_dir / "review_passes.csv")
        row = next(r for r in passes if r["criterion"] == "duplicate")
        # A card from the same sample that comes after it.
        later = next(c for c, card in self.cards.items() if card["sample_id"] == self.cards[row["card_id"]]["sample_id"]
                     and card["index"] > self.cards[row["card_id"]]["index"])
        row["decision"] = later
        write_rows(self.split_dir / "review_passes.csv", passes)
        write_rows(self.split_dir / "score_changes.csv", [{
            "date": "2026-10-19", "card_id": row["card_id"], "field": "duplicate_of", "old": "", "new": later,
            "prompted_by": "review", "rubric_rule": "Rubric 1.6, No Near-Duplicates", "reason": "test",
            "provenance": "blind",
        }])
        self.assertIn("not an earlier card in the batch", self.merge_refused())
        self.assertFalse((self.split_dir / "split_scores.csv").exists())


if __name__ == "__main__":
    unittest.main()
