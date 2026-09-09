from sqlalchemy.orm import Session
from app.models.history import InteractionHistory

def log_interaction(db: Session, patient_id: str, interaction_type: str, summary: str, session_id: str = None):
    try:
        interaction = InteractionHistory(
            patient_id=patient_id,
            session_id=session_id,
            interaction_type=interaction_type,
            summary=summary
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return interaction
    except Exception as e:
        print(f"Failed to log interaction: {e}")
        db.rollback()
        return None
