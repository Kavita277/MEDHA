"""
MEDHA V2 Fusion Engine
======================

Core fusion logic for combining four DDS specialist predictions
(Structured, Text, Voice, Behaviour) into a single fused DDS score.

Architecture follows Step 10A Fusion Audit:
 - 4 modalities (no GRU/Temporal)
 - DDS-scale inputs (0-100)
 - Missing-modality proportional weight redistribution
 - Three candidate architectures: Weighted Average, Ridge, XGBoost

V1 Fusion Engine is NOT modified. This is a clean V2 implementation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
import numpy as np

# ====================================================================
# FUSION INPUT CONTRACT
# ====================================================================

# Approved fusion features (from Step 10A)
V2_FUSION_APPROVED_FEATURES = [
    "Struct_Pred",
    "Text_Pred",
    "Voice_Pred",
    "Behav_Pred",
]

V2_FUSION_AVAILABILITY_FLAGS = [
    "Struct_Available",
    "Text_Available",
    "Voice_Available",
    "Behav_Available",
]

V2_FUSION_IDENTITY_COLS = [
    "Victim_ID",
    "Timepoint",
]

# FORBIDDEN features -- must NEVER enter the fusion feature matrix
V2_FUSION_FORBIDDEN_FEATURES = [
    "Actual_DDS",
    "DDS",
    "Future_Escalation_Label",
    "Previous_DDS",
    "Rolling_DDS_Mean",
    "Rolling_DDS_SD",
    "DDS_Slope",
    "Recent_Change_Rate",
    "Recent_Max_DDS",
    "Recent_Min_DDS",
    "Delta_DDS",
    "DDS_Deviation_From_Baseline",
    "Baseline_DDS",
    "Trajectory_State",
    "Discordance_Test_Feature",
    "Discordance_Example_Flag",
    "Intervention",
    "Follow_Up",
]


def validate_fusion_features(feature_columns: list) -> None:
    """
    Hard-fail if any forbidden or unknown feature is present in
    the fusion feature matrix.

    Parameters
    ----------
    feature_columns : list
        The feature column names that will enter the fusion model.

    Raises
    ------
    ValueError
        If any forbidden or unknown feature is found.
    """
    all_approved = set(V2_FUSION_APPROVED_FEATURES + V2_FUSION_AVAILABILITY_FLAGS)

    for col in feature_columns:
        # Check forbidden
        if col in V2_FUSION_FORBIDDEN_FEATURES:
            raise ValueError(
                f"FORBIDDEN feature '{col}' found in fusion feature matrix. "
                f"This feature must NEVER enter the fusion model."
            )

        # Check unknown
        if col not in all_approved:
            raise ValueError(
                f"UNKNOWN feature '{col}' found in fusion feature matrix. "
                f"Only approved features are allowed: {sorted(all_approved)}"
            )


# ====================================================================
# DATA SCHEMAS
# ====================================================================

@dataclass
class ModalitySignal:
    """One specialist's DDS prediction for fusion."""
    available: bool
    dds: Optional[float] = None  # 0-100 when available, None when not


@dataclass
class V2FusionInput:
    """
    Everything the V2 fusion engine needs for one observation.

    Fields
    ------
    victim_id : str
    timepoint : int
    structured, text, voice, behaviour : ModalitySignal
        Each carries an ``available`` flag and a ``dds`` prediction value.
    """
    victim_id: str
    timepoint: int

    structured: ModalitySignal = field(
        default_factory=lambda: ModalitySignal(available=True)
    )
    text: ModalitySignal = field(
        default_factory=lambda: ModalitySignal(available=False)
    )
    voice: ModalitySignal = field(
        default_factory=lambda: ModalitySignal(available=False)
    )
    behaviour: ModalitySignal = field(
        default_factory=lambda: ModalitySignal(available=True)
    )


@dataclass
class V2FusionOutput:
    """
    Complete V2 fusion result for one observation.

    Fields
    ------
    victim_id, timepoint : identity
    fusion_available : bool
        False only when every modality is unavailable.
    specialist_predictions : dict
        Per-modality DDS predictions actually used.
    availability : dict
        Per-modality availability flags (1/0).
    effective_weights : dict
        Weights after redistribution for missing modalities.
    fused_dds : float or None
        Weighted DDS prediction (0-100).
    """
    victim_id: str
    timepoint: int
    fusion_available: bool
    specialist_predictions: Dict[str, Optional[float]]
    availability: Dict[str, int]
    effective_weights: Dict[str, float]
    fused_dds: Optional[float]

    def to_dict(self) -> dict:
        """Serialise to a plain dict (JSON-safe)."""
        return {
            "victim_id": self.victim_id,
            "timepoint": self.timepoint,
            "fusion_available": self.fusion_available,
            "specialist_predictions": self.specialist_predictions,
            "availability": self.availability,
            "effective_weights": self.effective_weights,
            "fused_dds": self.fused_dds,
        }


# ====================================================================
# MODALITY KEYS
# ====================================================================

_MODALITY_KEYS = ["structured", "text", "voice", "behaviour"]


# ====================================================================
# CANDIDATE A: WEIGHTED AVERAGE FUSION
# ====================================================================

