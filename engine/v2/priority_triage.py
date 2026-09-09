"""
MEDHA V2 Step 15: Priority / Triage Layer

WARNING: The threshold logic in this file is an ENGINEERING DEMONSTRATION PROTOTYPE.
It is based on the legacy prototype in `engine/fusion_engine/priority_thresholds.py`.
These thresholds are NOT clinically validated and MUST be tuned in coordination
with mental health professionals before clinical deployment.

This module processes the downstream outputs of the V2 Machine Learning pipeline.
It strictly preserves the raw machine-learning predictions and never feeds
the priority level back into the models.
"""

import pandas as pd
import numpy as np

class TriageEngine:
    """
    Downstream decision layer to assign priority levels based on V2 ML pipeline outputs.
    """

    def __init__(self):
        pass

    def evaluate(self, pipeline_output_df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies prototype priority logic to the outputs of the V2 inference pipeline.
        
        Args:
            pipeline_output_df: DataFrame output from MedhaV2Pipeline.predict_v2()
            
        Returns:
            DataFrame containing the original features + priority assignments.
        """
        out_df = pipeline_output_df.copy()
        
        # Ensure we have the required ML output columns
        if "Fusion_DDS_Prediction" not in out_df.columns:
            raise ValueError("Missing 'Fusion_DDS_Prediction' in pipeline output.")
        
        # Compute Priority
        priorities = []
        rationales = []
        
        for idx, row in out_df.iterrows():
            dds = row.get("Fusion_DDS_Prediction")
            future_risk = row.get("Temporal_Risk_Score")
            
            p_level, rationale = self._determine_priority(dds, future_risk)
            priorities.append(p_level)
            rationales.append(rationale)
            
        # Map back to output contract
        out_df["Current_DDS"] = out_df["Fusion_DDS_Prediction"]
        out_df["Future_Risk_Probability"] = out_df["Temporal_Risk_Score"]
        out_df["Future_Risk_Prediction"] = out_df["Future_Escalation_Flag"]
        
        out_df["Priority_Level"] = priorities
        out_df["Priority_Rationale"] = rationales
        
        return out_df

    def _determine_priority(self, dds, future_escalation_risk):
        """
        Determine the clinical priority level (ENGINEERING PROTOTYPE).
        """
        if pd.isna(dds) and pd.isna(future_escalation_risk):
            return "UNKNOWN", "Missing both Current DDS and Future Risk"
            
        # Prototype Thresholds
        if (not pd.isna(dds) and dds >= 75.0) or (not pd.isna(future_escalation_risk) and future_escalation_risk >= 0.85):
            if not pd.isna(future_escalation_risk) and future_escalation_risk >= 0.85:
                return "CRITICAL", "Future Risk >= 0.85"
            else:
                return "CRITICAL", "Current DDS >= 75.0"
                
        elif (not pd.isna(dds) and dds >= 50.0) or (not pd.isna(future_escalation_risk) and future_escalation_risk >= 0.50):
            if not pd.isna(future_escalation_risk) and future_escalation_risk >= 0.50:
                return "HIGH", "Future Risk >= 0.50"
            else:
                return "HIGH", "Current DDS >= 50.0"
                
        elif (not pd.isna(dds) and dds >= 25.0) or (not pd.isna(future_escalation_risk) and future_escalation_risk >= 0.25):
            if not pd.isna(future_escalation_risk) and future_escalation_risk >= 0.25:
                return "MEDIUM", "Future Risk >= 0.25"
            else:
                return "MEDIUM", "Current DDS >= 25.0"
                
        else:
            reason_parts = []
            if not pd.isna(dds):
                reason_parts.append(f"DDS {dds:.2f} < 25.0")
            if not pd.isna(future_escalation_risk):
                reason_parts.append(f"Risk {future_escalation_risk:.2f} < 0.25")
            
            return "LOW", " and ".join(reason_parts)
