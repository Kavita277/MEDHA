"""
test_behaviour_adapter.py
=========================
Integration tests for the QE → Behaviour Engine raw-input adapter (Option A).

Tests covered
-------------
B1  Completed session — session_status "completed" is preserved verbatim.
B2  Abandoned session — session_status "abandoned" is preserved verbatim.
B3  Answered + skipped questions — both appear with correct answered/skipped flags.
B4  Text response → response_text_length == len(answer).
B5  Structured response → response_text_length is None (not 0).
B6  enrollment_date preserved verbatim.
B7  Timestamps preserved verbatim (session and per-question).
B8  Missing optional fields handled safely — no crash, fields are None.
B9  Behaviour payload coexists with NLP and Voice signals in MedhaState.

Design notes
------------
- Does NOT load the Excel dataset.
- Does NOT require any real teammate model (Behaviour, Speech, NLP).
- Does NOT calculate any Behaviour feature.
- Uses controlled test dicts only.
- The Behaviour Engine is not invoked or mocked here.
- Existing tests (T1–T10b and Test1–Test6) are NOT duplicated.
"""

import unittest

from behaviour_adapter import (
    session_to_behaviour_payload,
    behaviour_payload_to_state,
)
from medha_state import MedhaState
from model_adapters import nlp_signals_to_state, speech_signals_to_state


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

# Minimal session record that matches the sessions.json schema.
_SESSION_COMPLETED = {
    "user_id":             "P-TEST-001",
    "session_id":          "sess-completed-001",
    "session_start_time":  "2026-08-28T09:00:00",
    "session_end_time":    "2026-08-28T09:05:00",
    "session_status":      "completed",
    "questions_presented": 2,
    "questions_answered":  2,
}

_SESSION_ABANDONED = {
    "user_id":             "P-TEST-001",
    "session_id":          "sess-abandoned-001",
    "session_start_time":  "2026-08-28T10:00:00",
    "session_end_time":    "2026-08-28T10:02:30",
    "session_status":      "abandoned",
    "questions_presented": 2,
    "questions_answered":  1,
}

# One answered scale_1_5 interaction record.
_RECORD_ANSWERED_SCALE = {
    "patient_id":              "P-TEST-001",
    "question_id":             "GW-01",
    "session_id":              "sess-completed-001",
    "question_order":          1,
    "question_presented_time": "2026-08-28T09:00:05",
    "answer_submitted_time":   "2026-08-28T09:00:42",
    "answered":                True,
    "skipped":                 False,
    "response_type":           "scale_1_5",
    "answer":                  "4",
    "modality":                "text",
}

# One skipped interaction record (no answer, no session_id).
_RECORD_SKIPPED = {
    "patient_id":              "P-TEST-001",
    "question_id":             "SF-01",
    "session_id":              "sess-completed-001",
    "question_order":          2,
    "question_presented_time": "2026-08-28T09:00:55",
    "answer_submitted_time":   "2026-08-28T09:01:10",
    "answered":                False,
    "skipped":                 True,
    "response_type":           "scale_1_5",
    "answer":                  None,
    "modality":                "text",
}

# Text (optional_text) answered record.
_RECORD_TEXT_ANSWER = {
    "patient_id":              "P-TEST-001",
    "question_id":             "SF-03",
    "session_id":              "sess-completed-001",
    "question_order":          1,
    "question_presented_time": "2026-08-28T09:01:00",
    "answer_submitted_time":   "2026-08-28T09:02:00",
    "answered":                True,
    "skipped":                 False,
    "response_type":           "optional_text",
    "answer":                  "I have been worried about the hearing.",
    "modality":                "text",
}

# Voice/text (optional_text_or_voice) answered record.
_RECORD_VOICE_ANSWER = {
    "patient_id":              "P-TEST-001",
    "question_id":             "GW-06",
    "session_id":              "sess-completed-001",
    "question_order":          2,
    "question_presented_time": "2026-08-28T09:02:30",
    "answer_submitted_time":   "2026-08-28T09:03:15",
    "answered":                True,
    "skipped":                 False,
    "response_type":           "optional_text_or_voice",
    "answer":                  "Having a hard time.",
    "modality":                "voice",
}

