"""
test_structured_risk_adapter.py
================================
Unit and integration tests for the Question Engine -> Structured Risk Engine adapter.

Tests covered:
1. Exact 7-field schema contract verification:
   All 7 keys ("Mood", "Stress", "Sleep", "Functioning", "Safety",
   "Social_Support_Checkin", "Self_Reported_Wellbeing") must always be present.
2. Missing / empty / None input handling:
   Missing fields remain None; values are never invented or defaulted.
3. Extraction from patient_context / current_state:
   Verifies exact mapping from patient_context["current_state"].
4. Extraction from live session interaction records:
   Verifies mapping of SF-01 (sleep), SE-01 (social support), GW-01 (wellbeing/mood),
   SF-02 (functioning), SA-01 (safety), ES-02/ES-06 (stress).
5. Unanswered / skipped interaction records are safely ignored.
6. Merging / precedence:
   Live interaction records take precedence over baseline current_state.
7. Storage into MedhaState:
   structured_risk_payload_to_state() stores the payload into
   patient_context["structured_risk_payload"] without activating any QE triggers.
8. Compatibility with model_adapters exports.
"""

import unittest
from medha_state import MedhaState
from structured_risk_adapter import (
    REQUIRED_STRUCTURED_RISK_FIELDS,
    extract_structured_risk_payload,
    structured_risk_payload_to_state,
)
from model_adapters import (
    extract_structured_risk_payload as ma_extract_payload,
    structured_risk_payload_to_state as ma_payload_to_state,
    REQUIRED_STRUCTURED_RISK_FIELDS as MA_REQUIRED_FIELDS,
)


class TestStructuredRiskAdapterSchema(unittest.TestCase):
    """Verify exact schema and 7 required field names."""

    def test_required_fields_exact_names(self):
        expected_fields = (
            "Mood",
            "Stress",
            "Sleep",
            "Functioning",
            "Safety",
            "Social_Support_Checkin",
            "Self_Reported_Wellbeing",
        )
        self.assertEqual(REQUIRED_STRUCTURED_RISK_FIELDS, expected_fields)
        self.assertEqual(MA_REQUIRED_FIELDS, expected_fields)

    def test_empty_source_returns_all_7_none_fields(self):
        """When given None or empty input, all 7 fields must be present and set to None."""
        payload = extract_structured_risk_payload(None)
        self.assertEqual(len(payload), 7)
        self.assertEqual(set(payload.keys()), set(REQUIRED_STRUCTURED_RISK_FIELDS))
        for k in REQUIRED_STRUCTURED_RISK_FIELDS:
            self.assertIsNone(payload[k], f"Field '{k}' should be None when unprovided")

    def test_empty_dict_returns_all_7_none_fields(self):
        payload = extract_structured_risk_payload({})
        self.assertEqual(len(payload), 7)
        self.assertEqual(set(payload.keys()), set(REQUIRED_STRUCTURED_RISK_FIELDS))
        for k in REQUIRED_STRUCTURED_RISK_FIELDS:
            self.assertIsNone(payload[k])


class TestExtractionFromPatientContext(unittest.TestCase):
    """Verify extraction from patient_context / current_state."""

    def test_patient_context_with_all_fields(self):
        patient_context = {
            "victim_id": "V0001",
            "current_state": {
                "Mood": 3.0,
                "Stress": 4.0,
                "Sleep": 2.0,
                "Functioning": 3.0,
                "Safety": 4.0,
                "Social_Support_Checkin": 2.0,
                "Self_Reported_Wellbeing": 3.0,
            }
        }
        payload = extract_structured_risk_payload(patient_context=patient_context)
        self.assertEqual(payload["Mood"], 3.0)
        self.assertEqual(payload["Stress"], 4.0)
        self.assertEqual(payload["Sleep"], 2.0)
        self.assertEqual(payload["Functioning"], 3.0)
        self.assertEqual(payload["Safety"], 4.0)
        self.assertEqual(payload["Social_Support_Checkin"], 2.0)
        self.assertEqual(payload["Self_Reported_Wellbeing"], 3.0)

    def test_patient_context_with_partial_fields(self):
        patient_context = {
            "current_state": {
                "Mood": 4.0,
                "Sleep": 3.0,
                "Safety": 5.0,
            }
        }
        payload = extract_structured_risk_payload(patient_context=patient_context)
        self.assertEqual(payload["Mood"], 4.0)
        self.assertEqual(payload["Sleep"], 3.0)
        self.assertEqual(payload["Safety"], 5.0)
        self.assertIsNone(payload["Stress"])
        self.assertIsNone(payload["Functioning"])
        self.assertIsNone(payload["Social_Support_Checkin"])
        self.assertIsNone(payload["Self_Reported_Wellbeing"])

    def test_direct_current_state_dict(self):
        current_state = {
            "Mood": 2,
            "Stress": 5,
            "Sleep": 1,
            "Functioning": 2,
            "Safety": 3,
            "Social_Support_Checkin": 4,
            "Self_Reported_Wellbeing": 2,
        }
        payload = extract_structured_risk_payload(current_state)
        self.assertEqual(payload["Mood"], 2)
        self.assertEqual(payload["Stress"], 5)
        self.assertEqual(payload["Sleep"], 1)
        self.assertEqual(payload["Functioning"], 2)
        self.assertEqual(payload["Safety"], 3)
        self.assertEqual(payload["Social_Support_Checkin"], 4)
        self.assertEqual(payload["Self_Reported_Wellbeing"], 2)


