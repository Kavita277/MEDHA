import os
import sys
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.persistence.database import SessionLocal
from backend.persistence.models.checkin import CheckInModel, QuestionRecordModel
from backend.persistence.models.case import Case

def main():
    db = SessionLocal()
    try:
        latest_chk = db.query(CheckInModel).order_by(CheckInModel.created_at.desc()).first()
        if not latest_chk:
            print("No check-ins found.")
            return

        print("=" * 80)
        print(f"LATEST CHECK-IN SESSION: {latest_chk.id}")
        print(f"Patient Case: {latest_chk.victim_id} | Status: {latest_chk.status} | Started: {latest_chk.started_at}")
        print("=" * 80)

        questions = sorted(latest_chk.questions, key=lambda q: q.question_order)
        print(f"\nTotal Questions: {len(questions)} | Answered: {sum(1 for q in questions if q.answer_status == 'answered')}\n")
        print(f"{'#':<3} | {'ID':<6} | {'Status':<10} | {'Answer / User Response':<30} | Question Prompt")
        print("-" * 110)

        for q in questions:
            ans_str = "-"
            if q.answer:
                if isinstance(q.answer, dict):
                    ans_str = q.answer.get("value", json.dumps(q.answer))
                else:
                    ans_str = str(q.answer)
            prompt_truncated = (q.question_text[:50] + "...") if len(q.question_text) > 50 else q.question_text
            print(f"{q.question_order:<3} | {q.question_id:<6} | {q.answer_status:<10} | {str(ans_str):<30} | {prompt_truncated}")

        print("=" * 110)
    finally:
        db.close()

if __name__ == "__main__":
    main()