# Minimal record — simulates older history.json entries that pre-date
# session_demo.py (missing session_id, order, timestamps, modality).
_RECORD_MINIMAL = {
    "patient_id":  "P-TEST-001",
    "question_id": "GW-01",
    "answered":    True,
    "skipped":     False,
    "response_type": "scale_1_5",
    "answer":      "3",
}

ENROLLMENT_DATE = "2026-01-15"


# ---------------------------------------------------------------------------
# B1 — Completed session status preserved
# ---------------------------------------------------------------------------

class TestB1_CompletedSession(unittest.TestCase):
    """B1: session_status "completed" is preserved verbatim."""

    def setUp(self):
        self.payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_ANSWERED_SCALE],
            enrollment_date=ENROLLMENT_DATE,
        )

    def test_session_status_is_completed(self):
        self.assertEqual(
            self.payload["session_status"], "completed",
            "session_status must be 'completed'"
        )

    def test_questions_presented_correct(self):
        self.assertEqual(self.payload["questions_presented"], 2)

    def test_questions_answered_correct(self):
        self.assertEqual(self.payload["questions_answered"], 2)

    def test_session_id_preserved(self):
        self.assertEqual(self.payload["session_id"], "sess-completed-001")

    def test_questions_list_present(self):
        self.assertIsInstance(self.payload["questions"], list)
        self.assertEqual(len(self.payload["questions"]), 1)


# ---------------------------------------------------------------------------
# B2 — Abandoned session status preserved
# ---------------------------------------------------------------------------

class TestB2_AbandonedSession(unittest.TestCase):
    """B2: session_status "abandoned" is preserved verbatim."""

    def setUp(self):
        self.payload = session_to_behaviour_payload(
            session=_SESSION_ABANDONED,
            history_records=[_RECORD_ANSWERED_SCALE, _RECORD_SKIPPED],
            enrollment_date=ENROLLMENT_DATE,
        )

    def test_session_status_is_abandoned(self):
        self.assertEqual(
            self.payload["session_status"], "abandoned",
            "session_status must be 'abandoned'"
        )

    def test_questions_presented_correct(self):
        self.assertEqual(self.payload["questions_presented"], 2)

    def test_questions_answered_correct(self):
        self.assertEqual(self.payload["questions_answered"], 1)


# ---------------------------------------------------------------------------
# B3 — Answered + skipped questions — correct flags
# ---------------------------------------------------------------------------

class TestB3_AnsweredAndSkipped(unittest.TestCase):
    """B3: One answered and one skipped record → correct answered/skipped flags."""

    def setUp(self):
        self.payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_ANSWERED_SCALE, _RECORD_SKIPPED],
            enrollment_date=ENROLLMENT_DATE,
        )
        self.questions = self.payload["questions"]

    def test_two_question_records(self):
        self.assertEqual(len(self.questions), 2)

    def test_first_question_answered(self):
        q = self.questions[0]
        self.assertTrue(q["answered"], "First question must be answered=True")
        self.assertFalse(q["skipped"], "First question must be skipped=False")

    def test_second_question_skipped(self):
        q = self.questions[1]
        self.assertFalse(q["answered"], "Second question must be answered=False")
        self.assertTrue(q["skipped"], "Second question must be skipped=True")

    def test_question_ids_preserved(self):
        self.assertEqual(self.questions[0]["question_id"], "GW-01")
        self.assertEqual(self.questions[1]["question_id"], "SF-01")


# ---------------------------------------------------------------------------
# B4 — Text response → response_text_length == len(answer)
# ---------------------------------------------------------------------------

