"""
Unit and Integration Tests for MEDHA LLM Layer (Step 5)
=======================================================

Verifies:
1. MockLLMProvider conforms to LLMProviderProtocol
2. Natural conversational response generation
3. Semantic observation extraction from user messages
4. Controlled observation domain validation
5. Evidence requirement enforcement
6. No V2 numeric feature fabrication
7. Confidence semantics (evidence confidence, NOT risk probability)
8. Conversation context handling
9. GeminiProvider instantiation and configuration
10. ConversationManager integration with LLM observation flow
11. Observations stored in MedhaState.candidate_observations
12. Provider independence (no Gemini coupling in ConversationManager)
"""

import os
import pytest
from typing import Any, Dict, List, Optional
from unittest.mock import patch, MagicMock

from chatbot.interfaces import LLMProviderProtocol, LLMResponse
from chatbot.state.medha_state import MedhaState, QuestionRecord
from chatbot.llm.mock_provider import MockLLMProvider
from chatbot.llm.gemini_provider import (
    GeminiProvider,
    _extract_json_from_text,
    _parse_observations,
)
from chatbot.llm.observation_schema import (
    CANDIDATE_OBSERVATION_DOMAINS,
    validate_observation_domain,
    validate_semantic_value,
    ALLOWED_SEMANTIC_VALUES,
)
from chatbot.llm.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from chatbot.conversation_manager import ConversationManager


# ===========================================================================
# HELPER: MockTextAdapter for fast ConversationManager tests
# ===========================================================================

class MockTextAdapter:
    def process_and_update_state(self, state, text=None, language=None, source="chatbot"):
        from chatbot.engines.text_adapter import TextEngineResult
        from chatbot.state.medha_state import TEXT_FEATURES
        if text and text.strip():
            feats = {f: 0.5 for f in TEXT_FEATURES}
            state.update_features_batch("text", feats)
            state.set_modality_availability("text", 1.0)
            return TextEngineResult(text_available=1.0, features=feats, source=source)
        for f in TEXT_FEATURES:
            state.text_features[f] = None
        state.set_modality_availability("text", 0.0)
        return TextEngineResult(
            text_available=0.0,
            features={f: None for f in TEXT_FEATURES},
            source=source,
        )


# ===========================================================================
# 1. PROTOCOL CONFORMANCE
# ===========================================================================

def test_mock_provider_conforms_to_protocol():
    """MockLLMProvider must satisfy LLMProviderProtocol."""
    provider = MockLLMProvider()
    assert isinstance(provider, LLMProviderProtocol)

    state = MedhaState(victim_id="VIC_PROTO", timepoint=1)
    result = provider.generate_response(message="hello", state=state)
    assert isinstance(result, LLMResponse)
    assert isinstance(result.text, str)
    assert isinstance(result.candidate_observations, list)
    assert isinstance(result.metadata, dict)


# ===========================================================================
# 2. NATURAL CONVERSATIONAL RESPONSE
# ===========================================================================

def test_natural_conversational_response():
    """Response must be natural, non-empty, and not a questionnaire."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_NAT", timepoint=1)

    result = provider.generate_response(
        message="I've been feeling overwhelmed lately.",
        state=state,
    )

    assert len(result.text) > 10
    # Response should NOT contain numeric ratings or clinical terms
    assert "rate" not in result.text.lower() or "appreciate" in result.text.lower()
    assert "DDS" not in result.text
    assert "risk score" not in result.text.lower()
    assert "diagnosis" not in result.text.lower()

    # Should be empathetic
    assert result.metadata.get("provider") == "mock"


# ===========================================================================
# 3. SEMANTIC OBSERVATION EXTRACTION
# ===========================================================================

def test_observation_extraction_sleep():
    """User mentioning sleep problems should extract a sleep observation."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_OBS", timepoint=1)

    result = provider.generate_response(
        message="I can't sleep at night, I keep hearing noises outside.",
        state=state,
    )

    assert len(result.candidate_observations) >= 1
    sleep_obs = [o for o in result.candidate_observations if o["domain"] == "sleep"]
    assert len(sleep_obs) == 1
    assert sleep_obs[0]["value"] == "poor"
    assert sleep_obs[0]["evidence"]  # must have evidence
    assert sleep_obs[0].get("source") == "llm_mock"


