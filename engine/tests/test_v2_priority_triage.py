import pytest
import pandas as pd
import numpy as np

from engine.v2.priority_triage import TriageEngine

@pytest.fixture
def triage_engine():
    return TriageEngine()

def test_missing_data_handling(triage_engine):
    """Test Case E / missing data handling (both NaN)."""
    df = pd.DataFrame([{
        "Fusion_DDS_Prediction": np.nan,
        "Temporal_Risk_Score": np.nan,
        "Future_Escalation_Flag": np.nan
    }])
    
    out = triage_engine.evaluate(df)
    assert out.iloc[0]["Priority_Level"] == "UNKNOWN"
    assert "Missing both" in out.iloc[0]["Priority_Rationale"]

def test_boundary_values(triage_engine):
    """Test boundary conditions exactly at the thresholds."""
    df = pd.DataFrame([
        # Exact boundaries
        {"Fusion_DDS_Prediction": 75.0, "Temporal_Risk_Score": 0.0, "Future_Escalation_Flag": 0},
        {"Fusion_DDS_Prediction": 0.0, "Temporal_Risk_Score": 0.85, "Future_Escalation_Flag": 1},
        {"Fusion_DDS_Prediction": 50.0, "Temporal_Risk_Score": 0.0, "Future_Escalation_Flag": 0},
        {"Fusion_DDS_Prediction": 0.0, "Temporal_Risk_Score": 0.50, "Future_Escalation_Flag": 0},
        {"Fusion_DDS_Prediction": 25.0, "Temporal_Risk_Score": 0.0, "Future_Escalation_Flag": 0},
        {"Fusion_DDS_Prediction": 0.0, "Temporal_Risk_Score": 0.25, "Future_Escalation_Flag": 0},
    ])
    
    out = triage_engine.evaluate(df)
    
    assert out.iloc[0]["Priority_Level"] == "CRITICAL"
    assert out.iloc[1]["Priority_Level"] == "CRITICAL"
    assert out.iloc[2]["Priority_Level"] == "HIGH"
    assert out.iloc[3]["Priority_Level"] == "HIGH"
    assert out.iloc[4]["Priority_Level"] == "MEDIUM"
    assert out.iloc[5]["Priority_Level"] == "MEDIUM"

def test_four_cases(triage_engine):
    """Test combinations of low and high."""
    df = pd.DataFrame([
        {"case": "Case A", "Fusion_DDS_Prediction": 10.0, "Temporal_Risk_Score": 0.10, "Future_Escalation_Flag": 0}, # Low / Low
        {"case": "Case B", "Fusion_DDS_Prediction": 60.0, "Temporal_Risk_Score": 0.10, "Future_Escalation_Flag": 0}, # High / Low
        {"case": "Case C", "Fusion_DDS_Prediction": 10.0, "Temporal_Risk_Score": 0.60, "Future_Escalation_Flag": 1}, # Low / High
        {"case": "Case D", "Fusion_DDS_Prediction": 80.0, "Temporal_Risk_Score": 0.90, "Future_Escalation_Flag": 1}, # High / High
    ])
    
    out = triage_engine.evaluate(df)
    
    assert out.iloc[0]["Priority_Level"] == "LOW"
    assert out.iloc[1]["Priority_Level"] == "HIGH"
    assert out.iloc[2]["Priority_Level"] == "HIGH"
    assert out.iloc[3]["Priority_Level"] == "CRITICAL"

def test_missing_future_risk(triage_engine):
    """Test Case F / Insufficient GRU history (Future Risk NaN but DDS present)."""
    df = pd.DataFrame([
        {"Fusion_DDS_Prediction": 60.0, "Temporal_Risk_Score": np.nan, "Future_Escalation_Flag": np.nan},
        {"Fusion_DDS_Prediction": 10.0, "Temporal_Risk_Score": np.nan, "Future_Escalation_Flag": np.nan},
    ])
    
    out = triage_engine.evaluate(df)
    
    assert out.iloc[0]["Priority_Level"] == "HIGH"
    assert out.iloc[1]["Priority_Level"] == "LOW"

def test_missing_dds(triage_engine):
    """Test missing DDS but present Future Risk."""
    df = pd.DataFrame([
        {"Fusion_DDS_Prediction": np.nan, "Temporal_Risk_Score": 0.90, "Future_Escalation_Flag": 1.0},
        {"Fusion_DDS_Prediction": np.nan, "Temporal_Risk_Score": 0.10, "Future_Escalation_Flag": 0.0},
    ])
    
    out = triage_engine.evaluate(df)
    
    assert out.iloc[0]["Priority_Level"] == "CRITICAL"
    assert out.iloc[1]["Priority_Level"] == "LOW"

def test_semantic_separation_preserved(triage_engine):
    """Ensure raw ML columns are not modified or dropped."""
    df = pd.DataFrame([{
        "Victim_ID": "V001",
        "Timepoint": 7,
        "Fusion_DDS_Prediction": 45.123,
        "Temporal_Risk_Score": 0.123,
        "Future_Escalation_Flag": 0
    }])
    
    out = triage_engine.evaluate(df)
    
    # Check that original columns are still there and unmodified
    assert out.iloc[0]["Fusion_DDS_Prediction"] == 45.123
    assert out.iloc[0]["Temporal_Risk_Score"] == 0.123
    
    # Check that aliased variables are created
    assert out.iloc[0]["Current_DDS"] == 45.123
    assert out.iloc[0]["Future_Risk_Probability"] == 0.123
