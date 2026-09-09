"""
MEDHA Text Engine Adapter
=========================

Thin integration adapter connecting chatbot text input to the existing
frozen MEDHA Text Engine (engine/text engine/medha_text_engine.py).

ABSOLUTE ARCHITECTURAL PRINCIPLES:
1. Zero modifications to the existing fine-tuned MuRIL model, tokenizer, or logic.
2. Uses the standardized medha_text_engine(request: dict) -> dict interface.
3. Maps outputs to the exact 5 canonical V2 text features:
   - Text_Distress  (from text_distress)
   - Fear           (from fear_signal)
   - Threat_Context (from threat_context)
   - Negative_Affect(from negative_affect)
   - Urgency        (from urgency)
4. Preserves continuous probabilities (0.0 to 1.0) without binarization or thresholding.
5. Updates Text_Available correctly (1.0 when analyzed, 0.0 when missing/empty).
6. Preserves missingness semantics: when text is absent or empty, features remain None (never 0.0).
7. Passes source="chatbot" metadata.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Environment safety: disable optional vision/audio C-extensions before transformers loads
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"
if "torchvision" not in sys.modules:
    sys.modules["torchvision"] = None
if "torchaudio" not in sys.modules:
    sys.modules["torchaudio"] = None

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEXT_ENGINE_DIR = REPO_ROOT / "engine" / "text engine"

from chatbot.state.medha_state import MedhaState, TEXT_FEATURES

# Authoritative mapping from medha_text_engine output keys to canonical V2 feature names
VECTOR_KEY_TO_V2_FEATURE: Dict[str, str] = {
    "text_distress": "Text_Distress",
    "fear_signal": "Fear",
    "threat_context": "Threat_Context",
    "negative_affect": "Negative_Affect",
    "urgency": "Urgency",
}


@dataclass
class TextEngineResult:
    """
    Standardized result from the existing MEDHA Text Engine.
    Preserves continuous model probabilities and canonical V2 feature keys.
    """
    text_available: float                       # 1.0 if successfully analyzed, 0.0 if missing/empty/failed
    features: Dict[str, Optional[float]]        # Canonical V2 features (Text_Distress, Fear, Threat_Context, Negative_Affect, Urgency)
    raw_vector: Optional[Dict[str, float]] = None # Direct text_vector from medha_text_engine
    source: str = "chatbot"
    language: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_available": self.text_available,
            "features": dict(self.features),
            "raw_vector": dict(self.raw_vector) if self.raw_vector else None,
            "source": self.source,
            "language": self.language,
            "error_message": self.error_message,
        }


class MedhaTextAdapter:
    """
    Adapter interfacing the chatbot with the existing MEDHA Text Engine.
    """

    def __init__(
        self,
        engine_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        raise_on_error: bool = False,
    ):
        """
        Parameters
        ----------
        engine_fn : Optional[Callable]
            Custom inference callable matching medha_text_engine(request).
            If None, lazily imports the canonical function from engine/text engine/.
        raise_on_error : bool
            If True, unexpected inference errors raise exceptions.
            If False, falls back safely to text_available=0.0 and records error.
        """
        self._engine_fn = engine_fn
        self.raise_on_error = raise_on_error

    @property
    def engine_fn(self) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Lazily imports medha_text_engine from the existing module."""
        if self._engine_fn is None:
            text_engine_str = str(TEXT_ENGINE_DIR.resolve())
            if text_engine_str not in sys.path:
                sys.path.insert(0, text_engine_str)

            try:
                from medha_text_engine import medha_text_engine
                self._engine_fn = medha_text_engine
            except Exception as e:
                raise ImportError(
                    f"Could not import existing MEDHA Text Engine from {TEXT_ENGINE_DIR}: {e}"
                ) from e
        return self._engine_fn

    def analyze_text(
        self,
        text: Optional[str],
        victim_id: str = "anonymous",
        session_id: str = "sess_0",
        language: Optional[str] = None,
        source: str = "chatbot",
    ) -> TextEngineResult:
        """
        Processes conversational text using the existing MEDHA Text Engine.

        Parameters
        ----------
        text : Optional[str]
            User conversational message.
        victim_id : str
            Victim identifier for audit metadata pass-through.
        session_id : str
            Session identifier for audit metadata pass-through.
        language : Optional[str]
            Optional language hint ('en', 'hi', 'hinglish').
        source : str
            Source metadata tag (defaults to 'chatbot').

        Returns
        -------
        TextEngineResult
            Validated result containing continuous probabilities for the 5 V2 text features.
        """
        # Handle empty, whitespace-only, or None text
        if text is None or not str(text).strip():
            return TextEngineResult(
                text_available=0.0,
                features={feat: None for feat in TEXT_FEATURES},
                raw_vector=None,
                source=source,
                language=language,
                error_message=None,
            )

        clean_text = str(text).strip()

        # Build standardized JSON request matching existing Text Engine contract
        request: Dict[str, Any] = {
            "victim_id": victim_id,
            "session_id": session_id,
            "text": clean_text,
            "source": source,
        }
        if language:
            request["language"] = language

        try:
            # Invoke the existing Text Engine
            response = self.engine_fn(request)

            raw_vector = response.get("text_vector", {})
            features: Dict[str, Optional[float]] = {}

            # Map the 5 output probabilities to canonical V2 feature names
            for vec_key, v2_name in VECTOR_KEY_TO_V2_FEATURE.items():
                val = raw_vector.get(vec_key)
                if val is None:
                    raise KeyError(
                        f"Existing Text Engine response missing expected feature key '{vec_key}'."
                    )
                float_val = float(val)

                # Validate probability range [0.0, 1.0] without changing or binarizing it
                if not (0.0 <= float_val <= 1.0):
                    raise ValueError(
                        f"Text probability for '{v2_name}' out of bounds: {float_val}"
                    )

                features[v2_name] = float_val

            return TextEngineResult(
                text_available=1.0,
                features=features,
                raw_vector=raw_vector,
                source=response.get("source", source),
                language=response.get("language", language),
                error_message=None,
            )

        except Exception as e:
            if self.raise_on_error:
                raise
            return TextEngineResult(
                text_available=0.0,
                features={feat: None for feat in TEXT_FEATURES},
                raw_vector=None,
                source=source,
                language=language,
                error_message=str(e),
            )

    def process_and_update_state(
        self,
        state: MedhaState,
        text: Optional[str],
        language: Optional[str] = None,
        source: str = "chatbot",
    ) -> TextEngineResult:
        """
        Analyzes user text and updates MedhaState with the resulting 5 text features
        and Text_Available flag.

        Preserves missing-data semantics: if text is empty/missing, state text features
        remain None and Text_Available is set to 0.0.
        """
        if not isinstance(state, MedhaState):
            raise TypeError(f"Expected MedhaState, got {type(state).__name__}.")

        result = self.analyze_text(
            text=text,
            victim_id=state.victim_id,
            session_id=state.session_id,
            language=language,
            source=source,
        )

        if result.text_available == 1.0:
            # Update all 5 canonical text features atomically in state
            state.update_features_batch("text", result.features)
            state.set_modality_availability("text", 1.0)
        else:
            # Missing text: availability is 0.0, features remain None (missing)
            for feat in TEXT_FEATURES:
                state.text_features[feat] = None
            state.set_modality_availability("text", 0.0)

        return result
