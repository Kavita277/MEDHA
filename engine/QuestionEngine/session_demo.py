from test_engine import (
    load_history,
    select_next_question,
    record_interaction
)

from patient_context import (
    load_patient_context,
    load_patient_history,
    derive_question_engine_state,
)

from datetime import datetime
import uuid
import json


DEMO_HISTORY_FILE = "demo_history.json"
PATIENT_ID = "V0002"
QUESTIONNAIRE_ID = "MEDHA_CHECKIN"
DATASET_FILE = r"c:\Users\Kavita\Desktop\QuestionEngine-medha\MEDHA_Synthetic_1000x30.xlsx"


def save_session(session_record, filename="sessions.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            sessions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        sessions = []

    if not isinstance(sessions, list):
        sessions = []

    sessions.append(session_record)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def save_demo_history(history, filename=DEMO_HISTORY_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def run_session():
    # Use a separate history file for CLI testing.
    # The real history.json remains untouched.
    history = load_history(DEMO_HISTORY_FILE)

    # Load real patient context from the dataset.
    patient_context = load_patient_context(
        victim_id=PATIENT_ID,
        timepoint=19,
        dataset_file=DATASET_FILE
    )
    events = patient_context.get("events", {})

    # Create a unique session.
    session_id = str(uuid.uuid4())

    # Session timestamps.
    session_start_time = datetime.now().isoformat(
        timespec="seconds"
    )

    # For the CLI prototype, notification is treated
    # as the moment the session begins.
    notification_sent_time = session_start_time

    # Counters.
    questions_presented = 0
    questions_answered = 0

    # Question order.
    question_order = 0

    # Existing Question Engine state.
    # Patient context is added without changing
    # the existing question-selection logic.
    state = {
        "scheduled_checkin_due": True,
        "safety_intent_active": False,
        "scheduled_safety_check_due": False,
        "scheduled_safety_support_check_due": False,
        "upcoming_or_recent_case_event": (
            events.get("Upcoming_Hearing", 0) == 1
      ),
        "patient_context": patient_context
    }

    # Derive trigger flags from the patient's longitudinal history.
    # Only the 4 flags with a project-defined rule are computed.
    # This overrides the hand-crafted safety_intent_active default
    # with the real value from Threat_Event in the dataset.
    patient_history = load_patient_history(
        victim_id=PATIENT_ID,
        timepoint=patient_context["timepoint"],
        dataset_file=DATASET_FILE,
    )
    derived_state = derive_question_engine_state(patient_context, patient_history)
    state.update(derived_state)

    print("\n=== MEDHA QUESTION ENGINE ===\n")
    print("Patient:", PATIENT_ID)
    print("Session ID:", session_id)

    while True:

        question = select_next_question(state, history)

        if question is None:
            session_status = "completed"
            break

        question_order += 1
        questions_presented += 1

        # When the question was shown.
        question_presented_time = datetime.now().isoformat(
            timespec="seconds"
        )

        print("\nQuestion:", question["question"])

        answer = input(
            "\nYour answer (or type 'skip'/'quit'): "
        ).strip()
        if answer == "":
            print("Please enter an answer, or type 'skip'/'quit'.")
            continue

        # User ended the session without submitting
        # an answer to the current question.
        if answer.lower() == "quit":
            session_status = "abandoned"
            break

        # When answer/skip was submitted.
        answer_submitted_time = datetime.now().isoformat(
            timespec="seconds"
        )

        if answer.lower() == "skip":

            record = record_interaction(
                question,
                answer=None,
                answered=False,
                skipped=True,
                patient_id=PATIENT_ID,
                filename=DEMO_HISTORY_FILE,
                session_id=session_id,
                questionnaire_id=QUESTIONNAIRE_ID,
                question_order=question_order,
                question_presented_time=question_presented_time,
                answer_submitted_time=answer_submitted_time,
                modality="text"
            )

        else:

            questions_answered += 1

            record = record_interaction(
                question,
                answer=answer,
                answered=True,
                skipped=False,
                patient_id=PATIENT_ID,
                filename=DEMO_HISTORY_FILE,
                session_id=session_id,
                questionnaire_id=QUESTIONNAIRE_ID,
                question_order=question_order,
                question_presented_time=question_presented_time,
                answer_submitted_time=answer_submitted_time,
                modality="text"
            )

        # Add raw interaction/session metadata.
        record["session_id"] = session_id
        record["questionnaire_id"] = QUESTIONNAIRE_ID
        record["question_order"] = question_order
        record["question_presented_time"] = question_presented_time
        record["answer_submitted_time"] = answer_submitted_time
        record["modality"] = "text"

        # Keep current session history available
        # to the question selector.
        history.append(record)

        # Persist the enriched interaction record.
        save_demo_history(history)

        print("\nRecorded:")
        print(record)

        print("\n--- Selecting next question ---")

    # Session ended.
    session_end_time = datetime.now().isoformat(
        timespec="seconds"
    )

    session_record = {
        "user_id": PATIENT_ID,
        "session_id": session_id,
        "questionnaire_id": QUESTIONNAIRE_ID,
        "notification_sent_time": notification_sent_time,
        "session_start_time": session_start_time,
        "session_end_time": session_end_time,
        "session_status": session_status,
        "questions_presented": questions_presented,
        "questions_answered": questions_answered
    }

    # Persist session-level information.
    save_session(session_record)

    print("\n=== SESSION SUMMARY ===")
    print(session_record)


if __name__ == "__main__":
    run_session()