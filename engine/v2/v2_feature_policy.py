"""
MEDHA V2 Central Feature Policy
Single Source of Truth for DDS Feature Eligibility & Specialist Boundaries
"""

import json
import os

# Explicitly excluded because they leak current/future DDS
V2_DDS_EXCLUDED_FEATURES = [
    "Previous_DDS",                 # Contains previous DDS (historical)
    "Rolling_DDS_Mean",             # Derived from historical DDS
    "Rolling_DDS_SD",               # Derived from historical DDS
    "DDS_Slope",                    # Derived from historical DDS
    "Recent_Change_Rate",           # Derived from historical DDS
    "Recent_Max_DDS",               # Derived from historical DDS
    "Recent_Min_DDS",               # Derived from historical DDS
    "Delta_DDS",                    # Derived from historical DDS
    "DDS_Deviation_From_Baseline",  # Derived from current DDS
    "Baseline_DDS"                  # Excluded per Step 4: constant per victim but derived from target generation
]

# Identifiers and metadata (not predictive features)
V2_DDS_ID_METADATA_FEATURES = [
    "Victim_ID",
    "Case_ID",
    "Timepoint",
    "Date_Time"
]

# Targets (what we are predicting)
V2_DDS_TARGET_FEATURES = [
    "DDS",                          # The current-timepoint target
    "Future_Escalation_Label"       # Future-timepoint label for GRU
]

# Post-hoc outcomes
V2_DDS_POST_HOC_FEATURES = [
    "Intervention",
    "Follow_Up"
]

# Features requiring further investigation before they can be used
V2_DDS_QUARANTINED_FEATURES = [
    "Trajectory_State",             # May encode future trajectory/target information
    "Discordance_Test_Feature",     # Generation logic unclear, could be leaky
    "Discordance_Example_Flag",     # Generation logic unclear
    "Diary_Distress_Feature",       # Extremely sparse (81% missing), test separately
    "Diary_Length"                  # Related to diary, extremely sparse
]

# Explicit whitelist of approved current-timepoint features (Global Universe: 60 features)
V2_DDS_APPROVED_FEATURES = [
    # Structured / Case / Context (10)
    "Case_Type",
    "Case_Stage",
    "Checkin_Available",
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",
    
    # Context / Protection Events / Clinical Episodes (17)
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
    "Episode_Severity",
    "Family_Reported_Episode",
    
    # Behaviour / Engagement (7)
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Hours",
    "Response_Delay_Deviation",
    
    # Text (6 direct + 3 trend/baseline = 9)
    "Text_Available",
    "Text_Distress",
    "Fear",
    "Threat_Context",
    "Negative_Affect",
    "Urgency",
    
    # Voice (6 direct + 3 trend/baseline = 9)
    "Voice_Available",
    "Voice_Distress",
    "Pause_Ratio",
    "Speech_Rate_Deviation",
    "Energy_Deviation",
    "Acoustic_Indicator",

    # Other Baseline/Trend/Observation features (8)
    "Baseline_Response_Delay",
    "Baseline_Engagement",
    "Baseline_Text_Distress",
    "Baseline_Voice_Distress",
    "Baseline_Checkin_Distress",
    "Text_Distress_Deviation",
    "Voice_Distress_Deviation",
    "Behaviour_Trend",
    "Engagement_Trend",
    "Text_Distress_Trend",
    "Voice_Distress_Trend",
    
    # Other Availability flags and features (3)
    "Diary_Available",
    "Therapist_Observation_Available",
    "Therapist_Observation_Score"
]

# ===========================================================================
# MODALITY-SPECIFIC SUBSETS & SPECIALIST BOUNDARIES
# ===========================================================================

# Text-derived features (9 features)
V2_TEXT_DDS_FEATURES = [
    "Text_Available",
    "Text_Distress",
    "Fear",
    "Threat_Context",
    "Negative_Affect",
    "Urgency",
    "Baseline_Text_Distress",
    "Text_Distress_Deviation",
    "Text_Distress_Trend",
]

# Voice-derived features (9 features)
V2_VOICE_DDS_FEATURES = [
    "Voice_Available",
    "Voice_Distress",
    "Pause_Ratio",
    "Speech_Rate_Deviation",
    "Energy_Deviation",
    "Acoustic_Indicator",
    "Baseline_Voice_Distress",
    "Voice_Distress_Deviation",
    "Voice_Distress_Trend",
]

# Clean Structured Specialist features (42 features)
# Excludes all Text-derived and Voice-derived features
V2_STRUCTURED_DDS_FEATURES = [
    # Structured / Case / Context (10)
    "Case_Type",
    "Case_Stage",
    "Checkin_Available",
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",
    
    # Context / Protection Events / Clinical Episodes (17)
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
    "Episode_Severity",
    "Family_Reported_Episode",
    
    # Behaviour / Engagement (7)
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Hours",
    "Response_Delay_Deviation",
    
    # Structured Baseline / Trend / Observations (8)
    "Baseline_Response_Delay",
    "Baseline_Engagement",
    "Baseline_Checkin_Distress",
    "Behaviour_Trend",
    "Engagement_Trend",
    "Diary_Available",
    "Therapist_Observation_Available",
    "Therapist_Observation_Score",
]