def compute_weighted_average_fusion(
    fusion_input: V2FusionInput,
    weights: Dict[str, float],
) -> V2FusionOutput:
    """
    Candidate A: Fixed-weight linear combination of specialist DDS predictions.

    Missing modalities have their weight redistributed proportionally
    among available modalities.

    Parameters
    ----------
    fusion_input : V2FusionInput
    weights : dict
        Base weights for each modality, must sum to ~1.0.

    Returns
    -------
    V2FusionOutput
    """
    signals: Dict[str, ModalitySignal] = {
        "structured": fusion_input.structured,
        "text":       fusion_input.text,
        "voice":      fusion_input.voice,
        "behaviour":  fusion_input.behaviour,
    }

    availability = {
        key: int(sig.available) for key, sig in signals.items()
    }

    specialist_predictions = {
        key: sig.dds if sig.available else None
        for key, sig in signals.items()
    }

    # Available modalities
    available_keys = [
        key for key in _MODALITY_KEYS
        if signals[key].available and signals[key].dds is not None
    ]

    # Edge case: nothing available
    if not available_keys:
        return V2FusionOutput(
            victim_id=fusion_input.victim_id,
            timepoint=fusion_input.timepoint,
            fusion_available=False,
            specialist_predictions=specialist_predictions,
            availability=availability,
            effective_weights={key: 0.0 for key in _MODALITY_KEYS},
            fused_dds=None,
        )

    # Renormalise weights for available modalities
    raw_weight_sum = sum(weights[key] for key in available_keys)
    effective_weights = {}
    for key in _MODALITY_KEYS:
        if key in available_keys:
            effective_weights[key] = weights[key] / raw_weight_sum
        else:
            effective_weights[key] = 0.0

    # Weighted sum
    fused_dds = sum(
        effective_weights[key] * signals[key].dds
        for key in available_keys
    )

    # Clamp to [0, 100]
    fused_dds = max(0.0, min(100.0, fused_dds))

    return V2FusionOutput(
        victim_id=fusion_input.victim_id,
        timepoint=fusion_input.timepoint,
        fusion_available=True,
        specialist_predictions=specialist_predictions,
        availability=availability,
        effective_weights={
            key: round(w, 6) for key, w in effective_weights.items()
        },
        fused_dds=round(fused_dds, 4),
    )


# ====================================================================
# CANDIDATE B/C: LEARNED FUSION (RIDGE / XGBOOST)
# ====================================================================

def prepare_fusion_features(
    fusion_input: V2FusionInput,
) -> Dict[str, float]:
    """
    Convert a V2FusionInput into the feature dict for a learned model.

    Missing modality predictions are set to 0.0 with a binary
    availability flag = 0.

    Returns
    -------
    dict
        Keys: Struct_Pred, Text_Pred, Voice_Pred, Behav_Pred,
              Struct_Available, Text_Available, Voice_Available, Behav_Available
    """
    signals = {
        "Struct": fusion_input.structured,
        "Text":   fusion_input.text,
        "Voice":  fusion_input.voice,
        "Behav":  fusion_input.behaviour,
    }

    features = {}
    for prefix, sig in signals.items():
        features[f"{prefix}_Pred"] = sig.dds if (sig.available and sig.dds is not None) else 0.0
        features[f"{prefix}_Available"] = 1.0 if sig.available else 0.0

    return features


def compute_learned_fusion(
    fusion_input: V2FusionInput,
    model,
    feature_order: List[str],
) -> V2FusionOutput:
    """
    Candidate B/C: Learned fusion using a trained sklearn model.

    Parameters
    ----------
    fusion_input : V2FusionInput
    model : sklearn estimator with .predict()
    feature_order : list
        Ordered feature names matching the model's training schema.

    Returns
    -------
    V2FusionOutput
    """
    signals: Dict[str, ModalitySignal] = {
        "structured": fusion_input.structured,
        "text":       fusion_input.text,
        "voice":      fusion_input.voice,
        "behaviour":  fusion_input.behaviour,
    }

    availability = {
        key: int(sig.available) for key, sig in signals.items()
    }

    specialist_predictions = {
        key: sig.dds if sig.available else None
        for key, sig in signals.items()
    }

    available_keys = [
        key for key in _MODALITY_KEYS
        if signals[key].available and signals[key].dds is not None
    ]

    # Edge case: nothing available
    if not available_keys:
        return V2FusionOutput(
            victim_id=fusion_input.victim_id,
            timepoint=fusion_input.timepoint,
            fusion_available=False,
            specialist_predictions=specialist_predictions,
            availability=availability,
            effective_weights={key: 0.0 for key in _MODALITY_KEYS},
            fused_dds=None,
        )

    # Build feature vector
    feat_dict = prepare_fusion_features(fusion_input)
    X = np.array([[feat_dict[f] for f in feature_order]])

    # Predict
    fused_dds = float(model.predict(X)[0])

    # Clamp to [0, 100]
    fused_dds = max(0.0, min(100.0, fused_dds))

    return V2FusionOutput(
        victim_id=fusion_input.victim_id,
        timepoint=fusion_input.timepoint,
        fusion_available=True,
        specialist_predictions=specialist_predictions,
        availability=availability,
        effective_weights={key: 0.0 for key in _MODALITY_KEYS},  # learned model doesn't expose per-modality weights cleanly
        fused_dds=round(fused_dds, 4),
    )
