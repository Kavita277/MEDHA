import json
from datetime import datetime, timedelta

with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)["questions"]

def recently_asked(question, history, now):
    for item in history:
        if item["question_id"] == question["question_id"]:
            asked = datetime.fromisoformat(item["timestamp"])
            return now - asked < timedelta(days=question["cooldown_days"])
    return False

def trigger_matches(question, state):
    trigger = question["trigger"]

    # -------------------------
    # SAFETY TRIGGERS
    # -------------------------

    if trigger == "safety_intent_active":
        return state.get("safety_intent_active", False)

    if trigger == "scheduled_safety_check":
        return state.get("scheduled_safety_check_due", False)

    if trigger == "scheduled_safety_support_check":
        return state.get("scheduled_safety_support_check_due", False)

    # -------------------------
    # EVENT TRIGGERS
    # -------------------------

    if trigger == "upcoming_or_recent_case_event":
        return state.get("upcoming_or_recent_case_event", False)

    if trigger == "event_trigger_signal":
        return state.get("event_trigger_signal", False)

    # -------------------------
    # SLEEP / FUNCTIONING
    # -------------------------

    if trigger == "two_consecutive_low_SF01_scores":
        return state.get("two_consecutive_low_sleep", False)

    if trigger == "functioning_trend_declining":
        return state.get("functioning_trend_declining", False)

    # -------------------------
    # GENERAL WELLBEING
    # -------------------------

    if trigger == "two_or_more_low_GW01_scores":
        return state.get("two_or_more_low_wellbeing", False)

    if trigger == "previous_wellbeing_checkin_exists":
        return (
            state.get("scheduled_checkin_due", False)
            and state.get("previous_wellbeing_checkin_exists", False)
        )

    # -------------------------
    # SOCIAL SUPPORT
    # -------------------------

    if trigger == "support_network_change_or_SE01_drop":
        return state.get("support_network_change_or_SE01_drop", False)

    if trigger == "low_SE01_or_high_withdrawal_twice":
        return state.get("low_support_or_high_withdrawal_twice", False)

    # -------------------------
    # ROUTINE QUESTIONS
    # -------------------------

    if trigger == "scheduled_checkin":
        return state.get("scheduled_checkin_due", False)

    if trigger == "low_frequency_scheduled":
        return state.get("low_frequency_checkin_due", False)

    # Unknown trigger = NOT active
    return False