def test_observation_extraction_fear():
    """User expressing fear should extract a fear observation."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_FEAR", timepoint=1)

    result = provider.generate_response(
        message="I feel scared every time the doorbell rings.",
        state=state,
    )

    fear_obs = [o for o in result.candidate_observations if o["domain"] == "fear"]
    assert len(fear_obs) == 1
    assert fear_obs[0]["value"] == "present"


def test_observation_extraction_multiple():
    """User message covering multiple domains should extract multiple observations."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_MULTI", timepoint=1)

    result = provider.generate_response(
        message="I'm so stressed and scared, I can't sleep at all.",
        state=state,
    )

    domains = {o["domain"] for o in result.candidate_observations}
    assert "stress" in domains
    assert "fear" in domains
    assert "sleep" in domains


def test_no_observation_on_neutral_message():
    """Neutral greetings should not produce observations."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_NEUTRAL", timepoint=1)

    result = provider.generate_response(
        message="Hello, how are you?",
        state=state,
    )

    assert len(result.candidate_observations) == 0


# ===========================================================================
# 4. CONTROLLED OBSERVATION DOMAIN VALIDATION
# ===========================================================================

def test_observation_domains_are_controlled():
    """All domains must be from the controlled vocabulary."""
    assert "sleep" in CANDIDATE_OBSERVATION_DOMAINS
    assert "mood" in CANDIDATE_OBSERVATION_DOMAINS
    assert "fear" in CANDIDATE_OBSERVATION_DOMAINS
    assert "safety" in CANDIDATE_OBSERVATION_DOMAINS
    assert "stress" in CANDIDATE_OBSERVATION_DOMAINS
    assert "social_support" in CANDIDATE_OBSERVATION_DOMAINS
    assert "urgency" in CANDIDATE_OBSERVATION_DOMAINS
    assert "distress" in CANDIDATE_OBSERVATION_DOMAINS

    # Invalid domains must be rejected
    assert not validate_observation_domain("suicide_risk")
    assert not validate_observation_domain("DDS")
    assert not validate_observation_domain("fusion_score")
    assert not validate_observation_domain("arbitrary_domain_123")


# ===========================================================================
# 5. EVIDENCE REQUIREMENT
# ===========================================================================

def test_evidence_requirement():
    """Observations without evidence must be dropped."""
    raw = [
        {"domain": "sleep", "value": "poor", "evidence": "I can't sleep"},
        {"domain": "mood", "value": "low", "evidence": ""},  # empty evidence
        {"domain": "stress", "value": "high", "evidence": None},  # missing evidence
        {"domain": "fear", "value": "present"},  # no evidence key at all
    ]

    validated = _parse_observations(raw)
    assert len(validated) == 1
    assert validated[0]["domain"] == "sleep"
    assert validated[0]["evidence"] == "I can't sleep"


# ===========================================================================
# 6. NO V2 NUMERIC FEATURE FABRICATION
# ===========================================================================

def test_no_v2_numeric_fabrication():
    """
    LLM observations must be candidate semantics, not V2 numeric features.
    The mock provider must never output V2 feature names as observation values.
    """
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_NO_V2", timepoint=1)

    result = provider.generate_response(
        message="I haven't slept in days and I'm really stressed.",
        state=state,
    )

    for obs in result.candidate_observations:
        # Observations must be semantic, NOT numeric V2 values
        assert not isinstance(obs["value"], (int, float)), \
            f"Observation value must not be numeric: {obs}"
        # Must NOT contain V2 column names as domain
        assert obs["domain"] not in {"Sleep", "Stress", "Mood", "Functioning"}, \
            f"Domain must not be a raw V2 column name: {obs['domain']}"


# ===========================================================================
# 7. CONFIDENCE SEMANTICS
# ===========================================================================

def test_confidence_is_evidence_confidence():
    """Confidence must represent evidence clarity, NOT clinical risk probability."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_CONF", timepoint=1)

    result = provider.generate_response(
        message="I can't sleep at all lately.",
        state=state,
    )

    for obs in result.candidate_observations:
        if obs.get("confidence") is not None:
            # Must be in [0, 1]
            assert 0.0 <= obs["confidence"] <= 1.0
            # Should be moderate-to-high for clear statements
            # (NOT a clinical risk probability)


