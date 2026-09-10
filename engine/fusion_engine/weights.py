"""
MEDHA Fusion Engine — Initial Experimental Weights
====================================================

Single source of truth for modality weights used by the weighted
fusion formula.

These are INITIAL EXPERIMENTAL weights.  They are NOT clinically
validated and NOT optimised.  After the baseline implementation is
verified, a weight-selection experiment on validation data should
determine better values (see §15 of the fusion specification).

To change weights, edit ONLY this file.
"""

FUSION_WEIGHTS = {
    "text":       0.25,
    "voice":      0.15,
    "behaviour":  0.15,
    "structured": 0.25,
    "temporal":   0.20,
}

# Sanity check at import time
_total = sum(FUSION_WEIGHTS.values())
assert abs(_total - 1.0) < 1e-9, (
    f"FUSION_WEIGHTS must sum to 1.0, got {_total}"
)