class TestB4_TextResponseLength(unittest.TestCase):
    """B4: optional_text and optional_text_or_voice answers yield char count."""

    def test_optional_text_length_is_char_count(self):
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_TEXT_ANSWER],
            enrollment_date=ENROLLMENT_DATE,
        )
        q = payload["questions"][0]
        expected_len = len(_RECORD_TEXT_ANSWER["answer"])
        self.assertIsNotNone(
            q["response_text_length"],
            "response_text_length must not be None for optional_text"
        )
        self.assertEqual(
            q["response_text_length"], expected_len,
            f"Expected char count {expected_len}, got {q['response_text_length']}"
        )

    def test_optional_text_or_voice_length_is_char_count(self):
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_VOICE_ANSWER],
            enrollment_date=ENROLLMENT_DATE,
        )
        q = payload["questions"][0]
        expected_len = len(_RECORD_VOICE_ANSWER["answer"])
        self.assertEqual(
            q["response_text_length"], expected_len,
            f"Expected char count {expected_len}, got {q['response_text_length']}"
        )

    def test_skipped_text_question_length_is_none(self):
        """A skipped optional_text question must yield None, not 0."""
        skipped_text_record = {
            "patient_id":    "P-TEST-001",
            "question_id":   "SF-03",
            "answered":      False,
            "skipped":       True,
            "response_type": "optional_text",
            "answer":        None,
        }
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[skipped_text_record],
            enrollment_date=ENROLLMENT_DATE,
        )
        self.assertIsNone(
            payload["questions"][0]["response_text_length"],
            "Skipped text question must have response_text_length=None"
        )


# ---------------------------------------------------------------------------
# B5 — Structured response → response_text_length is None (not 0)
# ---------------------------------------------------------------------------

class TestB5_StructuredResponseLengthNull(unittest.TestCase):
    """B5: Structured/non-text responses must have response_text_length=None."""

    def _check_none_for_type(self, response_type: str, answer: str):
        record = {
            "patient_id":    "P-TEST-001",
            "question_id":   "Q-TEST",
            "answered":      True,
            "skipped":       False,
            "response_type": response_type,
            "answer":        answer,
        }
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[record],
            enrollment_date=ENROLLMENT_DATE,
        )
        q = payload["questions"][0]
        self.assertIsNone(
            q["response_text_length"],
            f"response_text_length must be None for response_type={response_type!r}"
        )

    def test_scale_1_5_is_none(self):
        self._check_none_for_type("scale_1_5", "4")

    def test_yes_no_is_none(self):
        self._check_none_for_type("yes_no", "yes")

    def test_multiple_choice_is_none(self):
        self._check_none_for_type("multiple_choice", "better")

    def test_multiple_choice_optional_text_is_none(self):
        self._check_none_for_type("multiple_choice_optional_text", "all")

    def test_yes_no_optional_text_is_none(self):
        self._check_none_for_type("yes_no_optional_text", "yes")

    def test_missing_response_type_is_none(self):
        """No response_type key in record → response_text_length must be None."""
        record = {
            "patient_id": "P-TEST-001",
            "question_id": "Q-TEST",
            "answered": True,
            "skipped": False,
            "answer": "some text",
            # response_type intentionally absent
        }
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[record],
            enrollment_date=ENROLLMENT_DATE,
        )
        self.assertIsNone(payload["questions"][0]["response_text_length"])


# ---------------------------------------------------------------------------
# B6 — enrollment_date preserved verbatim
# ---------------------------------------------------------------------------

class TestB6_EnrollmentDatePreserved(unittest.TestCase):
    """B6: enrollment_date is preserved exactly as supplied by the caller."""

    def test_enrollment_date_string_preserved(self):
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[],
            enrollment_date="2026-01-15",
        )
        self.assertEqual(payload["enrollment_date"], "2026-01-15")

    def test_enrollment_date_none_preserved(self):
        """None enrollment_date must appear as None in the payload — not omitted."""
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[],
            enrollment_date=None,
        )
        self.assertIn("enrollment_date", payload)
        self.assertIsNone(payload["enrollment_date"])

    def test_enrollment_date_not_modified(self):
        """Adapter must not validate, convert, or modify the enrollment_date value."""
        unusual_date = "2026-03-07T00:00:00+05:30"  # ISO datetime with tz
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[],
            enrollment_date=unusual_date,
        )
        self.assertEqual(payload["enrollment_date"], unusual_date)


