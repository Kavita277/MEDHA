import uuid
from backend.config import get_settings
from backend.persistence.base import Base
from backend.persistence.database import engine, SessionLocal, create_all_tables
from backend.persistence.models.user import User, UserRole, UserStatus
from backend.persistence.models.therapist import Therapist
from backend.security.passwords import hash_password

def seed():
    create_all_tables(engine)
    with SessionLocal() as db:
        # Check if therapist exists
        therapist_user = db.query(User).filter_by(email="therapist@medha.org").first()
        if not therapist_user:
            therapist_user = User(
                id=uuid.uuid4(),
                role=UserRole.THERAPIST,
                name="Dr. Jane Clinician",
                email="therapist@medha.org",
                mobile="+919876543202",
                password_hash=hash_password("TherapistPass123!"),
                status=UserStatus.ACTIVE,
            )
            db.add(therapist_user)
            db.flush()

            therapist_profile = Therapist(
                id=uuid.uuid4(),
                user_id=therapist_user.id,
                display_name="Dr. Jane Clinician, Psy.D.",
            )
            db.add(therapist_profile)
            print("Created Therapist: therapist@medha.org / TherapistPass123!")
        else:
            print("Therapist already exists")

        # Check if patient exists
        patient_user = db.query(User).filter_by(email="patient@medha.org").first()
        if not patient_user:
            patient_user = User(
                id=uuid.uuid4(),
                role=UserRole.USER,
                name="John Patient",
                email="patient@medha.org",
                mobile="+919876543201",
                password_hash=hash_password("PatientPass123!"),
                status=UserStatus.ACTIVE,
            )
            db.add(patient_user)
            db.flush()
            print("Created Patient: patient@medha.org / PatientPass123!")
            
            # Create a Case for the patient!
            from backend.persistence.models.case import Case, CaseStatus
            case = Case(
                id=uuid.uuid4(),
                victim_id=f"V-{uuid.uuid4().hex[:6].upper()}",
                user_id=patient_user.id,
                therapist_id=therapist_profile.id,
                status=CaseStatus.ACTIVE,
            )
            db.add(case)
            print("Created Case for patient@medha.org")
        else:
            print("Patient already exists")

        db.commit()

if __name__ == "__main__":
    seed()
