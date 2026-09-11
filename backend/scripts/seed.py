"""
MEDHA Demo Seeder Script
========================

CLI command to populate the database with realistic multi-case longitudinal
demo data for Dr. Eleanor Vance using the real MEDHA V2 inference pipeline.

Usage:
    python backend/scripts/seed.py [--force]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.persistence.database import SessionLocal
from backend.services.seed_service import seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("medha.seed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MEDHA multi-case demo data.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-generation of existing prediction records.",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Optional database URL override (e.g. sqlite:///./demo.db or postgresql://...)",
    )
    args = parser.parse_args()

    if args.db_url:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.persistence.database import Base
        import backend.persistence.models  # noqa: F401

        connect_args = {"check_same_thread": False} if args.db_url.startswith("sqlite") else {}
        engine = create_engine(args.db_url, connect_args=connect_args)
        Base.metadata.create_all(bind=engine)
        SessionOverride = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionOverride()
    else:
        db = SessionLocal()
    try:
        result = seed_demo_data(db, force_refresh=args.force)
        print("\n=======================================================")
        print("          MEDHA DEMO DATA SEED SUMMARY                ")
        print("=======================================================")
        print(f"Therapist: {result['therapist']['name']} ({result['therapist']['email']})")
        print(f"Cases Created: {result['cases_created']}, Reused: {result['cases_reused']}")
        print(f"Timepoints Processed: {result['timepoints_seeded']}")
        print(f"Predictions Generated: {result['predictions_generated']}")
        print("-------------------------------------------------------")
        for detail in result["details"]:
            print(f"\nCase: {detail['victim_id']} ({detail['patient_name']}) - Target Profile: {detail['profile']}")
            for tp in detail["timepoints"]:
                print(
                    f"  T{tp['timepoint']} -> Fusion DDS: {tp['fusion_dds_prediction']}, "
                    f"Triage: {tp['triage_level']}, "
                    f"Temporal Risk: {tp['temporal_risk_score']}"
                )
        print("=======================================================\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
