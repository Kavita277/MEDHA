"""
test_nlp_interface.py
=====================
Focused unit tests for the MEDHA NLP adapter interface.

Tests covered
-------------
A  scale_1_5 answer        -> deterministic parser; NLP adapter NOT called
B  yes_no answer           -> deterministic parser; NLP adapter NOT called
C  multiple_choice answer  -> deterministic parser; NLP adapter NOT called
D  optional_text           -> extract_free_text_signals called exactly once
E  optional_text_or_voice  -> extract_free_text_signals called exactly once
F  NLP adapter failure     -> session does not crash; failure sentinel recorded
G  NLP module unavailable  -> extraction_status == "unavailable"; session continues

Design notes
------------
- Does NOT load the Excel dataset.
- Uses in-memory fake question dicts and temporary history files.
- Tests A/B/C verify the output schema (no NLP sentinel keys) rather than
  trying to patch a name that only exists inside a function body.
- Tests D/E/F/G patch at the nlp_interface module level, which is where
  the import resolves at runtime.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Minimal fake question dicts
# ---------------------------------------------------------------------------

def _question(question_id, response_type, trigger="scheduled_checkin",
              intent="general_wellbeing"):
    return {
        "question_id":   question_id,
        "question":      f"Fake question {question_id}",
        "response_type": response_type,
        "trigger":       trigger,
        "intent":        intent,
        "cooldown_days": 1,
    }


# ---------------------------------------------------------------------------
# NLP sentinel keys — these must NOT appear in deterministic outputs
# ---------------------------------------------------------------------------

NLP_KEYS = {
    "mentioned_emotions", "mentioned_problems", "linked_case_event",
    "sleep_issue", "social_support_issue", "safety_concern_mentioned",
    "needs_human_followup", "confidence",
    "extraction_status", "extraction_note", "extraction_error", "raw_text",
}

# Canonical valid NLP result (returned by mock when adapter succeeds)
MOCK_NLP_RESULT = {
    "mentioned_emotions":       ["anxious"],
    "mentioned_problems":       ["difficulty sleeping"],
    "linked_case_event":        "hearing",
    "sleep_issue":              True,
    "social_support_issue":     None,
    "safety_concern_mentioned": None,
    "needs_human_followup":     None,
    "confidence":               0.85,
}


# ---------------------------------------------------------------------------
# Base test class
# ---------------------------------------------------------------------------

class NLPInterfaceTestCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        json.dump([], self._tmp)
        self._tmp.close()
        self.history_file = self._tmp.name

    def tearDown(self):
        try:
            os.unlink(self.history_file)
        except OSError:
            pass

    def _record(self, question, answer, answered=True, skipped=False):
        from test_engine import record_interaction
        return record_interaction(
            question,
            answer=answer,
            answered=answered,
            skipped=skipped,
            patient_id="TEST-001",
            filename=self.history_file,
        )


# ---------------------------------------------------------------------------
# Test A — scale_1_5: deterministic output; no NLP sentinel keys present
# ---------------------------------------------------------------------------

class TestA_Scale(NLPInterfaceTestCase):

    def test_scale_produces_deterministic_output(self):
        """
        A scale_1_5 answer must be handled by the deterministic parser.
        The structured_output must contain the numeric score and must NOT
        contain any NLP extraction keys.
        """
        q = _question("GW-01", "scale_1_5")
        record = self._record(q, "3")

        out = record["structured_output"]
        self.assertEqual(
            out,
            {"wellbeing_score": 3},
            "scale_1_5 must produce only {wellbeing_score: 3}"
        )
        # Confirm no NLP sentinel keys leaked in
        nlp_leakage = NLP_KEYS & set(out.keys())
        self.assertEqual(nlp_leakage, set(),
                         f"NLP keys must not appear in scale output: {nlp_leakage}")


# ---------------------------------------------------------------------------
# Test B — yes_no: deterministic output; no NLP sentinel keys present
# ---------------------------------------------------------------------------

class TestB_YesNo(NLPInterfaceTestCase):

    def test_yesno_produces_deterministic_output(self):
        q = _question("SA-01", "yes_no",
                      trigger="safety_intent_active", intent="safety_support")
        record = self._record(q, "yes")

        out = record["structured_output"]
        self.assertEqual(
            out,
            {"feels_safe": True},
            "yes_no must produce only {feels_safe: True}"
        )
        nlp_leakage = NLP_KEYS & set(out.keys())
        self.assertEqual(nlp_leakage, set(),
                         f"NLP keys must not appear in yes_no output: {nlp_leakage}")


# ---------------------------------------------------------------------------
# Test C — multiple_choice: deterministic output; no NLP sentinel keys
# ---------------------------------------------------------------------------

class TestC_MultipleChoice(NLPInterfaceTestCase):

    def test_mc_produces_deterministic_output(self):
        q = _question("GW-05", "multiple_choice")
        record = self._record(q, "better")

        out = record["structured_output"]
        self.assertEqual(
            out,
            {"self_reported_trend": "better"},
            "multiple_choice must produce only {self_reported_trend: 'better'}"
        )
        nlp_leakage = NLP_KEYS & set(out.keys())
        self.assertEqual(nlp_leakage, set(),
                         f"NLP keys must not appear in MC output: {nlp_leakage}")


# ---------------------------------------------------------------------------
# Test D — optional_text: NLP adapter called exactly once
# ---------------------------------------------------------------------------

class TestD_OptionalText(NLPInterfaceTestCase):

    def test_optional_text_calls_nlp_adapter_once(self):
        q = _question("SF-03", "optional_text",
                      trigger="two_consecutive_low_SF01_scores",
                      intent="sleep_functioning")
        free_text = "I can't sleep because I'm worried about the hearing."

        import nlp_interface
        with patch.object(nlp_interface, "extract_free_text_signals",
                          return_value=MOCK_NLP_RESULT) as mock_nlp:
            record = self._record(q, free_text)

        mock_nlp.assert_called_once_with(free_text)
        self.assertEqual(record["structured_output"], MOCK_NLP_RESULT)
        self.assertEqual(record["response_type"], "optional_text")


# ---------------------------------------------------------------------------
# Test E — optional_text_or_voice: NLP adapter called exactly once
# ---------------------------------------------------------------------------

class TestE_OptionalTextOrVoice(NLPInterfaceTestCase):

    def test_optional_text_or_voice_calls_nlp_adapter_once(self):
        q = _question("GW-06", "optional_text_or_voice",
                      trigger="two_or_more_low_GW01_scores",
                      intent="general_wellbeing")
        free_text = "Things have been really hard lately."

        import nlp_interface
        with patch.object(nlp_interface, "extract_free_text_signals",
                          return_value=MOCK_NLP_RESULT) as mock_nlp:
            record = self._record(q, free_text)

        mock_nlp.assert_called_once_with(free_text)
        self.assertEqual(record["structured_output"], MOCK_NLP_RESULT)
        self.assertEqual(record["response_type"], "optional_text_or_voice")


# ---------------------------------------------------------------------------
# Test F — NLP adapter raises internally: session does not crash
# The adapter's own error handling must absorb the exception and return a
# failure sentinel. record_interaction has no try/except around the NLP call.
# ---------------------------------------------------------------------------

class TestF_NLPAdapterFailure(NLPInterfaceTestCase):

    def test_nlp_failure_does_not_crash_session(self):
        """
        nlp_interface.extract_free_text_signals must never propagate an
        exception. If the real NLP model raises, the adapter absorbs it and
        returns an extraction-failed sentinel. The session record is still
        written.
        """
        q = _question("SF-03", "optional_text",
                      trigger="two_consecutive_low_SF01_scores",
                      intent="sleep_functioning")
        free_text = "I am exhausted and can't sleep."

        import nlp_interface

        # Simulate medha_nlp being present but raising during inference.
        mock_module = MagicMock()
        mock_module.extract_free_text_signals.side_effect = RuntimeError(
            "Model inference error"
        )

        with patch.dict(sys.modules, {"medha_nlp": mock_module}):
            # Call nlp_interface directly to verify sentinel.
            result = nlp_interface.extract_free_text_signals(free_text)

        self.assertEqual(
            result["extraction_status"], "failed",
            f"Expected 'failed', got: {result}"
        )
        self.assertIn("Model inference error", result["extraction_error"])
        self.assertEqual(result["raw_text"], free_text)
        self.assertEqual(result["mentioned_emotions"], [])
        self.assertEqual(result["confidence"], 0.0)

    def test_session_record_written_despite_nlp_failure(self):
        """
        End-to-end: even when NLP raises internally, record_interaction
        must complete and persist the record.
        """
        q = _question("GW-06", "optional_text_or_voice",
                      trigger="two_or_more_low_GW01_scores",
                      intent="general_wellbeing")
        free_text = "I feel very isolated."

        import nlp_interface

        mock_module = MagicMock()
        mock_module.extract_free_text_signals.side_effect = RuntimeError("error")

        with patch.dict(sys.modules, {"medha_nlp": mock_module}):
            record = self._record(q, free_text)

        self.assertIsNotNone(record)
        self.assertEqual(record["structured_output"]["extraction_status"], "failed")
        # Verify it was actually persisted to the temp history file.
        written = json.load(open(self.history_file, encoding="utf-8"))
        self.assertEqual(len(written), 1)
        self.assertEqual(
            written[0]["structured_output"]["extraction_status"], "failed"
        )


# ---------------------------------------------------------------------------
# Test G — NLP module unavailable: extraction_status == "unavailable"
# ---------------------------------------------------------------------------

class TestG_NLPUnavailable(NLPInterfaceTestCase):

    def _make_fake_import(self, original):
        def fake_import(name, *args, **kwargs):
            if name == "medha_nlp":
                raise ImportError("No module named 'medha_nlp'")
            return original(name, *args, **kwargs)
        return fake_import

    def test_unavailable_sentinel_direct(self):
        """
        nlp_interface.extract_free_text_signals must return the
        extraction-unavailable sentinel when medha_nlp cannot be imported.
        """
        import nlp_interface
        import builtins

        saved = sys.modules.pop("medha_nlp", None)
        try:
            with patch("builtins.__import__",
                       side_effect=self._make_fake_import(builtins.__import__)):
                result = nlp_interface.extract_free_text_signals("I feel alone.")
        finally:
            if saved is not None:
                sys.modules["medha_nlp"] = saved

        self.assertEqual(result["extraction_status"], "unavailable")
        self.assertEqual(result["mentioned_emotions"], [])
        self.assertEqual(result["mentioned_problems"], [])
        self.assertIsNone(result["linked_case_event"])
        self.assertIsNone(result["sleep_issue"])
        self.assertIsNone(result["social_support_issue"])
        self.assertIsNone(result["safety_concern_mentioned"])
        self.assertIsNone(result["needs_human_followup"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["raw_text"], "I feel alone.")
        self.assertIn("medha_nlp", result["extraction_note"].lower())

    def test_record_interaction_with_unavailable_nlp(self):
        """
        End-to-end: record_interaction produces a valid record with
        extraction_status == 'unavailable' when NLP module is absent.
        """
        q = _question("GW-06", "optional_text_or_voice",
                      trigger="two_or_more_low_GW01_scores",
                      intent="general_wellbeing")
        free_text = "Not much support around me."

        import nlp_interface
        import builtins

        saved = sys.modules.pop("medha_nlp", None)
        try:
            with patch("builtins.__import__",
                       side_effect=self._make_fake_import(builtins.__import__)):
                record = self._record(q, free_text)
        finally:
            if saved is not None:
                sys.modules["medha_nlp"] = saved

        self.assertIsNotNone(record)
        out = record["structured_output"]
        self.assertEqual(out["extraction_status"], "unavailable")
        self.assertEqual(out["raw_text"], free_text)
        self.assertEqual(out["confidence"], 0.0)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestA_Scale,
        TestB_YesNo,
        TestC_MultipleChoice,
        TestD_OptionalText,
        TestE_OptionalTextOrVoice,
        TestF_NLPAdapterFailure,
        TestG_NLPUnavailable,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 62)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passed = total - failures
    print(f"NLP INTERFACE TESTS: {passed} passed, {failures} failed  "
          f"(of {total} total)")
    print("=" * 62)
    return result


if __name__ == "__main__":
    run_tests()
