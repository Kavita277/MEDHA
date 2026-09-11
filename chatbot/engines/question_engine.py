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
            "Safety": ["SA-01", "SA-02", "SA-03"],
            "Stress": ["ES-01", "ES-02", "ES-03", "ES-06"],
            "Sleep": ["SF-01", "SF-03", "SF-05"],
            "Functioning": ["SF-02", "SF-05"],
            "Social_Support_Checkin": ["SE-01", "SE-02", "SE-03"],
            "Mood": ["GW-01", "GW-03"],
            "Self_Reported_Wellbeing": ["GW-01", "GW-03", "GW-05"],
        }

    def _load_questions(self) -> List[Dict[str, Any]]:
        try:
            with open(self.question_bank_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("questions", [])
        except Exception as e:
            logger.error(f"Failed to load question bank from {self.question_bank_path}: {e}")
            return []

    def select_random_checkin_questions(
        self,
        count: Optional[int] = None,
        state: Optional[MedhaState] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generates a randomized sequence of 10 to 15 questions for a comprehensive check-in session.
        Stratified across the 5 authoritative clinical domains:
          - SA: Safety & Immediate Support (Priority 1)
          - ES: Event-Related Stress (Priority 2)
          - SF: Sleep & Daily Functioning (Priority 3)
          - SE: Social & Emotional Support (Priority 3)
          - GW: General Wellbeing & Mood (Priority 4)
        Questions are randomly sampled within each domain and ordered by clinical priority.
        """
        if not self.questions:
            return []

        import random

        by_series: Dict[str, List[Dict[str, Any]]] = {
            "SA": [],
            "ES": [],
            "SF": [],
            "SE": [],
            "GW": [],
        }
        other_qs: List[Dict[str, Any]] = []

        for q in self.questions:
            q_id = q.get("question_id", "")
            prefix = q_id.split("-")[0] if "-" in q_id else q_id[:2]
            if prefix in by_series:
                by_series[prefix].append(q)
            else:
                other_qs.append(q)

        # Target between 10 and 15 questions
        target_count = count if count is not None else random.randint(10, 15)
        target_count = min(target_count, len(self.questions))
        target_count = max(target_count, min(10, len(self.questions)))

        # Baseline: sample 2 questions from each of the 5 domains (= 10 questions)
        selected_by_domain: Dict[str, List[Dict[str, Any]]] = {}
        for prefix, qs in by_series.items():
            shuffled = list(qs)
            random.shuffle(shuffled)
            take = min(2, len(shuffled))
            selected_by_domain[prefix] = shuffled[:take]

        # Remaining candidate pool across domains to reach target_count
        current_total = sum(len(v) for v in selected_by_domain.values())
        remainder = target_count - current_total

        remaining_candidates = []
        for prefix, qs in by_series.items():
            already_selected_ids = {q["question_id"] for q in selected_by_domain[prefix]}
            for q in qs:
                if q["question_id"] not in already_selected_ids:
                    remaining_candidates.append(q)

        random.shuffle(remaining_candidates)
        if remainder > 0:
            extra = remaining_candidates[:remainder]
            for q in extra:
                prefix = q["question_id"].split("-")[0] if "-" in q["question_id"] else q["question_id"][:2]
                if prefix in selected_by_domain:
                    selected_by_domain[prefix].append(q)
                else:
                    selected_by_domain.setdefault(prefix, []).append(q)

        # Flatten in clinical priority order: SA -> ES -> SF -> SE -> GW
        priority_order = ["SA", "ES", "SF", "SE", "GW"]
        final_list: List[Dict[str, Any]] = []
        for prefix in priority_order:
            if prefix in selected_by_domain:
                dom_qs = selected_by_domain[prefix]
                random.shuffle(dom_qs)
                final_list.extend(dom_qs)

        return final_list

    def select_next_question(
        self,
        state: MedhaState,
        **kwargs: Any,
    ) -> Optional[QuestionRecord]:
        """
        Selects the single most appropriate question, or None if no question is needed.
        Supports daily check-in rotation: ensures a fresh, clinically appropriate question
        is selected every day without repeating questions asked today.
        """
        if not self.questions:
            return None

        # 1. Frequency check: ensure we haven't asked a question recently in this turn.
        # 2. Determine missing core features
        missing_features = self._get_missing_core_features(state)

        # 3. Filter candidates based on missingness, triggers, and cooldowns
        candidate_questions = []
        now = datetime.now(timezone.utc)

        # First priority: missing core features off cooldown
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

        # Daily Check-in Rotation Fallback:
        # If no missing features are pending (or all core features have values),
        # only select a new question for daily longitudinal monitoring if explicitly requested.
        allow_daily_fallback = kwargs.get("allow_daily_fallback", False)
        if not candidate_questions and allow_daily_fallback:
            daily_candidates = []
            for q in self.questions:
                q_id = q["question_id"]
                # Must not have been asked in the last 20 hours
                if self._is_asked_today(q_id, state, now):
                    continue

                # Must belong to an active clinical monitoring domain
                is_monitoring_domain = any(q_id in triggers for triggers in self.feature_triggers.values())
                if is_monitoring_domain:
                    # Calculate how many times this question has been asked in history
                    ask_count = sum(1 for r in state.question_history if r.question_id == q_id)
                    daily_candidates.append((ask_count, q.get("priority", 99), q))

            if daily_candidates:
                # Prioritize: 1) least asked in history (newest questions), 2) clinical priority
                daily_candidates.sort(key=lambda x: (x[0], x[1]))
                candidate_questions.append(daily_candidates[0][2])

        if not candidate_questions:
            return None

        # Sort candidates by priority (ascending, so 1 is highest priority)
        candidate_questions.sort(key=lambda x: x.get("priority", 99))
        best_q = candidate_questions[0]
        
        # Calculate cooldown_until (cooldown for daily questions set to 1 day so tomorrow gets a new question)
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

    def _is_asked_today(self, question_id: str, state: MedhaState, now: datetime) -> bool:
        """
        Returns True if the question was already asked today (within the last 20 hours).
        """
        cutoff = now - timedelta(hours=20)
        for record in reversed(state.question_history):
            if record.question_id == question_id:
                try:
                    asked = datetime.fromisoformat(record.asked_at).replace(tzinfo=timezone.utc)
                    if asked >= cutoff:
                        return True
                except Exception:
                    pass
        return False