class TestExtractionFromInteractionRecords(unittest.TestCase):
    """Verify extraction from live session interaction records."""

    def test_session_interaction_records_extraction(self):
        records = [
            {
                "question_id": "GW-01",
                "answered": True,
                "skipped": False,
                "response_type": "scale_1_5",
                "answer": "4",
                "structured_output": {"wellbeing_score": 4}
            },
            {
                "question_id": "SF-01",
                "answered": True,
                "skipped": False,
                "response_type": "scale_1_5",
                "answer": "2",
                "structured_output": {"sleep_score": 2}
            },
            {
                "question_id": "SE-01",
                "answered": True,
                "skipped": False,
                "response_type": "scale_1_5",
                "answer": "3",
                "structured_output": {"perceived_support_score": 3}
            },
            {
                "question_id": "SF-02",
                "answered": True,
                "skipped": False,
                "response_type": "multiple_choice",
                "answer": "mostly",
                "structured_output": {"functioning_level": "mostly"}
            },
            {
                "question_id": "SA-01",
                "answered": True,
                "skipped": False,
                "response_type": "yes_no",
                "answer": "yes",
                "structured_output": {"feels_safe": True}
            },
            {
                "question_id": "ES-02",
                "answered": True,
                "skipped": False,
                "response_type": "scale_1_5",
                "answer": "4",
                "structured_output": {"event_coping_score": 4}
            },
        ]
        payload = extract_structured_risk_payload(records)
        self.assertEqual(payload["Self_Reported_Wellbeing"], 4)
        self.assertEqual(payload["Mood"], 4)
        self.assertEqual(payload["Sleep"], 2)
        self.assertEqual(payload["Social_Support_Checkin"], 3)
        self.assertEqual(payload["Functioning"], "mostly")
        self.assertEqual(payload["Safety"], True)
        self.assertEqual(payload["Stress"], 4)

    def test_skipped_and_unanswered_records_ignored(self):
        records = [
            {
                "question_id": "SF-01",
                "answered": False,
                "skipped": True,
                "answer": None,
                "structured_output": None
            },
            {
                "question_id": "SE-01",
                "answered": False,
                "skipped": False,
                "answer": None,
                "structured_output": None
            }
        ]
        payload = extract_structured_risk_payload(records)
        self.assertIsNone(payload["Sleep"])
        self.assertIsNone(payload["Social_Support_Checkin"])


class TestMergeAndPrecedence(unittest.TestCase):
    """Verify live history updates baseline context."""

    def test_session_records_override_baseline_context(self):
        patient_context = {
            "current_state": {
                "Mood": 2.0,
                "Stress": 4.0,
                "Sleep": 1.0,
                "Functioning": 2.0,
                "Safety": 3.0,
                "Social_Support_Checkin": 1.0,
                "Self_Reported_Wellbeing": 2.0,
            }
        }
        # In current session, sleep and social support improved
        session_records = [
            {
                "question_id": "SF-01",
                "answered": True,
                "skipped": False,
                "answer": "4",
                "structured_output": {"sleep_score": 4}
            },
            {
                "question_id": "SE-01",
                "answered": True,
                "skipped": False,
                "answer": "5",
                "structured_output": {"perceived_support_score": 5}
            }
        ]
        payload = extract_structured_risk_payload(
            patient_context=patient_context,
            history_records=session_records
        )
        # Updated from live session
        self.assertEqual(payload["Sleep"], 4)
        self.assertEqual(payload["Social_Support_Checkin"], 5)
        # Preserved from baseline
        self.assertEqual(payload["Mood"], 2.0)
        self.assertEqual(payload["Stress"], 4.0)
        self.assertEqual(payload["Functioning"], 2.0)
        self.assertEqual(payload["Safety"], 3.0)
        self.assertEqual(payload["Self_Reported_Wellbeing"], 2.0)


class TestStateIntegration(unittest.TestCase):
    """Verify integration with MedhaState."""

    def test_structured_risk_payload_to_state(self):
        payload = {
            "Mood": 3,
            "Stress": 2,
            "Sleep": 4,
            "Functioning": 4,
            "Safety": 5,
            "Social_Support_Checkin": 3,
            "Self_Reported_Wellbeing": 3,
        }
        state_update = structured_risk_payload_to_state(payload)
        self.assertIn("patient_context", state_update)
        self.assertIn("structured_risk_payload", state_update["patient_context"])
        self.assertEqual(
            state_update["patient_context"]["structured_risk_payload"],
            payload
        )

        # Apply to MedhaState
        state = MedhaState(scheduled_checkin_due=True)
        state.update(state_update)

        state_dict = state.to_dict()
        self.assertEqual(
            state_dict["patient_context"]["structured_risk_payload"],
            payload
        )
        # Ensure no trigger flags were accidentally set
        self.assertFalse(state_dict["safety_intent_active"])
        self.assertFalse(state_dict["functioning_trend_declining"])


if __name__ == "__main__":
    unittest.main()
