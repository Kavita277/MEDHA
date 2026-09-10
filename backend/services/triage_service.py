"""
Triage Service
==============

Centralized, single-source triage level computation for MEDHA.

IMPORTANT: This is the ONLY place triage thresholds are defined.
  - Do NOT duplicate these thresholds in API handlers, schemas, or tests.
  - Thresholds match the frozen V2 architecture document exactly.
  - These thresholds are an engineering demonstration only and are NOT
    clinically validated.

Triage Logic (from MEDHA_V2_ARCHITECTURE.md §6):

  CRITICAL: DDS >= 75 OR Future Risk >= 0.85
  HIGH:     DDS >= 50 OR Future Risk >= 0.50
  MEDIUM:   DDS >= 25 OR Future Risk >= 0.25
  LOW:      DDS <  25 AND Future Risk < 0.25
  UNKNOWN:  Both DDS and Future Risk are unavailable (None)

If only one signal is available, thresholds for that signal are applied
and the other is ignored in the OR logic.
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Canonical threshold constants (single source of truth)
# ---------------------------------------------------------------------------
_DDS_CRITICAL = 75.0
_DDS_HIGH = 50.0
_DDS_MEDIUM = 25.0
_RISK_CRITICAL = 0.85
_RISK_HIGH = 0.50
_RISK_MEDIUM = 0.25

TRIAGE_LEVEL_UNKNOWN = "UNKNOWN"
TRIAGE_LEVEL_CRITICAL = "CRITICAL"
TRIAGE_LEVEL_HIGH = "HIGH"
TRIAGE_LEVEL_MEDIUM = "MEDIUM"
TRIAGE_LEVEL_LOW = "LOW"

ALL_TRIAGE_LEVELS = (
    TRIAGE_LEVEL_CRITICAL,
    TRIAGE_LEVEL_HIGH,
    TRIAGE_LEVEL_MEDIUM,
    TRIAGE_LEVEL_LOW,
    TRIAGE_LEVEL_UNKNOWN,
)


def compute_triage_level(
    fusion_dds: Optional[float],
    temporal_risk: Optional[float],
) -> str:
    """
    Computes the triage level from the MEDHA V2 core outputs.

    Parameters
    ----------
    fusion_dds:
        Fusion_DDS_Prediction (0.0 – 100.0). Pass None if unavailable.
    temporal_risk:
        Temporal_Risk_Score (0.0 – 1.0). Pass None if unavailable (<7 timesteps).

    Returns
    -------
    str
        One of: "CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN".
        "UNKNOWN" is returned only when BOTH signals are None.
    """
    # Both unavailable → UNKNOWN
    if fusion_dds is None and temporal_risk is None:
        return TRIAGE_LEVEL_UNKNOWN

    # Helper: True if the DDS threshold is met (handles None gracefully)
    def _dds_gte(threshold: float) -> bool:
        return fusion_dds is not None and fusion_dds >= threshold

    # Helper: True if the risk threshold is met (handles None gracefully)
    def _risk_gte(threshold: float) -> bool:
        return temporal_risk is not None and temporal_risk >= threshold

    if _dds_gte(_DDS_CRITICAL) or _risk_gte(_RISK_CRITICAL):
        return TRIAGE_LEVEL_CRITICAL

    if _dds_gte(_DDS_HIGH) or _risk_gte(_RISK_HIGH):
        return TRIAGE_LEVEL_HIGH

    if _dds_gte(_DDS_MEDIUM) or _risk_gte(_RISK_MEDIUM):
        return TRIAGE_LEVEL_MEDIUM

    # Both available and both below the MEDIUM threshold → LOW
    return TRIAGE_LEVEL_LOW
