"""
MEDHA Behaviour Engine Adapter
==============================

Thin integration adapter connecting authoritative behaviour input to the
existing frozen MEDHA V2 predictive pipeline.

ABSOLUTE ARCHITECTURAL PRINCIPLES:
1. DOES NOT invoke the Behaviour ML model directly. Inference is owned natively
   by `MedhaV2Pipeline.predict_v2()`.
2. Validates incoming authoritative raw metric data against `MedhaState.BEHAVIOUR_FEATURES`.
3. Populates `MedhaState.behaviour_features` and updates availability.
4. Leaves missing features as `None`. Never fabricates 0.0 values.
5. Does not convert conversational LLM extractions into numerical features.
"""

from typing import Dict, Any

from chatbot.state.medha_state import MedhaState, BEHAVIOUR_FEATURES
from chatbot.interfaces import BehaviourAdapterProtocol


class MedhaBehaviourAdapter(BehaviourAdapterProtocol):
    """
    Validates authoritative behaviour input against the MEDHA V2 behaviour schema.
    Updates state.behaviour_features if valid, preserving missing values for absent data.
    Does NOT invoke the Behaviour ML model directly, as that is handled natively 
    by MedhaV2Pipeline.predict_v2().
    """

    def process_and_update_state(
        self,
        state: MedhaState,
        behaviour_data: Dict[str, Any],
    ) -> None:
        if not behaviour_data:
            self._set_unavailable(state)
            return

        has_valid_data = False

        for feature in BEHAVIOUR_FEATURES:
            if feature in behaviour_data and behaviour_data[feature] is not None:
                try:
                    val = float(behaviour_data[feature])
                    state.behaviour_features[feature] = val
                    has_valid_data = True
                except (ValueError, TypeError):
                    state.behaviour_features[feature] = None
            else:
                state.behaviour_features[feature] = None

        state.set_modality_availability("behaviour", 1.0 if has_valid_data else 0.0)

    def _set_unavailable(self, state: MedhaState) -> None:
        """Sets all behaviour features to None and marks modality as unavailable."""
        for feat in BEHAVIOUR_FEATURES:
            state.behaviour_features[feat] = None
        state.set_modality_availability("behaviour", 0.0)
