"""
MEDHA V2 Adapter
================

Thin integration adapter connecting chatbot MedhaState to the frozen
MEDHA V2 predictive pipeline (MedhaV2Pipeline.predict_v2()).

ABSOLUTE ARCHITECTURAL PRINCIPLES:
1. Zero modifications to frozen V2 models, weights, or prediction pipelines.
2. The adapter never recalculates or replaces V2 predictions (DDS, GRU, Fusion).
3. Missing information remains missing (np.nan). Never converts missing values into 0.0.
4. Voice unavailable -> Voice_Available = 0.0, voice feature values remain np.nan.
5. Candidate observations are strictly isolated and never fabricated into V2 features.
6. All column names, feature order, and availability flags strictly match V2 contract.
"""

from __future__ import annotations

import copy
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Add repo root to path to ensure engine imports cleanly
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from chatbot.state.medha_state import (
    MedhaState,
    STRUCTURED_FEATURES,
    STRUCTURED_CATEGORICAL_FEATURES,
    STRUCTURED_NUMERIC_FEATURES,
    TEXT_FEATURES,
    VOICE_FEATURES,
    BEHAVIOUR_FEATURES,
)

# Additional 6 features present in the GRU whitelist (57 total) that are not in
# the core 42 structured + 5 text + 5 voice + 10 behaviour sets:
GRU_ADDITIONAL_WHITELIST_FEATURES: Tuple[str, ...] = (
    "Baseline_Text_Distress",
    "Baseline_Voice_Distress",
    "Text_Distress_Deviation",
    "Voice_Distress_Deviation",
    "Text_Distress_Trend",
    "Voice_Distress_Trend",
)


# ===========================================================================
# PREDICTION RESULT WRAPPER
# ===========================================================================

