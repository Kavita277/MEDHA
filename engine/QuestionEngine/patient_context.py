import pandas as pd


DATASET_FILE = "MEDHA_Synthetic_1000x30.xlsx"


QUESTION_ENGINE_STATE_FIELDS = [
    "Mood",
    "Stress",
    "Sleep",
    "Functioning",
    "Safety",
    "Social_Support_Checkin",
    "Self_Reported_Wellbeing",
]


EVENT_FIELDS = [
    "Threat_Event",
    "Upcoming_Hearing",
    "Hearing_Completed",
    "Investigation_Delay",
    "Compensation_Delay",
    "Relocation_Stress",
    "Rehabilitation_Issue",
    "Protection_Event",
]


THERAPIST_FIELDS = [
    "Therapist_Observation_Available",
    "Recent_Episode",
    "Episode_Severity",
    "Family_Reported_Episode",
    "Intervention",
    "Follow_Up",
]


def load_patient_context(
    victim_id,
    timepoint=None,
    dataset_file=DATASET_FILE
):
    """
    Load the latest available context for one victim.

    This function only provides context to the Question Engine.
    It does not calculate risk, behaviour, DDS, or text features.
    """

    longitudinal = pd.read_excel(
        dataset_file,
        sheet_name="Longitudinal_Data"
    )

    profiles = pd.read_excel(
        dataset_file,
        sheet_name="Victim_Profiles"
    )

    therapist = pd.read_excel(
        dataset_file,
        sheet_name="Therapist_Events"
    )

    # Find this patient's longitudinal history
    patient_rows = longitudinal[
        longitudinal["Victim_ID"] == victim_id
    ].copy()

    if patient_rows.empty:
        raise ValueError(
            f"Victim_ID '{victim_id}' was not found in the dataset."
        )

    # Make sure chronological ordering is correct
    patient_rows["Date_Time"] = pd.to_datetime(
        patient_rows["Date_Time"]
    )

    patient_rows = patient_rows.sort_values("Date_Time")

    # Latest longitudinal observation
    # Select requested timepoint, otherwise use latest.
    if timepoint is not None:
        matching_rows = patient_rows[
            patient_rows["Timepoint"] == timepoint
        ]

        if matching_rows.empty:
            raise ValueError(
                f"Timepoint '{timepoint}' was not found "
                f"for Victim_ID '{victim_id}'."
            )

        current = matching_rows.iloc[0]
    else:
        current = patient_rows.iloc[-1]

    # Patient profile
    profile_rows = profiles[
        profiles["Victim_ID"] == victim_id
    ]

    profile = (
        profile_rows.iloc[0]
        if not profile_rows.empty
        else None
    )

    # Latest therapist information
    therapist_rows = therapist[
        therapist["Victim_ID"] == victim_id
    ].copy()

    if not therapist_rows.empty:
        therapist_rows["Date_Time"] = pd.to_datetime(
            therapist_rows["Date_Time"]
        )
        therapist_rows = therapist_rows.sort_values("Date_Time")
        therapist_current = therapist_rows.iloc[-1]
    else:
        therapist_current = None

    def clean_value(value):
        if pd.isna(value):
            return None
        return value.item() if hasattr(value, "item") else value

    context = {
        "victim_id": clean_value(current["Victim_ID"]),
        "case_id": clean_value(current["Case_ID"]),

        "case_context": {
            "case_type": clean_value(current["Case_Type"]),
            "case_stage": clean_value(current["Case_Stage"]),
            "checkin_available": clean_value(
                current["Checkin_Available"]
            ),
        },

        "current_state": {
            field: clean_value(current[field])
            for field in QUESTION_ENGINE_STATE_FIELDS
        },

        "events": {
            field: clean_value(current[field])
            for field in EVENT_FIELDS
        },

        "professional_context": {},

        "preferred_language": (
            clean_value(profile["Preferred_Language"])
            if profile is not None
            else None
        ),

        "timepoint": clean_value(current["Timepoint"]),
        "date_time": clean_value(current["Date_Time"]),
    }

    if therapist_current is not None:
        context["professional_context"] = {
            field: clean_value(therapist_current[field])
            for field in THERAPIST_FIELDS
        }

    return context