def test_confidence_clamping():
    """Confidence values outside [0, 1] must be clamped."""
    raw = [
        {"domain": "sleep", "value": "poor", "evidence": "cant sleep", "confidence": 1.5},
        {"domain": "mood", "value": "low", "evidence": "feeling down", "confidence": -0.3},
    ]
    validated = _parse_observations(raw)
    assert validated[0]["confidence"] == 1.0
    assert validated[1]["confidence"] == 0.0


# ===========================================================================
# 8. CONVERSATION CONTEXT HANDLING
# ===========================================================================

def test_conversation_context_in_prompt():
    """User prompt builder should include recent conversation history."""
    history = [
        {"role": "user", "content": "I need help."},
        {"role": "assistant", "content": "I'm here for you."},
        {"role": "user", "content": "Things are getting worse."},
    ]

    prompt = build_user_prompt(
        message="I feel scared now.",
        conversation_history=history,
        max_history_turns=4,
    )

    assert "I need help" in prompt
    assert "I'm here for you" in prompt
    assert "I feel scared now" in prompt


def test_prompt_without_history():
    """Prompt should work without conversation history."""
    prompt = build_user_prompt(message="Hello there.", conversation_history=None)
    assert "Hello there." in prompt


# ===========================================================================
# 9. GEMINI PROVIDER CONFIGURATION
# ===========================================================================

def test_gemini_provider_configuration():
    """GeminiProvider must accept configuration without making API calls."""
    provider = GeminiProvider(
        api_key="test-key-not-real",
        model_name="gemini-2.5-flash",
        max_history_turns=4,
        temperature=0.5,
    )

    assert provider._api_key == "test-key-not-real"
    assert provider._model_name == "gemini-2.5-flash"
    assert provider._max_history_turns == 4
    assert provider._temperature == 0.5
    assert provider._client is None  # Lazy init: no API call yet


def test_gemini_provider_env_fallback():
    """GeminiProvider should fall back to environment variables."""
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "env-api-key",
        "MEDHA_LLM_MODEL": "gemini-2.0-flash-lite",
    }):
        provider = GeminiProvider()
        assert provider._api_key == "env-api-key"
        assert provider._model_name == "gemini-2.0-flash-lite"