def validate_dds_features(features):
    """
    Validates an explicit list of features requested by a model script.
    Hard-fails (raises ValueError) if ANY feature is not in the global approved whitelist (60 features).
    This prevents accidental leakage if a script says features=["Mood", "Previous_DDS"].
    """
    if not isinstance(features, (list, set, tuple)):
        features = list(features)
        
    seen = set()
    for f in features:
        if f in seen:
            raise ValueError(f"Duplicate feature requested: '{f}'")
        seen.add(f)
        
        if f in V2_DDS_EXCLUDED_FEATURES:
            raise ValueError(f"Feature '{f}' is explicitly EXCLUDED (leaky).")
        if f in V2_DDS_TARGET_FEATURES:
            raise ValueError(f"Feature '{f}' is a TARGET feature.")
        if f in V2_DDS_ID_METADATA_FEATURES:
            raise ValueError(f"Feature '{f}' is an ID/METADATA feature.")
        if f in V2_DDS_POST_HOC_FEATURES:
            raise ValueError(f"Feature '{f}' is a POST-HOC feature.")
        if f in V2_DDS_QUARANTINED_FEATURES:
            raise ValueError(f"Feature '{f}' is QUARANTINED (requires verification).")
            
        if f not in V2_DDS_APPROVED_FEATURES:
            raise ValueError(f"Feature '{f}' is UNKNOWN or NOT APPROVED for V2 DDS models.")
            
    return True

def validate_structured_specialist_features(features):
    """
    Strict validation for the Structured DDS Specialist.
    Enforces that:
    1. Global leakage policy passes (no excluded/target/metadata/quarantined/unknown).
    2. No Text-derived features are present.
    3. No Voice-derived features are present.
    4. All features belong to V2_STRUCTURED_DDS_FEATURES.
    """
    validate_dds_features(features)
    
    for f in features:
        if f in V2_TEXT_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is TEXT-derived and cannot be used by the Structured specialist.")
        if f in V2_VOICE_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is VOICE-derived and cannot be used by the Structured specialist.")
        if f not in V2_STRUCTURED_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' does not belong to the approved Structured specialist subset.")
            
    return True

# Core 5 direct outputs from MuRIL classifier
V2_CORE_TEXT_DDS_FEATURES = [
    "Text_Distress",
    "Fear",
    "Threat_Context",
    "Negative_Affect",
    "Urgency",
]

def validate_text_specialist_features(features, allow_extended=True):
    """
    Strict validation for the Text DDS Specialist.
    Enforces that:
    1. Global leakage policy passes (no excluded/target/metadata/quarantined/unknown).
    2. No Voice-derived features are present.
    3. No Structured-derived features are present.
    4. All features belong to V2_TEXT_DDS_FEATURES (or V2_CORE_TEXT_DDS_FEATURES if allow_extended=False).
    """
    validate_dds_features(features)
    
    for f in features:
        if f in V2_VOICE_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is VOICE-derived and cannot be used by the Text specialist.")
        if f in V2_STRUCTURED_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is STRUCTURED-derived and cannot be used by the Text specialist.")
        if not allow_extended and f not in V2_CORE_TEXT_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is not in core Text specialist features.")
        if f not in V2_TEXT_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' does not belong to the approved Text specialist subset.")
            
    return True

# Core 5 direct outputs from Voice Engine
V2_CORE_VOICE_DDS_FEATURES = [
    "Voice_Distress",
    "Pause_Ratio",
    "Speech_Rate_Deviation",
    "Energy_Deviation",
    "Acoustic_Indicator",
]

def validate_voice_specialist_features(features, allow_extended=True):
    """
    Strict validation for the Voice DDS Specialist.
    Enforces that:
    1. Global leakage policy passes (no excluded/target/metadata/quarantined/unknown).
    2. No Text-derived features are present.
    3. No Structured-derived features are present.
    4. All features belong to V2_VOICE_DDS_FEATURES (or V2_CORE_VOICE_DDS_FEATURES if allow_extended=False).
    """
    validate_dds_features(features)
    
    for f in features:
        if f in V2_TEXT_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is TEXT-derived and cannot be used by the Voice specialist.")
        if f in V2_STRUCTURED_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is STRUCTURED-derived and cannot be used by the Voice specialist.")
        if not allow_extended and f not in V2_CORE_VOICE_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is not in core Voice specialist features.")
        if f not in V2_VOICE_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' does not belong to the approved Voice specialist subset.")
            
    return True

def get_all_approved_voice_dds_features(core_only=False):
    """
    Helper for introspection. Returns a copy of the approved Voice specialist whitelist.
    If core_only is True, returns only the 5 core Voice features.
    """
    if core_only:
        return list(V2_CORE_VOICE_DDS_FEATURES)
    return list(V2_VOICE_DDS_FEATURES)