def load_history(filename="history.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history, filename="history.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
def load_history(filename="demo_history.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history, filename="history.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def record_interaction(
    question,
    answer=None,
    answered=False,
    skipped=False,
    patient_id="DEMO-001",
    filename="history.json",
    session_id=None,
    questionnaire_id=None,
    question_order=None,
    question_presented_time=None,
    answer_submitted_time=None,
    modality=None
):
    history = load_history(filename)
    structured_output = None

    if answered and answer is not None:

        structured_output = parse_structured_answer(
            question,
            answer
        )

        # Only genuine free-text questions go to the NLP/Text Model.
        # Fixed response types (scale, yes/no, multiple-choice) never
        # reach this branch - they are handled by parse_structured_answer.
        if question.get("response_type") in {
            "optional_text",
            "optional_text_or_voice"
        }:
            from nlp_interface import extract_free_text_signals
            structured_output = extract_free_text_signals(answer)

    record = {
        "patient_id": patient_id,
        "question_id": question["question_id"],
        "intent": question["intent"],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "trigger": question["trigger"],
        "answer": answer,
        "response_type": question["response_type"],
        "structured_output": structured_output,
        "response_valid": is_response_valid(question, answer),
        "answered": answered,
        "skipped": skipped
    }

    if session_id is not None:
        record["session_id"] = session_id
    if questionnaire_id is not None:
        record["questionnaire_id"] = questionnaire_id
    if question_order is not None:
        record["question_order"] = question_order
    if question_presented_time is not None:
        record["question_presented_time"] = question_presented_time
    if answer_submitted_time is not None:
        record["answer_submitted_time"] = answer_submitted_time
    if modality is not None:
        record["modality"] = modality

    history.append(record)
    save_history(history, filename)

    return record
def parse_structured_answer(question, answer):
    """
    Convert a user's answer into structured data
    that other MEDHA modules can use.
    """

    question_id = question["question_id"]

    # 1–5 scale questions
    scale_questions = {
        "GW-01": "wellbeing_score",
        "GW-03": "energy_score",
        "SF-01": "sleep_score",
        "SF-05": "concentration_change_score",
        "ES-02": "event_coping_score",
        "ES-06": "hypervigilance_score",
        "SE-01": "perceived_support_score"
    }

    if question_id in scale_questions:
        try:
            score = int(answer)

            if 1 <= score <= 5:
                return {
                    scale_questions[question_id]: score
                }

        except ValueError:
            return {
                "parse_error": "Expected a number from 1 to 5"
            }

    # Yes / No questions
    yes_no_questions = {
        "SA-01": "feels_safe",
        "SA-02": "active_threat_flag",
        "SA-04": "has_immediate_contact",
        "SE-02": "recent_support_contact"
    }

    if question_id in yes_no_questions:

        answer_lower = answer.strip().lower()

        if answer_lower in ["yes", "y"]:
            return {
                yes_no_questions[question_id]: True
            }

        if answer_lower in ["no", "n"]:
            return {
                yes_no_questions[question_id]: False
            }

        return {
            "parse_error": "Expected yes or no"
        }

    # Unknown/free-text answers are kept as text for now.
        # Multiple-choice questions
    multiple_choice_questions = {
        "GW-05": "self_reported_trend",
        "SF-02": "functioning_level",
        "ES-03": "intrusion_frequency"
    }

    multiple_choice_values = {
        "GW-05": {
            "better",
            "worse",
            "same",
            "prefer_not_to_say"
        },
        "SF-02": {
            "fully",
            "mostly",
            "partially",
            "not_at_all"
        },
        "ES-03": {
            "never",
            "rarely",
            "sometimes",
            "often",
            "very_often"
        }
    }

    if question_id in multiple_choice_questions:
        answer_lower = answer.strip().lower()

        if answer_lower in multiple_choice_values[question_id]:
            return {
                multiple_choice_questions[question_id]: answer_lower
            }

        return {
            "parse_error": "Invalid multiple-choice answer"
        }

    # Multiple-choice with optional text
    multiple_choice_optional_questions = {
        "SA-03": "basic_needs_status"
    }

    if question_id in multiple_choice_optional_questions:
        answer_lower = answer.strip().lower()

        if answer_lower in {
            "all",
            "some_not_all",
            "none"
        }:
            return {
                multiple_choice_optional_questions[question_id]: answer_lower
            }

        return {
            "parse_error": "Expected all, some_not_all, or none"
        }

    # Yes / No with optional text
    yes_no_optional_questions = {
        "ES-01": "trigger_sensitivity_flag",
        "SE-03": "support_network_change_flag"
    }

    if question_id in yes_no_optional_questions:
        answer_lower = answer.strip().lower()

        if answer_lower in {"yes", "y"}:
            return {
                yes_no_optional_questions[question_id]: True
            }

        if answer_lower in {"no", "n"}:
            return {
                yes_no_optional_questions[question_id]: False
            }

        return {
            "parse_error": "Expected yes or no"
        }

    question_id = question["question_id"]

    # 1–5 scale questions
    scale_questions = {
        "GW-01": "wellbeing_score",
        "GW-03": "energy_score",
        "SF-01": "sleep_score",
        "SF-05": "concentration_change_score",
        "ES-02": "event_coping_score",
        "ES-06": "hypervigilance_score",
        "SE-01": "perceived_support_score"
    }

    if question_id in scale_questions:
        try:
            score = int(answer)

            if 1 <= score <= 5:
                return {
                    scale_questions[question_id]: score
                }

        except ValueError:
            return {
                "parse_error": "Expected a number from 1 to 5"
            }

    # Yes / No questions
    yes_no_questions = {
        "SA-01": "feels_safe",
        "SA-02": "active_threat_flag",
        "SA-04": "has_immediate_contact",
        "SE-02": "recent_support_contact"
    }

    if question_id in yes_no_questions:

        answer_lower = answer.strip().lower()

        if answer_lower in ["yes", "y"]:
            return {
                yes_no_questions[question_id]: True
            }

        if answer_lower in ["no", "n"]:
            return {
                yes_no_questions[question_id]: False
            }

        return {
            "parse_error": "Expected yes or no"
        }
            # Optional text questions
    optional_text_questions = {
        "SF-03": "sleep_context_text",
        "GW-06": "context_text"
    }

    if question_id in optional_text_questions:
        return {
            optional_text_questions[question_id]: answer
        }
    # Unknown/free-text answers are kept as text for now.
    return {
        "raw_text": answer
    }
    
def is_response_valid(question, answer):
    """
    Check whether the user's response matches the expected
    response format of the question.
    """

    if answer is None:
        return False

    response_type = question.get("response_type")
    answer_lower = str(answer).strip().lower()

    # 1–5 scale
    if response_type == "scale_1_5":
        try:
            score = int(answer)
            return 1 <= score <= 5
        except (ValueError, TypeError):
            return False

    # Yes / No
    if response_type == "yes_no":
        return answer_lower in {
            "yes",
            "y",
            "no",
            "n"
        }

    # Multiple choice
    if response_type == "multiple_choice":
        return answer_lower in {
            "better",
            "worse",
            "same",
            "prefer_not_to_say",
            "fully",
            "mostly",
            "partially",
            "not_at_all",
            "never",
            "rarely",
            "sometimes",
            "often",
            "very_often"
        }

    # Multiple choice with optional text
    if response_type == "multiple_choice_optional_text":
        return answer_lower in {
            "all",
            "some_not_all",
            "none"
        }

    # Yes / No with optional text
    if response_type == "yes_no_optional_text":
        return answer_lower in {
            "yes",
            "y",
            "no",
            "n"
        }

    # Optional/free text
    if response_type in {
        "optional_text",
        "optional_text_or_voice"
    }:
        return True

    # Unknown format — don't assume it's valid.
    return False 
    
def ask_and_record(question):
    print("\nMEDHA:")
    print(question["question"])

    answer = input("\nYour answer (or type 'skip'): ")

    if answer.lower() == "skip":
        record_interaction(
            question,
            answer=None,
            answered=False,
            skipped=True
        )
        print("Recorded as skipped.")
    else:
        record_interaction(
            question,
            answer=answer,
            answered=True,
            skipped=False
        )
        print("Answer recorded.")   
        
def run_checkin(state):
    history = load_history()

    question = select_next_question(state, history)

    if question is None:
        print("\nMEDHA: No question is due right now.")
        return

    print("\nSelected question:", question["question_id"])

    ask_and_record(question)             
     
def apply_case_event_wording(question, state):
    if question.get("question_id") != "ES-02":
        return question

    events = (state.get("patient_context") or {}).get("events") or {}

    if events.get("Upcoming_Hearing") != 1:
        return question

    filled = dict(question)
    filled["question"] = (
        "We noticed you have an upcoming hearing. "
        "How are you coping with this?"
    )
    return filled


def select_next_question(state, history):
    now = datetime.now()

    # Priority 1: Safety
    safety_candidates = [
        q for q in QUESTIONS
        if q["intent"] == "safety_support"
        and trigger_matches(q, state)
        and not recently_asked(q, history, now)
    ]

    if safety_candidates:
        return apply_case_event_wording(safety_candidates[0], state)

    # Priority 2: Event-related
    event_candidates = [
        q for q in QUESTIONS
        if q["intent"] == "event_related_stress"
        and trigger_matches(q, state)
        and not recently_asked(q, history, now)
    ]

    if event_candidates:
        return apply_case_event_wording(event_candidates[0], state)

    # Priority 3: ADAPTIVE symptom/social/wellbeing triggers ONLY.
    # Do NOT include ordinary scheduled_checkin questions here.
    # NOTE: "general_wellbeing" added so GW-05 and GW-06 (which have
    # conditional non-scheduled triggers) are reachable at this tier.
    # Without this they fall through all buckets and are never selected.
    candidates = [
        q for q in QUESTIONS
        if q["intent"] in {
            "sleep_functioning",
            "social_emotional_support",
            "general_wellbeing",
        }
        and q["trigger"] != "scheduled_checkin"
        and trigger_matches(q, state)
        and not recently_asked(q, history, now)
    ]

    if candidates:
        return apply_case_event_wording(candidates[0], state)

    # Priority 4: Routine check-in
    # Exactly ONE routine question.
    if state.get("scheduled_checkin_due", False):

        routine_candidates = [
            q for q in QUESTIONS
            if q["trigger"] == "scheduled_checkin"
            and not recently_asked(q, history, now)
        ]

        if routine_candidates:

            # First-ever check-in starts with GW-01.
            if not history:
                for q in routine_candidates:
                    if q["question_id"] == "GW-01":
                        return apply_case_event_wording(q, state)

            # Otherwise rotate to the least recently asked question.
            def last_time(q):
                times = [
                    datetime.fromisoformat(h["timestamp"])
                    for h in history
                    if h.get("question_id") == q["question_id"]
                ]

                return max(times) if times else datetime.min

            return apply_case_event_wording(
                sorted(routine_candidates, key=last_time)[0],
                state
            )

    return None
def run_demo_tests():
    # Test 1: Event beats sleep.
    state = {
        "scheduled_checkin_due": True,
        "upcoming_or_recent_case_event": True,
        "two_consecutive_low_sleep": True,
        "safety_intent_active": False
    }
    q = select_next_question(state, [])
    print("TEST 1 — Event priority")
    print("Expected: ES-02")
    print("Selected:", q["question_id"] if q else None)
    print()

    # Test 2: Safety beats event and symptoms.
    state["safety_intent_active"] = True
    q = select_next_question(state, [])
    print("TEST 2 — Safety priority")
    print("Expected: SA-01")
    print("Selected:", q["question_id"] if q else None)
    print()

    # Test 3: Recently asked ES-02 should be skipped.
    recent = [{
        "question_id": "ES-02",
        "intent": "event_related_stress",
        "timestamp": datetime.now().isoformat(),
        "answered": True
    }]
    state["safety_intent_active"] = False
    q = select_next_question(state, recent)
    print("TEST 3 — Cooldown")
    print("Expected: not ES-02; likely a symptom question")
    print("Selected:", q["question_id"] if q else None)
    print()

    # Test 4: No special trigger -> scheduled general question.
    state = {
        "scheduled_checkin_due": True,
        "upcoming_or_recent_case_event": False,
        "two_consecutive_low_sleep": False,
        "safety_intent_active": False,
        "functioning_trend_declining": False,
        "support_network_change_or_SE01_drop": False,
        "low_support_or_high_withdrawal_twice": False
    }
    q = select_next_question(state, [])
    print("TEST 4 — General fallback")
    print("Expected: GW-01")
    print("Selected:", q["question_id"] if q else None)


def run_integration_tests():
    """
    MEDHA Question Engine - Integration & Unit Test Suite

    SECTION A - Dataset-Derived Integration Tests (T1, T2, T7)
        Require MEDHA_Synthetic_1000x30.xlsx at the working directory.

    SECTION B - Selector Unit Tests (T3-T6, T8, T9)
        Flags are set directly in synthetic state dicts.
        NOT claimed to be derived from the dataset.
        Purpose: verify the selector responds correctly to each flag.

    SECTION C - CLI Smoke Test (T10)
        Runs session_demo.py as a subprocess.
    """
    import pandas as pd
    import subprocess
    import sys
    from patient_context import derive_question_engine_state

    DATASET_FILE = "MEDHA_Synthetic_1000x30.xlsx"
    pass_count = 0
    fail_count = 0

    def check(label, condition, detail=""):
        nonlocal pass_count, fail_count
        if condition:
            print(f"  PASS  {label}")
            pass_count += 1
        else:
            msg = f"  FAIL  {label}"
            if detail:
                msg += f"\n        ({detail})"
            print(msg)
            fail_count += 1

    print()
    print("=" * 62)
    print("MEDHA QUESTION ENGINE - INTEGRATION & UNIT TESTS")
    print("=" * 62)

    # Load dataset once for all data-driven tests.
    print("\n[Loading longitudinal data - this may take a moment...]")
    dataset_available = False
    long_df = None
    try:
        long_df = pd.read_excel(DATASET_FILE, sheet_name="Longitudinal_Data")
        print(f"[Loaded {len(long_df):,} rows]\n")
        dataset_available = True
    except Exception as exc:
        print(f"[WARN] Dataset could not be loaded: {exc}")
        print("[WARN] Tests T1, T2, T7 will be skipped.\n")

    # ============================================================
    # SECTION A - Dataset-Derived Integration Tests
    # ============================================================
    print("--- SECTION A: Dataset-Derived Integration Tests ---\n")

    # T1: V0002 Timepoint 19 -> ES-02
    q_t1 = None
    state_t1 = None
    if dataset_available:
        try:
            v2 = (
                long_df[long_df["Victim_ID"] == "V0002"]
                .sort_values("Timepoint")
            )
            v2_t19 = v2[v2["Timepoint"] == 19].iloc[0]
            state_t1 = {
                "scheduled_checkin_due": True,
                "safety_intent_active": False,
                "scheduled_safety_check_due": False,
                "scheduled_safety_support_check_due": False,
                "low_frequency_checkin_due": False,
                "upcoming_or_recent_case_event": (
                    int(v2_t19["Upcoming_Hearing"]) == 1
                ),
                "two_consecutive_low_sleep": False,
                "functioning_trend_declining": False,
                "support_network_change_or_SE01_drop": False,
                "low_support_or_high_withdrawal_twice": False,
                "previous_wellbeing_checkin_exists": False,
                "two_or_more_low_wellbeing": False,
                "patient_context": {
                    "events": {
                        "Upcoming_Hearing":   int(v2_t19["Upcoming_Hearing"]),
                        "Compensation_Delay": int(v2_t19["Compensation_Delay"]),
                        "Threat_Event":        int(v2_t19["Threat_Event"]),
                        "Protection_Event":    int(v2_t19["Protection_Event"]),
                    }
                },
            }
            q_t1 = select_next_question(state_t1, [])
            check(
                "T1: V0002 Timepoint 19 -> ES-02 selected",
                q_t1 is not None and q_t1["question_id"] == "ES-02",
                f"got {q_t1['question_id'] if q_t1 else 'None'}",
            )
        except Exception as exc:
            check("T1: V0002 Timepoint 19 -> ES-02", False, str(exc))
    else:
        print("  SKIP  T1 (dataset unavailable)")

    # T2: ES-02 wording check
    if dataset_available and q_t1 is not None:
        try:
            text = q_t1["question"]
            check(
                'T2a: ES-02 -> "upcoming hearing" in question text',
                "upcoming hearing" in text.lower(),
                f'got: "{text}"',
            )
            check(
                'T2b: ES-02 -> "[case-related event]" NOT in text',
                "[case-related event]" not in text,
                f'got: "{text}"',
            )
        except Exception as exc:
            check("T2: ES-02 wording", False, str(exc))
    elif not dataset_available:
        print("  SKIP  T2 (dataset unavailable)")
    else:
        print("  SKIP  T2 (T1 did not return a question)")

    # ============================================================
    # SECTION B - Selector Unit Tests (Synthetic State)
    # ============================================================
    print("\n--- SECTION B: Selector Unit Tests (Synthetic State) ---\n")

    _base = {
        "scheduled_checkin_due": True,
        "safety_intent_active": False,
        "upcoming_or_recent_case_event": False,
        "two_consecutive_low_sleep": False,
        "functioning_trend_declining": False,
        "support_network_change_or_SE01_drop": False,
        "low_support_or_high_withdrawal_twice": False,
        "previous_wellbeing_checkin_exists": False,
        "two_or_more_low_wellbeing": False,
        "scheduled_safety_check_due": False,
        "scheduled_safety_support_check_due": False,
        "low_frequency_checkin_due": False,
        "patient_context": {"events": {}},
    }

    def synth(**overrides):
        s = dict(_base)
        s.update(overrides)
        return s

    # T3: Safety priority beats event trigger
    q_t3 = select_next_question(
        synth(
            safety_intent_active=True,
            upcoming_or_recent_case_event=True,
            patient_context={"events": {"Upcoming_Hearing": 1}},
        ), []
    )
    check(
        "T3: safety_intent_active=True beats event trigger -> SA-01",
        q_t3 is not None and q_t3["question_id"] == "SA-01",
        f"got {q_t3['question_id'] if q_t3 else 'None'}",
    )

    # T4 [UNIT]: two_consecutive_low_sleep -> SF-03
    # Flag NOT dataset-derived. 'Low sleep' threshold not project-defined.
    # Tests only that the selector picks SF-03 when the flag is externally set.
    q_t4 = select_next_question(synth(two_consecutive_low_sleep=True), [])
    check(
        "T4 [UNIT]: two_consecutive_low_sleep=True -> SF-03 (flag not dataset-derived)",
        q_t4 is not None and q_t4["question_id"] == "SF-03",
        f"got {q_t4['question_id'] if q_t4 else 'None'}",
    )

    # T5 [UNIT]: two_or_more_low_wellbeing -> GW-06
    # Flag NOT dataset-derived. 'Low wellbeing' threshold not project-defined.
    # Tests only that the selector picks GW-06 when the flag is externally set.
    q_t5 = select_next_question(synth(two_or_more_low_wellbeing=True), [])
    check(
        "T5 [UNIT]: two_or_more_low_wellbeing=True -> GW-06 (flag not dataset-derived)",
        q_t5 is not None and q_t5["question_id"] == "GW-06",
        f"got {q_t5['question_id'] if q_t5 else 'None'}",
    )

    # T6: previous_wellbeing_checkin_exists -> GW-05 (flag IS dataset-derived)
    q_t6 = select_next_question(synth(previous_wellbeing_checkin_exists=True), [])
    check(
        "T6: previous_wellbeing_checkin_exists=True -> GW-05",
        q_t6 is not None and q_t6["question_id"] == "GW-05",
        f"got {q_t6['question_id'] if q_t6 else 'None'}",
    )

    # T7: safety_intent_active derived via derive_question_engine_state from Threat_Event==1
    if dataset_available:
        try:
            threat_rows = long_df[long_df["Threat_Event"] == 1]
            if threat_rows.empty:
                print("  SKIP  T7 (no Threat_Event=1 rows in dataset)")
            else:
                row = threat_rows.iloc[0]
                vid = row["Victim_ID"]
                tp = int(row["Timepoint"])
                hist = (
                    long_df[long_df["Victim_ID"] == vid]
                    .sort_values("Timepoint")
                )
                hist = hist[hist["Timepoint"] <= tp].reset_index(drop=True)
                ctx = {
                    "timepoint": tp,
                    "events": {"Threat_Event": int(row["Threat_Event"])},
                }
                derived = derive_question_engine_state(ctx, hist)
                check(
                    f"T7a: {vid}/T{tp} Threat_Event=1 -> safety_intent_active=True",
                    derived["safety_intent_active"] is True,
                    f"got {derived['safety_intent_active']}",
                )
                q_t7 = select_next_question(
                    synth(
                        safety_intent_active=derived["safety_intent_active"],
                        patient_context={"events": {"Upcoming_Hearing": 0}},
                    ), []
                )
                check(
                    "T7b: safety_intent_active from Threat_Event -> SA-01 selected",
                    q_t7 is not None and q_t7["question_id"] == "SA-01",
                    f"got {q_t7['question_id'] if q_t7 else 'None'}",
                )
        except Exception as exc:
            check("T7: Threat_Event->safety_intent_active", False, str(exc))
    else:
        print("  SKIP  T7 (dataset unavailable)")

    # T8: Cooldown - recently asked ES-02 not re-selected
    recent_hist = [{"question_id": "ES-02", "timestamp": datetime.now().isoformat()}]
    q_t8 = select_next_question(
        synth(upcoming_or_recent_case_event=True), recent_hist
    )
    check(
        "T8: cooldown - ES-02 recently asked, not re-selected",
        q_t8 is None or q_t8["question_id"] != "ES-02",
        f"got {q_t8['question_id'] if q_t8 else 'None (no question due)'}",
    )

    # T9: No active trigger, empty history -> routine fallback -> GW-01
    q_t9 = select_next_question(synth(), [])
    check(
        "T9: no trigger + empty history -> routine fallback -> GW-01",
        q_t9 is not None and q_t9["question_id"] == "GW-01",
        f"got {q_t9['question_id'] if q_t9 else 'None'}",
    )

    # ============================================================
    # SECTION C - CLI Smoke Test
    # ============================================================
    print("\n--- SECTION C: CLI Smoke Test ---\n")
    print("  [T10 launches session_demo.py as subprocess.")
    print("   The Excel loads twice inside that process.")
    print("   Allow several minutes for this test.]\n")

    try:
        result = subprocess.run(
            [sys.executable, "session_demo.py"],
            input="quit\n",
            capture_output=True,
            text=True,
            timeout=600,
        )
        stdout_lower = result.stdout.lower()
        no_crash = (
            result.returncode == 0
            and "traceback" not in stdout_lower
            and "error" not in result.stderr.lower()
        )
        check(
            "T10: session_demo.py exits cleanly (no exception)",
            no_crash,
            (
                f"returncode={result.returncode} "
                f"stderr={result.stderr[:300].strip()!r}"
            ) if not no_crash else "",
        )
        if no_crash:
            heard = "upcoming hearing" in stdout_lower
            check(
                'T10b: CLI output contains "upcoming hearing" wording',
                heard,
                "wording not found in stdout" if not heard else "",
            )
    except subprocess.TimeoutExpired:
        check("T10: session_demo.py CLI smoke", False, "subprocess timed out (>600s)")
    except Exception as exc:
        check("T10: session_demo.py CLI smoke", False, str(exc))

    # ============================================================
    # Summary
    # ============================================================
    print()
    print("=" * 62)
    print(f"RESULT: {pass_count} passed, {fail_count} failed")
    print("=" * 62)


if __name__ == "__main__":

    # SCENARIO 1 - Upcoming hearing
    print("\n--- SCENARIO 1: Upcoming hearing ---")

    state = {
        "scheduled_checkin_due": True,
        "upcoming_or_recent_case_event": True,
        "safety_intent_active": False,
        "two_consecutive_low_sleep": False,
        "functioning_trend_declining": False,
        "support_network_change_or_SE01_drop": False,
        "low_support_or_high_withdrawal_twice": False,
        "scheduled_safety_check_due": False,
        "scheduled_safety_support_check_due": False,
        "low_frequency_checkin_due": False,
        "previous_wellbeing_checkin_exists": False
    }

    history = []
    question = select_next_question(state, history)

    print("Expected: ES-02")
    print("Selected:", question["question_id"])


    # SCENARIO 2 - Safety concern
    print("\n--- SCENARIO 2: Safety concern ---")

    state["upcoming_or_recent_case_event"] = False
    state["safety_intent_active"] = True

    question = select_next_question(state, [])

    print("Expected: SA-01")
    print("Selected:", question["question_id"])


    # SCENARIO 3 - Worsening sleep
    print("\n--- SCENARIO 3: Worsening sleep ---")

    state = {
        "scheduled_checkin_due": True,
        "upcoming_or_recent_case_event": False,
        "safety_intent_active": False,
        "two_consecutive_low_sleep": True,
        "functioning_trend_declining": False,
        "support_network_change_or_SE01_drop": False,
        "low_support_or_high_withdrawal_twice": False,
        "scheduled_safety_check_due": False,
        "scheduled_safety_support_check_due": False,
        "low_frequency_checkin_due": False,
        "previous_wellbeing_checkin_exists": False
    }

    question = select_next_question(state, [])

    print("Expected: SF-03")
    print("Selected:", question["question_id"])

    print("\n")
    run_integration_tests()
