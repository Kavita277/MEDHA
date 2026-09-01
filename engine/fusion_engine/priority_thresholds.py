"""
MEDHA Priority Thresholds (PROTOTYPE)
=====================================

WARNING: These are prototype rules for deriving an operational 
priority level from the model outputs (DDS and Future Escalation Risk).
They are NOT clinically validated and should be tuned in coordination
with mental health professionals.

Priority is derived AFTER the models have made their predictions. 
It is an operational layer, NOT a model feature.
"""

def determine_priority(dds: float, future_escalation_risk: float) -> str:
    """
    Determine the clinical priority level based on current distress (DDS)
    and the 7-day future escalation risk.
    
    Priority Levels:
    - CRITICAL: High current distress OR very high risk of future escalation.
    - HIGH: Elevated distress or elevated future risk.
    - MEDIUM: Moderate distress.
    - LOW: Minimal distress and low future risk.
    """
    if dds is None or future_escalation_risk is None:
        return "UNKNOWN"
        
    # Prototype Thresholds
    if dds >= 75.0 or future_escalation_risk >= 0.85:
        return "CRITICAL"
    elif dds >= 50.0 or future_escalation_risk >= 0.50:
        return "HIGH"
    elif dds >= 25.0 or future_escalation_risk >= 0.25:
        return "MEDIUM"
    else:
        return "LOW"