@dataclass
class V2PredictionResult:
    """
    Chatbot-friendly wrapper for outputs returned by MedhaV2Pipeline.predict_v2().
    Preserves all authoritative outputs without modification or reinterpretation.
    """
    victim_id: str
    timepoint: int

    # Core V2 Outputs
    current_dds: float                          # Fusion_DDS_Prediction (0.0 to 100.0)
    future_risk: Optional[float]                # Temporal_Risk_Score (0.0 to 1.0) or None
    future_risk_available: bool                 # True if Temporal_Available == 1
    future_escalation_flag: Optional[int]       # 1 (High Risk) / 0 (Safe) / None if unavailable

    # Specialist Predictions
    struct_pred: float                          # Structured baseline prediction
    text_pred: Optional[float]                  # Text prediction or None if unavailable
    voice_pred: Optional[float]                 # Voice prediction or None if unavailable
    behav_pred: float                           # Behaviour prediction

    # Availability Flags
    struct_available: float                     # Hardcoded 1.0 in V2
    text_available: float                       # 1.0 or 0.0
    voice_available: float                      # 1.0 or 0.0
    behav_available: float                      # Hardcoded 1.0 in V2

    # Downstream Triage (Engineering Demonstration)
    priority_level: Optional[str] = None        # "CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    priority_rationale: Optional[str] = None

    # Raw Full DataFrame output from V2
    raw_dataframe: pd.DataFrame = field(default_factory=pd.DataFrame, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result to a clean dictionary."""
        return {
            "victim_id": self.victim_id,
            "timepoint": self.timepoint,
            "current_dds": self.current_dds,
            "future_risk": self.future_risk,
            "future_risk_available": self.future_risk_available,
            "future_escalation_flag": self.future_escalation_flag,
            "struct_pred": self.struct_pred,
            "text_pred": self.text_pred,
            "voice_pred": self.voice_pred,
            "behav_pred": self.behav_pred,
            "struct_available": self.struct_available,
            "text_available": self.text_available,
            "voice_available": self.voice_available,
            "behav_available": self.behav_available,
            "priority_level": self.priority_level,
            "priority_rationale": self.priority_rationale,
        }


# ===========================================================================
# MEDHA V2 ADAPTER
# ===========================================================================

class MedhaV2Adapter:
    """
    Adapter between chatbot MedhaState and the frozen MEDHA V2 pipeline.

    Responsibilities:
    1. Validates MedhaState suitability for inference.
    2. Constructs canonical longitudinal DataFrame matching predict_v2() contract.
    3. Strictly enforces missing-modality rules (missing audio -> Voice_Available=0.0,
       voice features = np.nan, never 0.0).
    4. Enforces candidate observation isolation (qualitative observations never
       fabricate V2 feature values).
    5. Calls existing MedhaV2Pipeline.predict_v2().
    6. Returns outputs wrapped in V2PredictionResult.
    """

    def __init__(
        self,
        pipeline: Optional[Any] = None,
        enable_triage: bool = True,
        engine_dir: Optional[str] = None,
    ):
        self._pipeline = pipeline
        self.enable_triage = enable_triage
        self.engine_dir = engine_dir or os.path.join(REPO_ROOT, "engine")
        self._triage_engine = None

    @property
    def pipeline(self) -> Any:
        """Lazily loads the frozen MedhaV2Pipeline if not injected."""
        if self._pipeline is None:
            from engine.v2.medha_v2_pipeline import MedhaV2Pipeline
            self._pipeline = MedhaV2Pipeline(engine_dir=self.engine_dir)
        return self._pipeline

    @property
    def triage_engine(self) -> Any:
        """Lazily loads the TriageEngine if enabled."""
        if self._triage_engine is None and self.enable_triage:
            from engine.v2.priority_triage import TriageEngine
            self._triage_engine = TriageEngine()
        return self._triage_engine

    def state_to_row(self, state: MedhaState) -> Dict[str, Any]:
        """
        Converts a single validated MedhaState into a single-observation dictionary
        matching the exact canonical V2 input schema.

        CRITICAL SAFEGUARDS:
        - Missing values are explicitly set to np.nan (never 0.0).
        - If voice is unavailable, Voice_Available = 0.0 and voice features = np.nan.
        - If text is unavailable, Text_Available = 0.0 and text features = np.nan.
        - Candidate observations (e.g. sleep = poor) are NEVER read or converted here.
        """
        if not isinstance(state, MedhaState):
            raise TypeError(f"Expected MedhaState, got {type(state).__name__}.")

        errors = state.validate()
        if errors:
            raise ValueError(f"Cannot adapt invalid MedhaState for V2 inference: {errors}")

        row: Dict[str, Any] = {
            "Victim_ID": state.victim_id,
            "Timepoint": state.timepoint,
        }

        # 1. Modality Availability Flags (Strictly 1.0 or 0.0)
        # In V2 Data Contract, Text_Available and Voice_Available are required as 1.0 or 0.0.
        text_avail = 1.0 if state.text_available == 1.0 else 0.0
        voice_avail = 1.0 if state.voice_available == 1.0 else 0.0
        row["Text_Available"] = text_avail
        row["Voice_Available"] = voice_avail

        # 2. Structured Features (42 features)
        # Missing values must remain np.nan so V2 preprocessor imputes them safely.
        for feat in STRUCTURED_FEATURES:
            val = state.structured_features.get(feat)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                row[feat] = np.nan
            else:
                row[feat] = val

        # 3. Text Features (5 features)
        # If text is not available, features must remain np.nan (never 0.0!).
        for feat in TEXT_FEATURES:
            if text_avail == 1.0:
                val = state.text_features.get(feat)
                row[feat] = np.nan if val is None or (isinstance(val, float) and math.isnan(val)) else float(val)
            else:
                row[feat] = np.nan

        # 4. Voice Features (5 features)
        # If voice is not available, features must remain np.nan (never 0.0!).
        for feat in VOICE_FEATURES:
            if voice_avail == 1.0:
                val = state.voice_features.get(feat)
                row[feat] = np.nan if val is None or (isinstance(val, float) and math.isnan(val)) else float(val)
            else:
                row[feat] = np.nan

        # 5. Behaviour Features (10 features)
        for feat in BEHAVIOUR_FEATURES:
            val = state.behaviour_features.get(feat)
            if val is None or (isinstance(val, float) and math.isnan(val)):
                row[feat] = np.nan
            else:
                row[feat] = float(val)

        # 6. Additional GRU Whitelist Features (6 features)
        # Any unobserved trend/baseline features remain np.nan for safe V2 GRU pre-fill (line 185).
        for feat in GRU_ADDITIONAL_WHITELIST_FEATURES:
            # Check if stored in state metadata, otherwise np.nan
            row[feat] = state.metadata.get(feat, np.nan)

        return row

    def build_input_dataframe(
        self,
        state: MedhaState,
        history_states: Optional[List[MedhaState]] = None,
        history_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Builds the complete longitudinal DataFrame for predict_v2().

        Parameters
        ----------
        state : MedhaState
            The current active session state.
        history_states : Optional[List[MedhaState]]
            Prior timepoint states for this victim (ordered chronologically).
        history_df : Optional[pd.DataFrame]
            Prior pre-constructed longitudinal DataFrame rows for this victim.

        Returns
        -------
        pd.DataFrame
            Longitudinal DataFrame sorted by Timepoint, containing all required
            V2 columns and availability flags.
        """
        rows: List[Dict[str, Any]] = []

        # Process historical states if provided
        if history_states:
            for h_state in history_states:
                if h_state.victim_id != state.victim_id:
                    raise ValueError(
                        f"History state victim_id mismatch: '{h_state.victim_id}' != '{state.victim_id}'."
                    )
                if h_state.timepoint >= state.timepoint:
                    raise ValueError(
                        f"History state timepoint ({h_state.timepoint}) must be < current timepoint ({state.timepoint})."
                    )
                rows.append(self.state_to_row(h_state))

        # Current state row
        rows.append(self.state_to_row(state))
        current_df = pd.DataFrame(rows)

        # Merge with history_df if provided
        if history_df is not None and not history_df.empty:
            # Ensure history_df belongs to the same victim
            if "Victim_ID" in history_df.columns:
                h_vids = set(history_df["Victim_ID"].unique())
                if h_vids != {state.victim_id}:
                    raise ValueError(f"history_df victim mismatch: {h_vids} vs '{state.victim_id}'.")

            combined_df = pd.concat([history_df, current_df], ignore_index=True)
        else:
            combined_df = current_df

        # Sort strictly by Timepoint as required by the GRU sequence windowing
        if "Timepoint" in combined_df.columns:
            combined_df = combined_df.sort_values("Timepoint").reset_index(drop=True)

        return combined_df

    def predict(
        self,
        state: MedhaState,
        history_states: Optional[List[MedhaState]] = None,
        history_df: Optional[pd.DataFrame] = None,
    ) -> V2PredictionResult:
        """
        Executes end-to-end V2 prediction for the given MedhaState.

        Parameters
        ----------
        state : MedhaState
            Current state to predict on.
        history_states : Optional[List[MedhaState]]
            Optional preceding historical MedhaState objects (for GRU history).
        history_df : Optional[pd.DataFrame]
            Optional preceding historical DataFrame (for GRU history).

        Returns
        -------
        V2PredictionResult
            Authoritative results preserved from MedhaV2Pipeline.predict_v2().
        """
        input_df = self.build_input_dataframe(
            state=state,
            history_states=history_states,
            history_df=history_df,
        )

        # 1. Call existing frozen MedhaV2Pipeline.predict_v2()
        out_df = self.pipeline.predict_v2(input_df)

        # 2. Optionally evaluate downstream Priority Triage
        final_df = out_df
        if self.enable_triage and self.triage_engine is not None:
            final_df = self.triage_engine.evaluate(out_df)

        # 3. Extract output for the target state (latest row matching state.timepoint)
        target_rows = final_df[
            (final_df["Victim_ID"] == state.victim_id) &
            (final_df["Timepoint"] == state.timepoint)
        ]

        if target_rows.empty:
            raise RuntimeError(
                f"Pipeline output missing target observation for Victim_ID='{state.victim_id}', Timepoint={state.timepoint}."
            )

        row = target_rows.iloc[-1]

        # Clean NaN helper
        def _get_clean(col: str) -> Optional[float]:
            val = row.get(col)
            if val is None or pd.isna(val):
                return None
            return float(val)

        def _get_int(col: str) -> Optional[int]:
            val = row.get(col)
            if val is None or pd.isna(val):
                return None
            return int(val)

        return V2PredictionResult(
            victim_id=state.victim_id,
            timepoint=state.timepoint,
            current_dds=float(row["Fusion_DDS_Prediction"]),
            future_risk=_get_clean("Temporal_Risk_Score"),
            future_risk_available=bool(row.get("Temporal_Available", 0) == 1),
            future_escalation_flag=_get_int("Future_Escalation_Flag"),
            struct_pred=float(row["Struct_Pred"]),
            text_pred=_get_clean("Text_Pred"),
            voice_pred=_get_clean("Voice_Pred"),
            behav_pred=float(row["Behav_Pred"]),
            struct_available=float(row.get("Struct_Available", 1.0)),
            text_available=float(row.get("Text_Available", 0.0)),
            voice_available=float(row.get("Voice_Available", 0.0)),
            behav_available=float(row.get("Behav_Available", 1.0)),
            priority_level=str(row["Priority_Level"]) if "Priority_Level" in row and pd.notna(row["Priority_Level"]) else None,
            priority_rationale=str(row["Priority_Rationale"]) if "Priority_Rationale" in row and pd.notna(row["Priority_Rationale"]) else None,
            raw_dataframe=final_df,
        )
