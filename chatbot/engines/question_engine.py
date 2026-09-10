"""
Deterministic Question Engine
=============================

Selects the next question from the controlled question bank based on
missing information, cooldowns, and strict priority.
Does NOT use LLMs to invent clinical questioning strategy.
"""

import json
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

from chatbot.interfaces import QuestionEngineProtocol
from chatbot.state.medha_state import MedhaState, QuestionRecord

logger = logging.getLogger(__name__)


def _current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class DeterministicQuestionEngine(QuestionEngineProtocol):
    """
    Deterministic rule-based policy for selecting the next MEDHA question.
    """

    def __init__(self, question_bank_path: str = "engine/QuestionEngine/questions.json"):
        self.question_bank_path = question_bank_path
        self.questions = self._load_questions()

        # Map target missing features -> question_id
        # Priority mapping is derived from questions.json (lower number = higher priority)
        # Priority 1: SA-01, SA-02, SA-03, SA-04
        # Priority 2: ES-01, ES-02, ES-03, ES-06
        # Priority 3: SF-01, SF-02, SF-03, SF-05, SE-01, SE-02, SE-03
        # Priority 4: GW-01, GW-03, GW-05, GW-06
        
        self.feature_triggers = {
            "Safety": ["SA-01"],
            "Stress": ["ES-01", "ES-02"],
            "Sleep": ["SF-01"],
            "Functioning": ["SF-02"],
            "Social_Support_Checkin": ["SE-01"],
            "Mood": ["GW-01"],
            "Self_Reported_Wellbeing": ["GW-01"],
        }

    def _load_questions(self) -> List[Dict[str, Any]]:
        try:
            with open(self.question_bank_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("questions", [])
        except Exception as e:
            logger.error(f"Failed to load question bank from {self.question_bank_path}: {e}")
            return []

    def select_next_question(
        self,
        state: MedhaState,
        **kwargs: Any,
    ) -> Optional[QuestionRecord]:
        """
        Selects the single most appropriate question, or None if no question is needed.
        """
        if not self.questions:
            return None

        # 1. Frequency check: ensure we haven't asked a question recently in this turn.
        # We can check if any question was added to the history in the last few seconds.
        # However, typically the conversation manager calls this once per user message.
        # We just need to make sure we don't ask multiple questions. Since we return one, 
        # the ConversationManager will append it to state.

        # 2. Determine missing core features
        missing_features = self._get_missing_core_features(state)

        # 3. Filter candidates based on missingness, triggers, and cooldowns
        candidate_questions = []

        now = datetime.now(timezone.utc)

        for q in self.questions:
            q_id = q["question_id"]

            # Cooldown check
            if not self._is_off_cooldown(q_id, state, now, q.get("cooldown_days", 1)):
                continue
                
            # If the feature is missing, this question is a candidate
            is_triggered = False
            for feature, triggers in self.feature_triggers.items():
                if feature in missing_features and q_id in triggers:
                    is_triggered = True
                    break
                    
            if not is_triggered:
                continue

            candidate_questions.append(q)

        if not candidate_questions:
            return None

        # 4. Sort by priority (ascending, so 1 is highest priority)
        # Fallback to 99 if priority is missing
        candidate_questions.sort(key=lambda x: x.get("priority", 99))

        best_q = candidate_questions[0]
        
        # Calculate cooldown_until
        cooldown_days = best_q.get("cooldown_days", 1)
        cooldown_until = (now + timedelta(days=cooldown_days)).isoformat()

        record = QuestionRecord(
            question_id=best_q["question_id"],
            question_text=best_q["question"],
            intent=best_q.get("intent", "unknown"),
            asked_at=_current_iso_timestamp(),
            answered=False,
            cooldown_until=cooldown_until
        )

        return record

    def _get_missing_core_features(self, state: MedhaState) -> Set[str]:
        """
        Returns a set of core feature names that are considered 'missing'.
        A feature is missing if it's None in structured_features AND
        not present in the current candidate_observations.
        """
        missing = set()
        
        # We also need to map the semantic observation domains to the V2 structured names
        # to ensure we don't ask for Sleep if "sleep: poor" is in candidate_observations.
        domain_to_feature = {
            "sleep": "Sleep",
            "mood": "Mood",
            "stress": "Stress",
            "functioning": "Functioning",
            "safety": "Safety",
            "social_support": "Social_Support_Checkin",
            "wellbeing": "Self_Reported_Wellbeing"
        }
        
        # Collect what is known in candidates
        known_candidates = set()
        for obs in state.candidate_observations:
            domain = obs.domain
            if domain in domain_to_feature:
                known_candidates.add(domain_to_feature[domain])

        # Check all tracked features
        for feature in self.feature_triggers.keys():
            val = state.structured_features.get(feature)
            # It's missing if it is None or NaN
            is_struct_missing = val is None or (isinstance(val, float) and math.isnan(val))
            
            if is_struct_missing and feature not in known_candidates:
                missing.add(feature)
                
        return missing

    def _is_off_cooldown(self, question_id: str, state: MedhaState, now: datetime, default_cooldown_days: int) -> bool:
        """
        Checks if the question has passed its cooldown period based on history.
        """
        for record in reversed(state.question_history):
            if record.question_id == question_id:
                if record.cooldown_until:
                    try:
                        cooldown_end = datetime.fromisoformat(record.cooldown_until).replace(tzinfo=timezone.utc)
                        if now < cooldown_end:
                            return False
                    except ValueError:
                        pass
                
                # Fallback check if cooldown_until was not correctly stored
                try:
                    asked = datetime.fromisoformat(record.asked_at).replace(tzinfo=timezone.utc)
                    if now < asked + timedelta(days=default_cooldown_days):
                        return False
                except ValueError:
                    pass
        return True