# ===========================================================================
# BEHAVIOUR SPECIALIST FEATURE POLICY & BOUNDARIES
# ===========================================================================

# Core 7 interaction features from Behaviour Engine / check-in app activity
V2_CORE_BEHAVIOUR_DDS_FEATURES = [
    "Engagement_Score",
    "Engagement_Deviation",
    "Response_Delay_Hours",
    "Response_Delay_Deviation",
    "Missed_Checkin",
    "Interaction_Frequency_7d",
    "Session_Duration_Minutes",
]

# Extended 10 features including personal baselines and trajectory trend
V2_EXTENDED_BEHAVIOUR_DDS_FEATURES = [
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
]

def validate_behaviour_specialist_features(features, allow_extended=True):
    """
    Strict validation for the Behaviour DDS Specialist.
    Enforces that:
    1. Global leakage policy passes (no excluded/target/metadata/quarantined/unknown).
    2. No Text-derived features are present.
    3. No Voice-derived features are present.
    4. No Structured clinical/context/event features are present.
    5. All features belong to V2_EXTENDED_BEHAVIOUR_DDS_FEATURES (or V2_CORE_BEHAVIOUR_DDS_FEATURES if allow_extended=False).
    """
    validate_dds_features(features)
    
    allowed_set = set(V2_EXTENDED_BEHAVIOUR_DDS_FEATURES if allow_extended else V2_CORE_BEHAVIOUR_DDS_FEATURES)
    
    for f in features:
        if f in V2_TEXT_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is TEXT-derived and cannot be used by the Behaviour specialist.")
        if f in V2_VOICE_DDS_FEATURES:
            raise ValueError(f"Feature '{f}' is VOICE-derived and cannot be used by the Behaviour specialist.")
        if f not in allowed_set:
            if f in V2_STRUCTURED_DDS_FEATURES:
                raise ValueError(f"Feature '{f}' is a Structured context/event feature, not a Behaviour interaction feature.")
            raise ValueError(f"Feature '{f}' does not belong to the approved Behaviour specialist subset.")
            
    return True

def get_all_approved_behaviour_dds_features(core_only=False):
    """
    Helper for introspection. Returns a copy of the approved Behaviour specialist whitelist.
    If core_only is True, returns only the 7 core interaction features.
    """
    if core_only:
        return list(V2_CORE_BEHAVIOUR_DDS_FEATURES)
    return list(V2_EXTENDED_BEHAVIOUR_DDS_FEATURES)

def get_allowed_dds_features(requested_features):
    """
    Validates a list of requested features against the global policy.
    If ANY feature is unapproved, excluded, a target, or unknown, it will hard-fail.
    This prevents silent feature dropping.
    """
    validate_dds_features(requested_features)
    return list(requested_features)

def get_all_approved_dds_features():
    """
    Helper for introspection. Returns a copy of the complete global 60-feature whitelist.
    """
    return list(V2_DDS_APPROVED_FEATURES)

def get_all_approved_structured_dds_features():
    """
    Helper for introspection. Returns a copy of the 42-feature Structured specialist whitelist.
    """
    return list(V2_STRUCTURED_DDS_FEATURES)

def get_all_approved_text_dds_features(core_only=False):
    """
    Helper for introspection. Returns a copy of the approved Text specialist whitelist.
    If core_only is True, returns only the 5 core MuRIL outputs.
    """
    if core_only:
        return list(V2_CORE_TEXT_DDS_FEATURES)
    return list(V2_TEXT_DDS_FEATURES)

def export_policy_to_json(filepath):
    """Exports the policy rules to a machine-readable JSON file."""
    policy = {
        "policy_version": "v2.0",
        "dataset_name": "MEDHA_Synthetic_1000x30_DDS_Regenerated.xlsx",
        "global_approved_feature_count": len(V2_DDS_APPROVED_FEATURES),
        "approved_features": V2_DDS_APPROVED_FEATURES,
        "structured_specialist_features": V2_STRUCTURED_DDS_FEATURES,
        "text_specialist_features": V2_TEXT_DDS_FEATURES,
        "voice_specialist_features": V2_VOICE_DDS_FEATURES,
        "behaviour_specialist_features": V2_EXTENDED_BEHAVIOUR_DDS_FEATURES,
        "behaviour_core_features": V2_CORE_BEHAVIOUR_DDS_FEATURES,
        "excluded_features": V2_DDS_EXCLUDED_FEATURES,
        "quarantined_features": V2_DDS_QUARANTINED_FEATURES,
        "target_features": V2_DDS_TARGET_FEATURES,
        "id_metadata_features": V2_DDS_ID_METADATA_FEATURES,
        "post_hoc_features": V2_DDS_POST_HOC_FEATURES,
        "leakage_rationale": {
            "excluded": "These features contain historical or current target (DDS) information and will cause data leakage if used to predict current DDS.",
            "quarantined": "These features have unclear generation origins or sparsity that require further manual verification before they can be safely used.",
            "post_hoc": "These events happen after the timepoint prediction."
        }
    }
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(policy, f, indent=4)

