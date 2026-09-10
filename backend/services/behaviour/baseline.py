"""
Baseline Calculation
====================
Calculates historical baseline and deviation using only strictly past observations.
"""

from typing import List, Optional
from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel

def calculate_deviation(
    current_value: Optional[float], 
    snapshots: List[BehaviourFeatureSnapshotModel], 
    feature_attr: str
) -> Optional[float]:
    """
    Calculates current deviation = current_value - baseline.
    The baseline is the mean of the feature_attr across all strictly past snapshots.
    Snapshots provided MUST ALREADY BE FILTERED to only include timepoints < current_timepoint.
    Returns None if current_value is None or if there is no valid historical data (Cold Start).
    """
    if current_value is None:
        return None
        
    valid_values = [
        getattr(s, feature_attr) 
        for s in snapshots 
        if getattr(s, feature_attr) is not None
    ]
    
    if not valid_values:
        return None
        
    baseline = sum(valid_values) / len(valid_values)
    return current_value - baseline

def calculate_all_deviations(
    current_duration: Optional[float], 
    current_delay: Optional[float], 
    past_snapshots: List[BehaviourFeatureSnapshotModel]
) -> tuple[Optional[float], Optional[float]]:
    """
    Convenience method for calculating deviations for the authoritative features that require it.
    Returns (duration_deviation, delay_deviation).
    """
    duration_dev = calculate_deviation(current_duration, past_snapshots, "app_interaction_duration")
    delay_dev = calculate_deviation(current_delay, past_snapshots, "checkin_response_delay")
    
    return duration_dev, delay_dev
