"""
MEDHA State Representation
==========================

Central model-agnostic session and longitudinal state container for the
MEDHA Chatbot Orchestration Layer.

Stores everything the chatbot needs before preparing information for
the frozen MEDHA V2 predictive pipeline.

CRITICAL RULES:
1. Missing information remains missing (None / NaN).
2. Never convert unknown values into 0.0 or default scores.
3. Never fabricate feature values or model outputs.
4. Never calculate DDS, Future Risk, or call ML models / LLMs.
5. All feature names strictly match canonical V2 definitions.
"""

from __future__ import annotations

import copy
import json
import math
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

# ===========================================================================
# CANONICAL V2 FEATURE REGISTRIES (Discovered in Step 0)
# ===========================================================================

STRUCTURED_CATEGORICAL_FEATURES: Tuple[str, ...] = (
    "Case_Type",
    "Case_Stage",
    "Episode_Severity",
)

STRUCTURED_NUMERIC_FEATURES: Tuple[str, ...] = (
    "Checkin_Available",
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",
    "Threat_Event",
    "Upcoming_Hearing",
    "Hearing_Completed",
    "Investigation_Delay",
    "Compensation_Delay",
    "Relocation_Stress",
    "Rehabilitation_Issue",
    "Protection_Event",
    "Family_Support",
    "Social_Support",
    "Therapist_Engagement",
    "Access_To_Services",
    "Stable_Housing",
    "Other_Protective_Factors",
    "Recent_Episode",
    "Family_Reported_Episode",
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Hours",
    "Response_Delay_Deviation",
    "Baseline_Response_Delay",
    "Baseline_Engagement",
    "Baseline_Checkin_Distress",
    "Behaviour_Trend",
    "Engagement_Trend",
    "Diary_Available",
    "Therapist_Observation_Available",
    "Therapist_Observation_Score",
)

STRUCTURED_FEATURES: Tuple[str, ...] = (
    STRUCTURED_CATEGORICAL_FEATURES + STRUCTURED_NUMERIC_FEATURES
)  # Exactly 42 features

TEXT_FEATURES: Tuple[str, ...] = (
    "Text_Distress",
    "Fear",
    "Threat_Context",
    "Negative_Affect",
    "Urgency",
)  # Exactly 5 features

VOICE_FEATURES: Tuple[str, ...] = (
    "Voice_Distress",
    "Pause_Ratio",
    "Speech_Rate_Deviation",
    "Energy_Deviation",
    "Acoustic_Indicator",
)  # Exactly 5 features

BEHAVIOUR_FEATURES: Tuple[str, ...] = (
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Hours",
    "Response_Delay_Deviation",
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
    "Baseline_Response_Delay",
    "Baseline_Engagement",
    "Behaviour_Trend",
)  # Exactly 10 features

VALID_MODALITIES: Tuple[str, ...] = (
    "structured",
    "text",
    "voice",
    "behaviour",
)