def test_gemini_provider_missing_key():
    """GeminiProvider must raise ValueError when no API key is available."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove all possible key sources
        env_backup = {}
        for key in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)

        try:
            provider = GeminiProvider(api_key=None)
            with pytest.raises(ValueError, match="API key not configured"):
                _ = provider.client
        finally:
            os.environ.update(env_backup)


def test_gemini_conforms_to_protocol():
    """GeminiProvider must satisfy LLMProviderProtocol."""
    provider = GeminiProvider(api_key="test-key")
    assert isinstance(provider, LLMProviderProtocol)


# ===========================================================================
# 10. JSON PARSING ROBUSTNESS
# ===========================================================================

def test_json_extraction_clean():
    """Clean JSON should parse correctly."""
    text = '{"response_text": "I hear you.", "observations": []}'
    parsed = _extract_json_from_text(text)
    assert parsed["response_text"] == "I hear you."
    assert parsed["observations"] == []


def test_json_extraction_markdown_fences():
    """JSON wrapped in markdown fences should parse correctly."""
    text = '```json\n{"response_text": "hello", "observations": []}\n```'
    parsed = _extract_json_from_text(text)
    assert parsed["response_text"] == "hello"


def test_json_extraction_with_preamble():
    """JSON with surrounding text should be extracted."""
    text = 'Here is my response:\n{"response_text": "test", "observations": []}\nDone.'
    parsed = _extract_json_from_text(text)
    assert parsed is not None
    assert parsed["response_text"] == "test"


def test_json_extraction_invalid():
    """Invalid JSON should return None."""
    assert _extract_json_from_text("This is not JSON at all.") is None
    assert _extract_json_from_text("") is None


# ===========================================================================
# 11. CONVERSATION MANAGER INTEGRATION WITH LLM OBSERVATIONS
# ===========================================================================

def test_conversation_manager_stores_observations():
    """
    ConversationManager must store LLM-extracted observations
    in MedhaState.candidate_observations.
    """
    mock_llm = MockLLMProvider()
    manager = ConversationManager(
        text_adapter=MockTextAdapter(),
        llm_provider=mock_llm,
    )
    session = manager.create_session(victim_id="VIC_CM_OBS", session_id="sess_obs")

    turn = manager.process_message(
        session_id="sess_obs",
        message="I can't sleep and I feel so scared.",
    )

    # Observations should be stored in state
    obs_list = session.state.candidate_observations
    assert len(obs_list) >= 2

    domains = {o.domain for o in obs_list}
    assert "sleep" in domains
    assert "fear" in domains

    # Each observation must have evidence
    for obs in obs_list:
        assert obs.evidence is not None
        assert len(obs.evidence) > 0
        assert obs.status == "candidate"


def test_conversation_manager_no_observations_on_neutral():
    """Neutral messages should not create candidate observations."""
    manager = ConversationManager(
        text_adapter=MockTextAdapter(),
        llm_provider=MockLLMProvider(),
    )
    session = manager.create_session(victim_id="VIC_CM_NEUT", session_id="sess_neut")

    manager.process_message(session_id="sess_neut", message="Hello, good morning.")

    assert len(session.state.candidate_observations) == 0


# ===========================================================================
# 12. PROVIDER INDEPENDENCE
# ===========================================================================

def test_provider_independence():
    """
    ConversationManager must work with any LLMProviderProtocol,
    not just Gemini or the mock.
    """
    class CustomProvider:
        def generate_response(self, message, state, next_question=None, **kwargs):
            return LLMResponse(
                text="Custom provider response.",
                candidate_observations=[
                    {"domain": "mood", "value": "low", "evidence": message[:20], "source": "custom"},
                ],
                metadata={"provider": "custom_test"},
            )

    manager = ConversationManager(
        text_adapter=MockTextAdapter(),
        llm_provider=CustomProvider(),
    )
    session = manager.create_session(victim_id="VIC_CUSTOM", session_id="sess_custom")

    turn = manager.process_message(
        session_id="sess_custom",
        message="I'm feeling down today.",
    )

    assert turn.assistant_response == "Custom provider response."
    assert len(session.state.candidate_observations) == 1
    assert session.state.candidate_observations[0].domain == "mood"


# ===========================================================================
# 13. SYSTEM PROMPT SAFETY VERIFICATION
# ===========================================================================

def test_system_prompt_contains_safety_rules():
    """System prompt must contain explicit safety and boundary rules."""
    prompt = SYSTEM_PROMPT.lower()
    assert "never assign numerical scores" in prompt or "never" in prompt
    assert "dds" in prompt
    assert "risk" in prompt
    assert "diagnosis" in prompt or "diagnos" in prompt
    assert "empathetic" in prompt or "supportive" in prompt


def test_system_prompt_contains_controlled_domains():
    """System prompt must list the controlled observation domains."""
    for domain in ["sleep", "mood", "fear", "stress", "safety"]:
        assert domain in SYSTEM_PROMPT


# ===========================================================================
# 14. QUESTION ENGINE INTEGRATION
# ===========================================================================

def test_question_engine_integration():
    """If a QuestionRecord is passed, the response should acknowledge it."""
    provider = MockLLMProvider()
    state = MedhaState(victim_id="VIC_QE", timepoint=1)
    question = QuestionRecord(
        question_id="Q_SLEEP",
        question_text="How has your sleep been lately?",
        intent="assess_sleep",
    )

    result = provider.generate_response(
        message="Things are tough.",
        state=state,
        next_question=question,
    )

    assert "sleep" in result.text.lower()
