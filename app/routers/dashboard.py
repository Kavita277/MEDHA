from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/district")
def get_district_dashboard(db: Session = Depends(get_db)):
    return {
        "High_Risk_Patients": 12,
        "DDS_Distribution": {"Low": 50, "Medium": 30, "High": 20},
        "Escalation_Count": 5,
        "Trend_Graph_Data": [10, 15, 12, 20, 25]
    }

@router.get("/state")
def get_state_dashboard(db: Session = Depends(get_db)):
    return {
        "High_Risk_Patients": 120,
        "DDS_Distribution": {"Low": 500, "Medium": 300, "High": 200},
        "Escalation_Count": 45,
        "Trend_Graph_Data": [100, 150, 120, 200, 250]
    }

@router.get("/national")
def get_national_dashboard(db: Session = Depends(get_db)):
    return {
        "High_Risk_Patients": 1200,
        "DDS_Distribution": {"Low": 5000, "Medium": 3000, "High": 2000},
        "Escalation_Count": 450,
        "Trend_Graph_Data": [1000, 1500, 1200, 2000, 2500]
    }