def _current_iso_timestamp() -> str:
    """Returns current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


# ===========================================================================
# DATA STRUCTURES
# ===========================================================================

@dataclass
class ChatMessage:
    """Represents a single message in the conversation history."""
    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: str = field(default_factory=_current_iso_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChatMessage:
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", _current_iso_timestamp()),
            metadata=copy.deepcopy(data.get("metadata", {})),
        )


@dataclass
class QuestionRecord:
    """Represents an interaction item in the Question History."""
    question_id: str
    question_text: str
    intent: str
    asked_at: str = field(default_factory=_current_iso_timestamp)
    answered: bool = False
    response_text: Optional[str] = None
    cooldown_until: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QuestionRecord:
        return cls(
            question_id=data["question_id"],
            question_text=data["question_text"],
            intent=data["intent"],
            asked_at=data.get("asked_at", _current_iso_timestamp()),
            answered=bool(data.get("answered", False)),
            response_text=data.get("response_text"),
            cooldown_until=data.get("cooldown_until"),
            metadata=copy.deepcopy(data.get("metadata", {})),
        )


@dataclass
class CandidateObservation:
    """
    Represents an unverified, qualitative, or extracted semantic observation.
    Must NOT be converted into arbitrary V2 numbers unless authoritatively mapped.
    """
    domain: str
    semantic_value: Any
    evidence: Optional[str] = None
    timestamp: str = field(default_factory=_current_iso_timestamp)
    status: str = "candidate"  # "candidate", "mapped", "unresolved"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CandidateObservation:
        return cls(
            domain=data["domain"],
            semantic_value=data["semantic_value"],
            evidence=data.get("evidence"),
            timestamp=data.get("timestamp", _current_iso_timestamp()),
            status=data.get("status", "candidate"),
        )


@dataclass
class ContextEvent:
    """Represents contextual case or life events."""
    event_type: str
    description: str
    timestamp: str = field(default_factory=_current_iso_timestamp)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ContextEvent:
        return cls(
            event_type=data["event_type"],
            description=data["description"],
            timestamp=data.get("timestamp", _current_iso_timestamp()),
            metadata=copy.deepcopy(data.get("metadata", {})),
        )


@dataclass
class PreviousPrediction:
    """Records historical or previous V2 prediction results."""
    timepoint: int
    fusion_dds: Optional[float] = None
    temporal_risk: Optional[float] = None
    temporal_available: Optional[int] = None
    future_escalation_flag: Optional[int] = None
    priority_level: Optional[str] = None
    timestamp: str = field(default_factory=_current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PreviousPrediction:
        return cls(
            timepoint=int(data["timepoint"]),
            fusion_dds=data.get("fusion_dds"),
            temporal_risk=data.get("temporal_risk"),
            temporal_available=data.get("temporal_available"),
            future_escalation_flag=data.get("future_escalation_flag"),
            priority_level=data.get("priority_level"),
            timestamp=data.get("timestamp", _current_iso_timestamp()),
        )

from chatbot.summary.summary_schema import ConversationSummary


# ===========================================================================
# MEDHA STATE
# ===========================================================================

class MedhaState:
    """
    Authoritative state representation for MEDHA Chatbot sessions.

    Maintains:
    - Victim and session identity
    - Longitudinal timepoint
    - Conversation history
    - Question history & cooldown tracking
    - Modality feature values (None if missing)
    - Modality availability flags
    - Candidate qualitative observations (isolated from ML numbers)
    - Contextual events
    - Prior V2 predictions
    """

    def __init__(
        self,
        victim_id: str,
        session_id: Optional[str] = None,
        timepoint: int = 1,
        created_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if not isinstance(victim_id, str) or not victim_id.strip():
            raise ValueError("victim_id must be a non-empty string.")

        if not isinstance(timepoint, int) or timepoint < 1:
            raise ValueError(f"timepoint must be a positive integer >= 1, got {timepoint}.")

        self.victim_id: str = victim_id.strip()
        self.session_id: str = session_id.strip() if session_id and session_id.strip() else f"sess_{uuid.uuid4().hex[:12]}"
        self.timepoint: int = timepoint
        self.created_at: str = created_at or _current_iso_timestamp()
        self.updated_at: str = self.created_at

        # Conversation state
        self.conversation_history: List[ChatMessage] = []
        self.current_user_message: Optional[str] = None
        self.latest_assistant_response: Optional[str] = None

        # Question Engine state
        self.question_history: List[QuestionRecord] = []
        
        # Step 9: Summary
        self.conversation_summary: ConversationSummary = ConversationSummary()
        
        # Safety Trigger: Track emitted safety events
        self.safety_events: List[Dict[str, Any]] = []

        # Modality Features — strictly initialized to None (missing remains missing!)
        self.structured_features: Dict[str, Optional[Union[float, int, str]]] = {
            feat: None for feat in STRUCTURED_FEATURES
        }
        self.text_features: Dict[str, Optional[float]] = {
            feat: None for feat in TEXT_FEATURES
        }
        self.voice_features: Dict[str, Optional[float]] = {
            feat: None for feat in VOICE_FEATURES
        }
        self.behaviour_features: Dict[str, Optional[float]] = {
            feat: None for feat in BEHAVIOUR_FEATURES
        }

        # Modality Availability Flags
        # Text and Voice are optional; None indicates unassessed/not yet evaluated.
        self.text_available: Optional[float] = None
        self.voice_available: Optional[float] = None
        # Structured and Behaviour are conceptually always available in V2
        self.struct_available: float = 1.0
        self.behav_available: float = 1.0

        # Context & observations
        self.candidate_observations: List[CandidateObservation] = []
        self.recent_events: List[ContextEvent] = []
        self.previous_predictions: List[PreviousPrediction] = []

        # Arbitrary session metadata
        self.metadata: Dict[str, Any] = copy.deepcopy(metadata or {})

    # -----------------------------------------------------------------------
    # State Update Helper
    # -----------------------------------------------------------------------
    def _touch(self) -> None:
        """Updates internal modification timestamp."""
        self.updated_at = _current_iso_timestamp()

    def add_safety_event(self, event_dict: Dict[str, Any]) -> None:
        """Records an emitted safety event for idempotency and tracing."""
        self.safety_events.append(event_dict)
        self._touch()

    # -----------------------------------------------------------------------
    # Conversation History Management
    # -----------------------------------------------------------------------
    def add_user_message(
        self,
        content: str,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """Records a user message in the conversation history."""
        if not isinstance(content, str):
            raise TypeError(f"Message content must be str, got {type(content).__name__}")

        msg = ChatMessage(
            role="user",
            content=content,
            timestamp=timestamp or _current_iso_timestamp(),
            metadata=copy.deepcopy(metadata or {}),
        )
        self.conversation_history.append(msg)
        self.current_user_message = content
        self._touch()
        return msg

    def add_assistant_response(
        self,
        content: str,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """Records an assistant reply in the conversation history."""
        if not isinstance(content, str):
            raise TypeError(f"Message content must be str, got {type(content).__name__}")

        msg = ChatMessage(
            role="assistant",
            content=content,
            timestamp=timestamp or _current_iso_timestamp(),
            metadata=copy.deepcopy(metadata or {}),
        )
        self.conversation_history.append(msg)
        self.latest_assistant_response = content
        self._touch()
        return msg

    def add_system_message(
        self,
        content: str,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ChatMessage:
        """Records a system message/event in the conversation history."""
        if not isinstance(content, str):
            raise TypeError(f"Message content must be str, got {type(content).__name__}")

        msg = ChatMessage(
            role="system",
            content=content,
            timestamp=timestamp or _current_iso_timestamp(),
            metadata=copy.deepcopy(metadata or {}),
        )
        self.conversation_history.append(msg)
        self._touch()
        return msg

    def get_history(self, limit: Optional[int] = None) -> List[ChatMessage]:
        """Returns full or truncated conversation history."""
        if limit is not None:
            return self.conversation_history[-limit:]
        return list(self.conversation_history)

    # -----------------------------------------------------------------------
    # Question History Management
    # -----------------------------------------------------------------------
    def record_question_asked(
        self,
        question_id: str,
        question_text: str,
        intent: str,
        cooldown_until: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> QuestionRecord:
        """Records that a controlled question was presented to the user."""
        if not question_id or not question_text:
            raise ValueError("question_id and question_text must be non-empty strings.")

        record = QuestionRecord(
            question_id=question_id,
            question_text=question_text,
            intent=intent,
            asked_at=_current_iso_timestamp(),
            answered=False,
            cooldown_until=cooldown_until,
            metadata=copy.deepcopy(metadata or {}),
        )
        self.question_history.append(record)
        self._touch()
        return record

    def record_question_answered(
        self,
        question_id: str,
        response_text: str,
    ) -> bool:
        """Finds the most recent question matching question_id and marks it answered."""
        for record in reversed(self.question_history):
            if record.question_id == question_id and not record.answered:
                record.answered = True
                record.response_text = response_text
                self._touch()
                return True
        return False

    def get_last_question(self) -> Optional[QuestionRecord]:
        """Returns the most recent question asked, if any."""
        return self.question_history[-1] if self.question_history else None

    def get_unanswered_questions(self) -> List[QuestionRecord]:
        """Returns all questions recorded that have not yet been marked answered."""
        return [q for q in self.question_history if not q.answered]

    def is_question_in_cooldown(
        self,
        question_id: str,
        current_time_iso: Optional[str] = None,
    ) -> bool:
        """Checks whether a given question is currently in cooldown."""
        check_time = current_time_iso or _current_iso_timestamp()
        for record in reversed(self.question_history):
            if record.question_id == question_id:
                if record.cooldown_until and record.cooldown_until > check_time:
                    return True
        return False

    # -----------------------------------------------------------------------
    # Safe Feature Updates (Strict Schema Validation)
    # -----------------------------------------------------------------------
    def update_feature(
        self,
        modality: str,
        feature_name: str,
        value: Any,
    ) -> None:
        """
        Safely updates a single feature in the given modality.

        Raises KeyError if modality or feature_name is invalid.
        Raises TypeError if value violates expected numeric/categorical type.
        Missing values (None or math.nan) are preserved as missing.
        """
        modality_clean = modality.lower().strip()
        if modality_clean not in VALID_MODALITIES:
            raise KeyError(
                f"Invalid modality '{modality}'. Must be one of {VALID_MODALITIES}."
            )

        # 1. Structured
        if modality_clean == "structured":
            if feature_name not in STRUCTURED_FEATURES:
                raise KeyError(
                    f"Unknown structured feature '{feature_name}'. "
                    f"Must be one of the 42 approved V2 structured features."
                )

            # Categorical validation
            if feature_name in STRUCTURED_CATEGORICAL_FEATURES:
                if value is not None and not (isinstance(value, float) and math.isnan(value)):
                    if not isinstance(value, str):
                        raise TypeError(
                            f"Categorical feature '{feature_name}' requires str, None, or NaN. "
                            f"Got {type(value).__name__} ({value!r})."
                        )
                self.structured_features[feature_name] = value

            # Numeric validation
            else:
                self._validate_numeric(feature_name, value)
                self.structured_features[feature_name] = value

        # 2. Text
        elif modality_clean == "text":
            if feature_name not in TEXT_FEATURES:
                raise KeyError(
                    f"Unknown text feature '{feature_name}'. Must be one of {TEXT_FEATURES}."
                )
            self._validate_numeric(feature_name, value)
            self.text_features[feature_name] = value

        # 3. Voice
        elif modality_clean == "voice":
            if feature_name not in VOICE_FEATURES:
                raise KeyError(
                    f"Unknown voice feature '{feature_name}'. Must be one of {VOICE_FEATURES}."
                )
            self._validate_numeric(feature_name, value)
            self.voice_features[feature_name] = value

        # 4. Behaviour
        elif modality_clean == "behaviour":
            if feature_name not in BEHAVIOUR_FEATURES:
                raise KeyError(
                    f"Unknown behaviour feature '{feature_name}'. Must be one of {BEHAVIOUR_FEATURES}."
                )
            self._validate_numeric(feature_name, value)
            self.behaviour_features[feature_name] = value

        self._touch()

    def update_features_batch(
        self,
        modality: str,
        features_dict: Dict[str, Any],
    ) -> None:
        """Updates multiple features in a modality with atomic verification."""
        for feat_name, feat_val in features_dict.items():
            self.update_feature(modality, feat_name, feat_val)

    def set_modality_availability(
        self,
        modality: str,
        available: Optional[Union[float, int, bool]],
    ) -> None:
        """
        Sets explicit availability flag for optional modalities.
        Value must be 1.0, 0.0, or None.
        """
        mod = modality.lower().strip()
        if mod not in ("text", "voice", "struct", "structured", "behav", "behaviour"):
            raise KeyError(f"Invalid modality '{modality}'.")

        val_float: Optional[float] = None
        if available is not None:
            if isinstance(available, bool):
                val_float = 1.0 if available else 0.0
            elif isinstance(available, (int, float)):
                if available not in (0, 1, 0.0, 1.0):
                    raise ValueError(f"Availability flag must be 1.0, 0.0, or None, got {available}.")
                val_float = float(available)
            else:
                raise TypeError(f"Invalid availability type {type(available).__name__}.")

        if mod == "text":
            self.text_available = val_float
        elif mod == "voice":
            self.voice_available = val_float
        elif mod in ("struct", "structured"):
            self.struct_available = 1.0 if val_float is None else val_float
        elif mod in ("behav", "behaviour"):
            self.behav_available = 1.0 if val_float is None else val_float

        self._touch()

    @staticmethod
    def _validate_numeric(feat_name: str, val: Any) -> None:
        """Validates that val is a number (int, float), None, or NaN."""
        if val is None:
            return
        # Reject booleans first (since in Python isinstance(True, int) is True)
        if isinstance(val, bool):
            raise TypeError(
                f"Numeric feature '{feat_name}' cannot be a boolean ({val}). "
                f"Must be float, int, None, or NaN."
            )
        if isinstance(val, (int, float)):
            return
        raise TypeError(
            f"Numeric feature '{feat_name}' requires float, int, None, or NaN. "
            f"Got {type(val).__name__} ({val!r})."
        )

    # -----------------------------------------------------------------------
    # Candidate Observations & Context Management
    # -----------------------------------------------------------------------
    def add_candidate_observation(
        self,
        domain: str,
        semantic_value: Any,
        evidence: Optional[str] = None,
        status: str = "candidate",
    ) -> CandidateObservation:
        """
        Stores an extracted qualitative observation.
        This remains distinct from authoritative numeric V2 features.
        """
        obs = CandidateObservation(
            domain=domain,
            semantic_value=semantic_value,
            evidence=evidence,
            timestamp=_current_iso_timestamp(),
            status=status,
        )
        self.candidate_observations.append(obs)
        self._touch()
        return obs

    def add_event(
        self,
        event_type: str,
        description: str,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextEvent:
        """Records a contextual life/legal event."""
        event = ContextEvent(
            event_type=event_type,
            description=description,
            timestamp=timestamp or _current_iso_timestamp(),
            metadata=copy.deepcopy(metadata or {}),
        )
        self.recent_events.append(event)
        self._touch()
        return event

    def record_prediction(
        self,
        prediction: Union[PreviousPrediction, Dict[str, Any]],
    ) -> PreviousPrediction:
        """Stores a prior V2 prediction result."""
        if isinstance(prediction, dict):
            pred_obj = PreviousPrediction.from_dict(prediction)
        elif isinstance(prediction, PreviousPrediction):
            pred_obj = prediction
        else:
            raise TypeError(f"Expected PreviousPrediction or dict, got {type(prediction).__name__}")

        self.previous_predictions.append(pred_obj)
        self._touch()
        return pred_obj

    # -----------------------------------------------------------------------
    # Inspection Helpers
    # -----------------------------------------------------------------------
    def get_missing_structured_features(self) -> List[str]:
        """Returns all 42 structured feature names that currently have None or NaN values."""
        missing = []
        for feat, val in self.structured_features.items():
            if val is None or (isinstance(val, float) and math.isnan(val)):
                missing.append(feat)
        return missing

    def get_populated_structured_features(self) -> Dict[str, Any]:
        """Returns structured features that currently hold non-missing values."""
        populated = {}
        for feat, val in self.structured_features.items():
            if val is not None and not (isinstance(val, float) and math.isnan(val)):
                populated[feat] = val
        return populated

    def is_modality_available(self, modality: str) -> bool:
        """Returns True if the given modality flag is explicitly 1.0."""
        mod = modality.lower().strip()
        if mod == "text":
            return self.text_available == 1.0
        if mod == "voice":
            return self.voice_available == 1.0
        if mod in ("struct", "structured"):
            return self.struct_available == 1.0
        if mod in ("behav", "behaviour"):
            return self.behav_available == 1.0
        return False

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------
    def validate(self) -> List[str]:
        """
        Validates internal state against V2 rules.
        Returns a list of error strings; empty list indicates fully valid state.
        """
        errors: List[str] = []

        if not self.victim_id or not self.victim_id.strip():
            errors.append("victim_id is empty or missing.")

        if self.timepoint < 1:
            errors.append(f"timepoint must be >= 1, got {self.timepoint}.")

        # Check structured features completeness of keys
        if set(self.structured_features.keys()) != set(STRUCTURED_FEATURES):
            extra = set(self.structured_features.keys()) - set(STRUCTURED_FEATURES)
            missing = set(STRUCTURED_FEATURES) - set(self.structured_features.keys())
            if extra:
                errors.append(f"Unauthorized structured features: {extra}")
            if missing:
                errors.append(f"Missing structured feature keys: {missing}")

        # Check text feature keys
        if set(self.text_features.keys()) != set(TEXT_FEATURES):
            extra = set(self.text_features.keys()) - set(TEXT_FEATURES)
            missing = set(TEXT_FEATURES) - set(self.text_features.keys())
            if extra:
                errors.append(f"Unauthorized text features: {extra}")
            if missing:
                errors.append(f"Missing text feature keys: {missing}")

        # Check voice feature keys
        if set(self.voice_features.keys()) != set(VOICE_FEATURES):
            extra = set(self.voice_features.keys()) - set(VOICE_FEATURES)
            missing = set(VOICE_FEATURES) - set(self.voice_features.keys())
            if extra:
                errors.append(f"Unauthorized voice features: {extra}")
            if missing:
                errors.append(f"Missing voice feature keys: {missing}")

        # Check behaviour feature keys
        if set(self.behaviour_features.keys()) != set(BEHAVIOUR_FEATURES):
            extra = set(self.behaviour_features.keys()) - set(BEHAVIOUR_FEATURES)
            missing = set(BEHAVIOUR_FEATURES) - set(self.behaviour_features.keys())
            if extra:
                errors.append(f"Unauthorized behaviour features: {extra}")
            if missing:
                errors.append(f"Missing behaviour feature keys: {missing}")

        # Check availability flags
        for name, flag in [
            ("text_available", self.text_available),
            ("voice_available", self.voice_available),
            ("struct_available", self.struct_available),
            ("behav_available", self.behav_available),
        ]:
            if flag is not None and flag not in (0.0, 1.0):
                errors.append(f"{name} must be 0.0, 1.0, or None, got {flag}.")

        return errors

    # -----------------------------------------------------------------------
    # Serialization & Deserialization
    # -----------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes entire MedhaState into a pure Python dictionary.
        Safe for JSON encoding. Preserves NaNs as None.
        """
        def _clean_val(v: Any) -> Any:
            if isinstance(v, float) and math.isnan(v):
                return None
            return v

        return {
            "victim_id": self.victim_id,
            "session_id": self.session_id,
            "timepoint": self.timepoint,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "conversation_history": [msg.to_dict() for msg in self.conversation_history],
            "current_user_message": self.current_user_message,
            "latest_assistant_response": self.latest_assistant_response,
            "question_history": [q.to_dict() for q in self.question_history],
            "conversation_summary": self.conversation_summary.to_dict(),
            "structured_features": {k: _clean_val(v) for k, v in self.structured_features.items()},
            "text_features": {k: _clean_val(v) for k, v in self.text_features.items()},
            "voice_features": {k: _clean_val(v) for k, v in self.voice_features.items()},
            "behaviour_features": {k: _clean_val(v) for k, v in self.behaviour_features.items()},
            "text_available": self.text_available,
            "voice_available": self.voice_available,
            "struct_available": self.struct_available,
            "behav_available": self.behav_available,
            "candidate_observations": [obs.to_dict() for obs in self.candidate_observations],
            "recent_events": [evt.to_dict() for evt in self.recent_events],
            "previous_predictions": [pred.to_dict() for pred in self.previous_predictions],
            "metadata": copy.deepcopy(self.metadata),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serializes state to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MedhaState:
        """Reconstitutes a MedhaState instance from a dictionary."""
        state = cls(
            victim_id=data["victim_id"],
            session_id=data.get("session_id"),
            timepoint=int(data.get("timepoint", 1)),
            created_at=data.get("created_at"),
            metadata=data.get("metadata", {}),
        )
        state.updated_at = data.get("updated_at", state.created_at)
        state.current_user_message = data.get("current_user_message")
        state.latest_assistant_response = data.get("latest_assistant_response")

        # History
        for msg_dict in data.get("conversation_history", []):
            state.conversation_history.append(ChatMessage.from_dict(msg_dict))

        # Questions
        for q_dict in data.get("question_history", []):
            state.question_history.append(QuestionRecord.from_dict(q_dict))

        if "conversation_summary" in data:
            state.conversation_summary = ConversationSummary.from_dict(data["conversation_summary"])

        # Features
        for k, v in data.get("structured_features", {}).items():
            if k in state.structured_features:
                state.structured_features[k] = v

        for k, v in data.get("text_features", {}).items():
            if k in state.text_features:
                state.text_features[k] = v

        for k, v in data.get("voice_features", {}).items():
            if k in state.voice_features:
                state.voice_features[k] = v

        for k, v in data.get("behaviour_features", {}).items():
            if k in state.behaviour_features:
                state.behaviour_features[k] = v

        # Availability
        state.text_available = data.get("text_available")
        state.voice_available = data.get("voice_available")
        state.struct_available = float(data.get("struct_available", 1.0))
        state.behav_available = float(data.get("behav_available", 1.0))

        # Candidate observations
        for obs_dict in data.get("candidate_observations", []):
            state.candidate_observations.append(CandidateObservation.from_dict(obs_dict))

        # Events
        for evt_dict in data.get("recent_events", []):
            state.recent_events.append(ContextEvent.from_dict(evt_dict))

        # Predictions
        for pred_dict in data.get("previous_predictions", []):
            state.previous_predictions.append(PreviousPrediction.from_dict(pred_dict))

        return state

    @classmethod
    def from_json(cls, json_str: str) -> MedhaState:
        """Reconstitutes a MedhaState instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))
