"""
Event Mapping Rules
===================
Defines how RawEventModel events translate into concrete behavioural metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.persistence.models.event import RawEventModel


def calculate_app_interaction_duration(events: List[RawEventModel]) -> Optional[float]:
    """
    Pairs session_start and session_end events chronologically to calculate duration in seconds.
    If a session_start has no corresponding end before the next start, it's considered incomplete and ignored.
    If no valid pairs exist, returns None.
    If valid pairs exist, returns total sum of durations (min 0.0).
    """
    total_duration = 0.0
    has_valid_pair = False
    
    current_start: Optional[datetime] = None
    
    for event in events:
        if event.event_type == "session_start":
            current_start = event.occurred_at
        elif event.event_type == "session_end":
            if current_start:
                duration = (event.occurred_at - current_start).total_seconds()
                if duration >= 0:
                    total_duration += duration
                    has_valid_pair = True
                current_start = None  # Reset for next pair
                
    return total_duration if has_valid_pair else None


def calculate_checkin_metrics(events: List[RawEventModel]) -> Dict[str, Optional[float]]:
    """
    Evaluates checkin_prompt_shown and checkin_submitted/checkin_completed events.
    """
    prompts_shown = 0
    completed_checkins = 0
    missed_checkins = 0
    total_delay_seconds = 0.0
    
    prompt_time: Optional[datetime] = None
    
    # Check-in lifecycle is typically: prompt_shown -> (started/answered) -> completed
    for event in events:
        if event.event_type == "checkin_prompt_shown":
            if prompt_time is not None:
                # Previous prompt was missed
                missed_checkins += 1
            prompts_shown += 1
            prompt_time = event.occurred_at
        
        elif event.event_type == "checkin_completed":
            if prompt_time is not None:
                completed_checkins += 1
                delay = (event.occurred_at - prompt_time).total_seconds()
                if delay >= 0:
                    total_delay_seconds += delay
                prompt_time = None
    
    completion_rate = (completed_checkins / prompts_shown) if prompts_shown > 0 else None
    avg_delay = (total_delay_seconds / completed_checkins) if completed_checkins > 0 else None
    final_missed = float(missed_checkins) if prompts_shown > 0 else None
    
    return {
        "Checkin_Response_Delay": avg_delay,
        "Checkin_Completion_Rate": completion_rate,
        "Missed_Checkin_Count": final_missed
    }


def calculate_simple_counts(events: List[RawEventModel]) -> Dict[str, Optional[float]]:
    """
    Calculates journal_entry_count, chat_message_count, support_resource_access_count.
    Returns None if there are absolutely no events in the window (missing data).
    Returns 0.0 if events exist but none of the specific type match.
    """
    if not events:
        return {
            "Journal_Entry_Count": None,
            "Chat_Message_Count": None,
            "Support_Resource_Access_Count": None
        }
        
    counts = {
        "Journal_Entry_Count": 0.0,
        "Chat_Message_Count": 0.0,
        "Support_Resource_Access_Count": 0.0
    }
    
    seen_journals = set()
    
    for event in events:
        if event.event_type == "journal_saved":
            j_id = event.metadata_payload.get("journal_id") if event.metadata_payload else None
            if j_id:
                if j_id not in seen_journals:
                    counts["Journal_Entry_Count"] += 1.0
                    seen_journals.add(j_id)
            else:
                counts["Journal_Entry_Count"] += 1.0
                
        elif event.event_type == "chat_message_sent":
            role = event.metadata_payload.get("role") if event.metadata_payload else "user"
            if role == "user":
                counts["Chat_Message_Count"] += 1.0
                
        elif event.event_type in ["support_opened", "support_resource_accessed"]:
            counts["Support_Resource_Access_Count"] += 1.0

    return counts


def calculate_late_night_ratio(events: List[RawEventModel]) -> Optional[float]:
    """
    Calculates Late_Night_Usage_Ratio.
    Uses configurable time window and timezone (default 00:00 to 06:00 UTC).
    Ratio = (events in late night) / (total valid interaction events)
    """
    from backend.config import get_settings
    import zoneinfo
    
    settings = get_settings()
    
    interaction_types = {
        "chat_message_sent", "journal_saved", "checkin_completed", 
        "screen_view", "support_opened", "session_start"
    }
    
    valid_events = [e for e in events if e.event_type in interaction_types]
    if not valid_events:
        return None
        
    late_night_count = 0
    tz = zoneinfo.ZoneInfo(settings.BEHAVIOUR_LATE_NIGHT_TIMEZONE)
    start_hr = settings.BEHAVIOUR_LATE_NIGHT_START_HOUR
    end_hr = settings.BEHAVIOUR_LATE_NIGHT_END_HOUR
    
    for e in valid_events:
        # Note: e.occurred_at is expected to be a timezone-aware datetime (UTC from DB)
        local_time = e.occurred_at.astimezone(tz)
        if start_hr <= local_time.hour < end_hr:
            late_night_count += 1
            
    return float(late_night_count) / len(valid_events)
