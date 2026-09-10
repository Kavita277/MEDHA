"""
Behaviour Schemas
=================
Pydantic schemas for the 10 authoritative behaviour features.
"""

from typing import Optional
from pydantic import BaseModel

class BehaviourFeatureSnapshot(BaseModel):
    app_interaction_duration: Optional[float] = None
    app_interaction_duration_deviation: Optional[float] = None
    checkin_response_delay: Optional[float] = None
    checkin_response_delay_deviation: Optional[float] = None
    checkin_completion_rate: Optional[float] = None
    missed_checkin_count: Optional[float] = None
    journal_entry_count: Optional[float] = None
    chat_message_count: Optional[float] = None
    late_night_usage_ratio: Optional[float] = None
    support_resource_access_count: Optional[float] = None