# ---------------------------------------------------------------------------
# B7 — Timestamps preserved verbatim
# ---------------------------------------------------------------------------

class TestB7_TimestampsPreserved(unittest.TestCase):
    """B7: All session and per-question timestamps are preserved verbatim."""

    def setUp(self):
        self.payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_TEXT_ANSWER],
            enrollment_date=ENROLLMENT_DATE,
        )

    def test_session_start_time_preserved(self):
        self.assertEqual(
            self.payload["session_start_time"],
            _SESSION_COMPLETED["session_start_time"]
        )

    def test_session_end_time_preserved(self):
        self.assertEqual(
            self.payload["session_end_time"],
            _SESSION_COMPLETED["session_end_time"]
        )

    def test_question_presented_time_preserved(self):
        q = self.payload["questions"][0]
        self.assertEqual(
            q["question_presented_time"],
            _RECORD_TEXT_ANSWER["question_presented_time"]
        )

    def test_answer_submitted_time_preserved(self):
        q = self.payload["questions"][0]
        self.assertEqual(
            q["answer_submitted_time"],
            _RECORD_TEXT_ANSWER["answer_submitted_time"]
        )


# ---------------------------------------------------------------------------
# B8 — Missing optional fields handled safely
# ---------------------------------------------------------------------------

class TestB8_MissingOptionalFieldsSafe(unittest.TestCase):
    """
    B8: Older history records that pre-date session_demo.py may be missing
    session_id, question_order, question_presented_time, answer_submitted_time,
    and modality.  The adapter must not crash and must set those fields to None.
    """

    def setUp(self):
        # Use a session that also lacks optional fields.
        session_minimal = {
            "user_id":             "P-TEST-001",
            "session_status":      "completed",
            "questions_presented": 1,
            "questions_answered":  1,
            # session_id, session_start_time, session_end_time intentionally absent
        }
        self.payload = session_to_behaviour_payload(
            session=session_minimal,
            history_records=[_RECORD_MINIMAL],
            enrollment_date=ENROLLMENT_DATE,
        )

    def test_no_crash_on_missing_session_id(self):
        self.assertIsNone(self.payload["session_id"])

    def test_no_crash_on_missing_session_timestamps(self):
        self.assertIsNone(self.payload["session_start_time"])
        self.assertIsNone(self.payload["session_end_time"])

    def test_no_crash_on_missing_question_order(self):
        q = self.payload["questions"][0]
        self.assertIsNone(q["question_order"])

    def test_no_crash_on_missing_question_timestamps(self):
        q = self.payload["questions"][0]
        self.assertIsNone(q["question_presented_time"])
        self.assertIsNone(q["answer_submitted_time"])

    def test_no_crash_on_missing_modality(self):
        q = self.payload["questions"][0]
        self.assertIsNone(q["modality"])

    def test_patient_id_resolved_from_history(self):
        """Patient ID must resolve from the history record's patient_id field."""
        self.assertEqual(self.payload["patient_id"], "P-TEST-001")

    def test_patient_id_resolved_from_session_user_id(self):
        """When history record has no patient_id, fall back to session user_id."""
        record_no_pid = {
            "question_id":   "GW-01",
            "answered":      True,
            "skipped":       False,
            "response_type": "scale_1_5",
            "answer":        "3",
            # patient_id intentionally absent
        }
        session_with_uid = {
            "user_id":             "FALLBACK-001",
            "session_status":      "completed",
            "questions_presented": 1,
            "questions_answered":  1,
        }
        payload = session_to_behaviour_payload(
            session=session_with_uid,
            history_records=[record_no_pid],
            enrollment_date=ENROLLMENT_DATE,
        )
        self.assertEqual(payload["patient_id"], "FALLBACK-001")

    def test_patient_id_explicit_arg_takes_priority(self):
        """Explicit patient_id argument must take priority over history and session."""
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_ANSWERED_SCALE],
            enrollment_date=ENROLLMENT_DATE,
            patient_id="EXPLICIT-999",
        )
        self.assertEqual(payload["patient_id"], "EXPLICIT-999")

    def test_patient_id_none_when_no_source(self):
        """When no patient_id is available from any source, result is None."""
        empty_session = {
            "session_status":      "completed",
            "questions_presented": 0,
            "questions_answered":  0,
        }
        record_no_pid = {
            "question_id": "GW-01",
            "answered": True,
            "skipped": False,
        }
        payload = session_to_behaviour_payload(
            session=empty_session,
            history_records=[record_no_pid],
            enrollment_date=ENROLLMENT_DATE,
        )
        self.assertIsNone(payload["patient_id"])

    def test_empty_history_records_gives_empty_questions_list(self):
        """An empty history_records list must produce an empty questions list."""
        payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[],
            enrollment_date=ENROLLMENT_DATE,
        )
        self.assertEqual(payload["questions"], [])

    def test_non_dict_session_does_not_crash(self):
        """Non-dict session must not raise."""
        for bad in [None, [], "text", 42]:
            payload = session_to_behaviour_payload(
                session=bad,
                history_records=[],
                enrollment_date=ENROLLMENT_DATE,
            )
            self.assertIsInstance(payload, dict)

    def test_non_list_history_records_does_not_crash(self):
        """Non-list history_records must not raise."""
        for bad in [None, {}, "text"]:
            payload = session_to_behaviour_payload(
                session=_SESSION_COMPLETED,
                history_records=bad,
                enrollment_date=ENROLLMENT_DATE,
            )
            self.assertEqual(payload["questions"], [])


