"""
Conversation Summary Schema
===========================

Structured representation for tracking important ongoing contextual information.
Provides compact memory for the LLM without modifying predictive features.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import copy


def _current_iso_timestamp() -> str:
    """Returns current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SummaryItem:
    """
    Represents a single atomic piece of contextual memory.
    """
    content: str
    turn_index: int
    source: str = "user_statement"
    extracted_by: str = "llm_extraction"
    status: str = "active"  # "active", "superseded", "unresolved", "contradicted"
    timestamp: str = field(default_factory=_current_iso_timestamp)
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SummaryItem":
        return cls(
            content=data["content"],
            turn_index=data["turn_index"],
            source=data.get("source", "user_statement"),
            extracted_by=data.get("extracted_by", "llm_extraction"),
            status=data.get("status", "active"),
            timestamp=data.get("timestamp", _current_iso_timestamp()),
            confidence=data.get("confidence"),
            evidence=data.get("evidence"),
            metadata=copy.deepcopy(data.get("metadata", {})),
        )


@dataclass
class ConversationSummary:
    """
    Compact memory structure isolating contextual facts from V2 predictive risk.
    """
    important_facts: List[SummaryItem] = field(default_factory=list)
    current_concerns: List[SummaryItem] = field(default_factory=list)
    recent_events: List[SummaryItem] = field(default_factory=list)
    support_context: List[SummaryItem] = field(default_factory=list)
    preferences: List[SummaryItem] = field(default_factory=list)
    ongoing_topics: List[SummaryItem] = field(default_factory=list)
    unresolved_topics: List[SummaryItem] = field(default_factory=list)
    important_observations: List[SummaryItem] = field(default_factory=list)
    
    updated_at: str = field(default_factory=_current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "important_facts": [item.to_dict() for item in self.important_facts],
            "current_concerns": [item.to_dict() for item in self.current_concerns],
            "recent_events": [item.to_dict() for item in self.recent_events],
            "support_context": [item.to_dict() for item in self.support_context],
            "preferences": [item.to_dict() for item in self.preferences],
            "ongoing_topics": [item.to_dict() for item in self.ongoing_topics],
            "unresolved_topics": [item.to_dict() for item in self.unresolved_topics],
            "important_observations": [item.to_dict() for item in self.important_observations],
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSummary":
        return cls(
            important_facts=[SummaryItem.from_dict(item) for item in data.get("important_facts", [])],
            current_concerns=[SummaryItem.from_dict(item) for item in data.get("current_concerns", [])],
            recent_events=[SummaryItem.from_dict(item) for item in data.get("recent_events", [])],
            support_context=[SummaryItem.from_dict(item) for item in data.get("support_context", [])],
            preferences=[SummaryItem.from_dict(item) for item in data.get("preferences", [])],
            ongoing_topics=[SummaryItem.from_dict(item) for item in data.get("ongoing_topics", [])],
            unresolved_topics=[SummaryItem.from_dict(item) for item in data.get("unresolved_topics", [])],
            important_observations=[SummaryItem.from_dict(item) for item in data.get("important_observations", [])],
            updated_at=data.get("updated_at", _current_iso_timestamp()),
        )
