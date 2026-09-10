"""
Unit and Integration Tests for MEDHA Question Engine (Step 7)
=============================================================

Verifies:
1. Missing mood -> triggers GW-01.
2. Missing sleep -> triggers SF-01.
3. Known sleep -> suppresses SF-01.
4. Repeated question prevention (cooldowns).
5. Maximum question frequency (only selects one highest priority).
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from chatbot.engines.question_engine import DeterministicQuestionEngine
from chatbot.state.medha_state import MedhaState, QuestionRecord

@pytest.fixture
def engine():
    # Provide the path to the real json file
    return DeterministicQuestionEngine(question_bank_path="engine/QuestionEngine/questions.json")


def test_missing_mood_triggers_GW01(engine):
    """If Self_Reported_Wellbeing/Mood is missing, the highest priority missing core is selected."""
    state = MedhaState(victim_id="V1", timepoint=1)
    
    # Fill in all other features to isolate Mood/Wellbeing
    state.structured_features["Safety"] = 1.0
    state.structured_features["Stress"] = 1.0
    state.structured_features["Sleep"] = 3.0
    state.structured_features["Functioning"] = 3.0
    state.structured_features["Social_Support_Checkin"] = 3.0
    
    # Self_Reported_Wellbeing and Mood remain None
    record = engine.select_next_question(state)
    
    assert record is not None
    assert record.question_id == "GW-01"


def test_missing_sleep_triggers_SF01(engine):
    """If Sleep is missing, it should trigger SF-01."""
    state = MedhaState(victim_id="V1", timepoint=1)
    
    # Saftey is Priority 1, Stress is Priority 2, Sleep is Priority 3
    # If all higher priorities are filled, Sleep should trigger.
    state.structured_features["Safety"] = 1.0
    state.structured_features["Stress"] = 2.0
    # Sleep is missing
    state.structured_features["Functioning"] = 3.0
    state.structured_features["Social_Support_Checkin"] = 3.0
    state.structured_features["Self_Reported_Wellbeing"] = 3.0
    state.structured_features["Mood"] = 3.0
    
    record = engine.select_next_question(state)
    
    assert record is not None
    assert record.question_id == "SF-01"


def test_known_sleep_suppresses_SF01(engine):
    """If Sleep is known (either in structured or candidate), SF-01 is skipped."""
    state = MedhaState(victim_id="V1", timepoint=1)
    
    state.structured_features["Safety"] = 1.0
    state.structured_features["Stress"] = 2.0
    
    # Instead of missing, sleep is known in candidate observations
    state.add_candidate_observation(domain="sleep", semantic_value="poor", evidence="x")
    
    state.structured_features["Functioning"] = 3.0
    state.structured_features["Social_Support_Checkin"] = 3.0
    state.structured_features["Self_Reported_Wellbeing"] = 3.0
    state.structured_features["Mood"] = 3.0
    
    # Everything is known (either structured or candidate)
    record = engine.select_next_question(state)
    
    # Should not trigger anything, or at least not SF-01.
    # Since everything core is filled, it should be None.
    assert record is None


def test_repeated_question_prevention(engine):
    """If SF-01 was asked recently (inside cooldown), it shouldn't be asked again."""
    state = MedhaState(victim_id="V1", timepoint=1)
    
    state.structured_features["Safety"] = 1.0
    state.structured_features["Stress"] = 2.0
    # Sleep is missing
    
    now = datetime.now(timezone.utc)
    cooldown_future = (now + timedelta(days=2)).isoformat()
    
    # Record that SF-01 was asked just now
    state.record_question_asked(
        question_id="SF-01",
        question_text="How is your sleep?",
        intent="sleep",
        cooldown_until=cooldown_future
    )
    
    record = engine.select_next_question(state)
    
    # Sleep is missing, but SF-01 is on cooldown. 
    # Because everything else is missing too (Functioning, Social, Wellbeing),
    # the engine should pick the next highest priority available (Functioning -> SF-02).
    assert record is not None
    assert record.question_id != "SF-01"
    assert record.question_id == "SF-02"


def test_maximum_question_frequency(engine):
    """Engine only returns ONE question per call (the highest priority one)."""
    state = MedhaState(victim_id="V1", timepoint=1)
    
    # EVERYTHING is missing
    # Priority 1: Safety (SA-01)
    record = engine.select_next_question(state)
    
    assert record is not None
    assert record.question_id == "SA-01"
