"""Offline tests for the runner's --model flag (run_eval.py) and per-model settings in card_generation.py.

Every test replaces the Anthropic client with a stub, so no API call is ever
made, and runs write to a temporary folder, never eval/runs/.

Run from the repository root:
    .venv/bin/python -m unittest discover -s eval/tests -v
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR))

import run_eval  # noqa: E402  (also puts backend/ on the path)
from app.services import card_generation  # noqa: E402

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-5-5"
OUTPUT = json.dumps({"status": "ok", "cards": [
    {"question": "What year was the Treaty of Versailles signed?", "answer": "1919", "source": ["1919"]},
]})


class StubClient:
    """Stands in for anthropic.Anthropic and records every request."""

    def __init__(self, calls: list, **kwargs):
        self.calls = calls
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **request):
        self.calls.append(request)
        return SimpleNamespace(
            model=request["model"],
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=1_000_000, output_tokens=1_000_000),
            content=[SimpleNamespace(type="text", text=OUTPUT)],
        )


class ModelSettingsTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        patches = [
            mock.patch.object(card_generation.anthropic, "Anthropic", lambda **kw: StubClient(self.calls, **kw)),
            mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_every_priced_model_has_request_options(self):
        self.assertEqual(set(card_generation.PRICING), set(card_generation.REQUEST_OPTIONS))
        self.assertIn(card_generation.MODEL, card_generation.PRICING)

    def test_app_default_is_haiku_without_thinking_or_effort(self):
        self.assertEqual(card_generation.MODEL, HAIKU)
        result = card_generation.generate_cards("notes")
        request = self.calls[0]
        self.assertEqual(request["model"], HAIKU)
        self.assertNotIn("thinking", request)
        self.assertEqual(list(request["output_config"]), ["format"])
        self.assertAlmostEqual(result.metadata.cost_usd, 1.00 + 5.00)  # one million tokens each way

    def test_sonnet_is_sent_without_extended_thinking_at_its_own_rates(self):
        result = card_generation.generate_cards("notes", model=SONNET)
        request = self.calls[0]
        self.assertEqual(request["model"], SONNET)
        self.assertEqual(request["thinking"], {"type": "between_tools"})
        self.assertEqual(request["output_config"]["effort"], "high")
        self.assertEqual(request["output_config"]["format"]["type"], "json_schema")
        self.assertAlmostEqual(result.metadata.cost_usd, 2.00 + 10.00)
        self.assertEqual(result.metadata.model, SONNET)

    def test_unpriced_model_is_refused_before_any_call(self):
        with self.assertRaises(ValueError):
            card_generation.generate_cards("notes", model="claude-sonnet-5")
        self.assertEqual(self.calls, [])


class ModelFlagTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.calls = []
        patches = [
            mock.patch.object(card_generation.anthropic, "Anthropic", lambda **kw: StubClient(self.calls, **kw)),
            mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}),
            mock.patch.object(run_eval, "RUNS_DIR", self.tmp / "runs"),
            mock.patch.object(run_eval, "PARTIAL_RUNS_DIR", self.tmp / "runs" / "partial"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def run_eval(self, *argv) -> dict:
        with mock.patch.object(sys, "argv", ["run_eval.py", "--samples", "sample_001", *argv]), \
                contextlib.redirect_stdout(io.StringIO()):
            run_eval.main()
        (run_dir,) = (self.tmp / "runs" / "partial").iterdir()
        return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    def test_default_run_uses_the_app_model(self):
        info = self.run_eval()
        self.assertEqual(info["model"], HAIKU)
        self.assertIsNone(info["thinking"])
        self.assertIsNone(info["effort"])
        self.assertEqual(info["prompt_version"], "v2")
        self.assertEqual(self.calls[0]["model"], HAIKU)

    def test_model_flag_records_the_requested_model_and_settings(self):
        info = self.run_eval("--model", SONNET)
        self.assertEqual(info["model"], SONNET)
        self.assertEqual(info["thinking"], {"type": "between_tools"})
        self.assertEqual(info["effort"], "high")
        self.assertEqual([c["model"] for c in self.calls], [SONNET])
        self.assertFalse(info["incomplete"])
        # The app's own model is untouched.
        self.assertEqual(card_generation.MODEL, HAIKU)

    def test_unknown_model_is_refused_before_any_run(self):
        with mock.patch.object(sys, "argv", ["run_eval.py", "--model", "claude-sonnet-5"]), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            run_eval.main()
        self.assertEqual(self.calls, [])
        self.assertFalse((self.tmp / "runs").exists())


if __name__ == "__main__":
    unittest.main()