def load_patient_history(
    victim_id,
    timepoint=None,
    dataset_file=DATASET_FILE,
):
    """
    Return all longitudinal rows for one patient up to and including
    the given timepoint, sorted chronologically.

    Returns a pandas DataFrame.
    Used as input to derive_question_engine_state().
    """
    longitudinal = pd.read_excel(
        dataset_file,
        sheet_name="Longitudinal_Data",
    )

    patient_rows = longitudinal[
        longitudinal["Victim_ID"] == victim_id
    ].copy()

    if patient_rows.empty:
        raise ValueError(
            f"Victim_ID '{victim_id}' was not found in the dataset."
        )

    patient_rows["Date_Time"] = pd.to_datetime(patient_rows["Date_Time"])
    patient_rows = patient_rows.sort_values("Date_Time").reset_index(drop=True)

    if timepoint is not None:
        patient_rows = patient_rows[
            patient_rows["Timepoint"] <= timepoint
        ].reset_index(drop=True)

    return patient_rows


def derive_question_engine_state(patient_context, patient_history_rows):
    """
    Derive Question Engine trigger flags from a patient's longitudinal history.

    Parameters
    ----------
    patient_context      : dict returned by load_patient_context()
    patient_history_rows : DataFrame returned by load_patient_history()

    Returns a partial state dict with exactly the 4 flags that have a
    clear, project-defined rule:

        previous_wellbeing_checkin_exists
            True if at least one prior timepoint exists in the history.

        functioning_trend_declining
            True if the most recent Functioning value is strictly less
            than the previous timepoint's value. Direction only — no
            floor threshold is defined or applied.

        support_network_change_or_SE01_drop
            SE-01 drop component only: True if Social_Support_Checkin
            dropped between the two most recent timepoints.
            The 'support network change' sub-component is NOT implemented
            — no dataset field represents a support network change event.

        safety_intent_active
            True if Threat_Event == 1 at the current timepoint.
            The Safety score (1-5) is NOT mapped — no project-defined
            clinical threshold exists for this conversion.

    NOT implemented (no project-defined rule):
        two_consecutive_low_sleep          — 'low' sleep not defined
        two_or_more_low_wellbeing          — 'low' wellbeing not defined
        low_support_or_high_withdrawal_twice — threshold not defined
        event_trigger_signal               — mapping not defined
        scheduled_safety_check_due         — scheduling not built
        scheduled_safety_support_check_due — scheduling not built
        low_frequency_checkin_due          — scheduling not built
    """
    rows = patient_history_rows
    events = patient_context.get("events", {})
    current_timepoint = patient_context.get("timepoint")

    # ------------------------------------------------------------------
    # 1. previous_wellbeing_checkin_exists
    # ------------------------------------------------------------------
    if current_timepoint is not None and not rows.empty:
        prior_count = int((rows["Timepoint"] < current_timepoint).sum())
        previous_wellbeing_checkin_exists = prior_count > 0
    else:
        previous_wellbeing_checkin_exists = False

    # ------------------------------------------------------------------
    # 2. functioning_trend_declining
    #    Direction only — no floor threshold.
    #    Requires at least two rows in history.
    # ------------------------------------------------------------------
    functioning_trend_declining = False

    if len(rows) >= 2:
        f_prev = rows.iloc[-2]["Functioning"]
        f_curr = rows.iloc[-1]["Functioning"]
        if pd.notna(f_prev) and pd.notna(f_curr):
            functioning_trend_declining = bool(float(f_curr) < float(f_prev))

    # ------------------------------------------------------------------
    # 3. support_network_change_or_SE01_drop
    #    SE-01 drop component only (Social_Support_Checkin).
    #    "Support network change" sub-component NOT implemented:
    #    no dataset field represents this event.
    # ------------------------------------------------------------------
    support_network_change_or_SE01_drop = False

    if len(rows) >= 2:
        sc_prev = rows.iloc[-2]["Social_Support_Checkin"]
        sc_curr = rows.iloc[-1]["Social_Support_Checkin"]
        if pd.notna(sc_prev) and pd.notna(sc_curr):
            support_network_change_or_SE01_drop = bool(
                float(sc_curr) < float(sc_prev)
            )

    # ------------------------------------------------------------------
    # 4. safety_intent_active
    #    Threat_Event == 1 only.
    #    Safety score (1-5) NOT mapped — no project-defined threshold.
    # ------------------------------------------------------------------
    safety_intent_active = (events.get("Threat_Event") == 1)

    return {
        "previous_wellbeing_checkin_exists":   previous_wellbeing_checkin_exists,
        "functioning_trend_declining":          functioning_trend_declining,
        "support_network_change_or_SE01_drop":  support_network_change_or_SE01_drop,
        "safety_intent_active":                 safety_intent_active,
    }