# ---------------------------------------------------------------------------
# B9 — Behaviour payload coexists with NLP and Voice signals in MedhaState
# ---------------------------------------------------------------------------

class TestB9_BehaviourPayloadCoexistsWithNLPAndVoice(unittest.TestCase):
    """
    B9: The Behaviour raw payload must coexist with NLP and Voice signals
    inside a single MedhaState without conflict.

    - behaviour_payload_to_state() stores the payload informatively under
      patient_context["behaviour_payload"].
    - NLP signals remain in patient_context["nlp_signals"].
    - Voice signals remain in patient_context["speech_signals"].
    - No QE trigger flag is activated by this adapter.
    - select_next_question() runs without error.
    """

    # Verbatim Voice Engine payload (matches fixtures in test_state_integration.py).
    _VOICE_PAYLOAD = {
        "patient_id":       "patient_001",
        "timestamp":        "2026-08-30T10:41:02.754967",
        "voice_available":  True,
        "voice_features": {
            "voice_distress":          0.1605,
            "voice_confidence":        0.7413,
            "pause_ratio":             0,
            "speech_rate_deviation":   0.4667,
            "energy_deviation":        0.317,
            "acoustic_indicator":      0.4375,
        },
        "fusion_features": {
            "voice_available":         1,
            "voice_distress":          0.1605,
            "pause_ratio":             0,
            "speech_rate_deviation":   0.4667,
            "energy_deviation":        0.317,
            "acoustic_indicator":      0.4375,
        },
        "speech": {
            "transcript":              "You did.",
            "language":               "en",
            "language_probability":   0.9674,
            "speech_rate_wpm":        80,
        },
        "raw_features": {
            "emotion_probabilities": {
                "neu": 0.0378, "hap": 0.7413,
                "ang": 0.2199, "sad": 0.001,
            },
            "acoustic_features": {
                "duration_seconds":     1.5,
                "rms_energy":           0.01366,
                "pitch_mean":           400.21,
                "pitch_std":            266.28,
                "zero_crossing_rate":   0.09227,
            },
        },
        "history_records": 2,
    }

    _NLP_OUTPUT = {
        "mentioned_emotions":       ["worried"],
        "mentioned_problems":       ["sleep"],
        "linked_case_event":        "hearing",
        "sleep_issue":              True,
        "social_support_issue":     None,
        "safety_concern_mentioned": None,
        "needs_human_followup":     None,
        "confidence":               0.85,
    }

    def setUp(self):
        from test_engine import select_next_question
        self.select_next_question = select_next_question

        self.payload = session_to_behaviour_payload(
            session=_SESSION_COMPLETED,
            history_records=[_RECORD_TEXT_ANSWER, _RECORD_ANSWERED_SCALE],
            enrollment_date=ENROLLMENT_DATE,
        )

        self.state = MedhaState(scheduled_checkin_due=True)
        # Apply all three model signals.
        self.state.update(behaviour_payload_to_state(self.payload))
        self.state.update(nlp_signals_to_state(self._NLP_OUTPUT))
        self.state.update(speech_signals_to_state(self._VOICE_PAYLOAD))

    def test_behaviour_payload_stored_in_patient_context(self):
        state_dict = self.state.to_dict()
        self.assertIn(
            "behaviour_payload", state_dict["patient_context"],
            "behaviour_payload must appear in patient_context"
        )

    def test_nlp_signals_still_present(self):
        state_dict = self.state.to_dict()
        self.assertIn(
            "nlp_signals", state_dict["patient_context"],
            "nlp_signals must still be present after behaviour_payload merge"
        )

    def test_voice_signals_still_present(self):
        state_dict = self.state.to_dict()
        self.assertIn(
            "speech_signals", state_dict["patient_context"],
            "speech_signals must still be present after behaviour_payload merge"
        )

    def test_behaviour_payload_does_not_activate_any_qe_trigger(self):
        """behaviour_payload_to_state() must NOT activate any QE trigger flag."""
        from medha_state import _QE_TRIGGER_DEFAULTS
        partial = behaviour_payload_to_state(self.payload)
        for trigger_key in _QE_TRIGGER_DEFAULTS:
            self.assertNotIn(
                trigger_key, partial,
                f"Adapter must not set QE trigger '{trigger_key}'"
            )
        self.assertEqual(set(partial.keys()), {"patient_context"})

    def test_payload_fields_intact_in_state(self):
        """All Behaviour payload top-level fields must be inside the stored payload."""
        stored = self.state.to_dict()["patient_context"]["behaviour_payload"]
        for field in (
            "patient_id", "enrollment_date", "session_id",
            "session_start_time", "session_end_time",
            "session_status", "questions_presented", "questions_answered",
            "questions",
        ):
            self.assertIn(
                field, stored,
                f"Field '{field}' must be present in stored behaviour_payload"
            )

    def test_qe_runs_cleanly_after_all_three_signals(self):
        """select_next_question() must run without error after all three signals."""
        question = self.select_next_question(self.state.to_dict(), [])
        self.assertIsNotNone(
            question,
            "QE must return a question when scheduled_checkin_due=True"
        )

    def test_behaviour_payload_to_state_empty_returns_empty(self):
        """Non-dict / empty payload must return {} without raising."""
        for bad in [None, {}, [], "text", 42]:
            result = behaviour_payload_to_state(bad)
            self.assertEqual(result, {})

    def test_all_three_signals_in_patient_context(self):
        """All three signal namespaces must coexist without overwriting each other."""
        state_dict = self.state.to_dict()
        ctx = state_dict["patient_context"]
        self.assertIn("behaviour_payload", ctx)
        self.assertIn("nlp_signals", ctx)
        self.assertIn("speech_signals", ctx)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_behaviour_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestB1_CompletedSession,
        TestB2_AbandonedSession,
        TestB3_AnsweredAndSkipped,
        TestB4_TextResponseLength,
        TestB5_StructuredResponseLengthNull,
        TestB6_EnrollmentDatePreserved,
        TestB7_TimestampsPreserved,
        TestB8_MissingOptionalFieldsSafe,
        TestB9_BehaviourPayloadCoexistsWithNLPAndVoice,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 62)
    total    = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passed   = total - failures
    print(
        f"BEHAVIOUR ADAPTER TESTS: {passed} passed, {failures} failed"
        f"  (of {total} total)"
    )
    print("=" * 62)
    return result


if __name__ == "__main__":
    run_behaviour_tests()
