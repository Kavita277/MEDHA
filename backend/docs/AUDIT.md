# MEDHA Backend Integration & Architecture Audit

**Date:** 2026-09-10  
**Status:** AUDIT COMPLETE — PRE-IMPLEMENTATION PHASE  
**Execution Objective:** Comprehensive codebase and architectural audit prior to backend implementation. No existing engine, chatbot, or model files have been modified.

---

## 1. Executive Summary

This audit establishes the baseline for building the **MEDHA Backend Service**. It examines the complete repository to evaluate existing architectural boundaries, runtime entry points, state handling, specialist adapters, safety protocols, and machine learning pipelines.

### Primary Audit Findings:
1. **The Machine Learning Core (MEDHA V2) is 100% Frozen:** All models (Structured XGBoost, Text Ridge, Voice Ridge, Behaviour Ridge, Fusion XGBoost, and PyTorch Temporal GRU) under `engine/` are fully trained, mathematically validated, and strictly frozen. They must not be modified, retrained, or bypassed.
2. **The Chatbot Orchestration Layer is Fully Implemented & Verified:** All conversational subcomponents (`MedhaState`, `ConversationManager`, `DeterministicSafetyGateway`, `SafetyTrigger`, `DeterministicQuestionEngine`, `DeterministicFeatureMapper`, `ConversationSummaryEngine`, and specialist adapters) are fully implemented and verified via 146 unit/integration tests.
3. **Current User Interface is Monolithic Streamlit:** Currently, `app.py` runs Streamlit and instantiates `ConversationManager` and specialist adapters directly in-process. 
4. **Backend Directory (`backend/`):** The `backend/` directory exists in the workspace root but is **completely empty**. There is currently **no unified REST API, no FastAPI service layer, no database persistence, and no production alert backend**.
5. **Pre-existing Legacy APIs:** A few isolated, legacy specialist scripts exist inside `engine/` (e.g. `engine/voice_engine/main.py`, `engine/gru-temporal-risk/src/inference_api.py`, `engine/behaviour_engine/medha_scoring_api.py`). These are standalone prototypes and not unified backend services.
6. **Test Suite Status:** 
   - Chatbot Test Suite (`chatbot/tests/`): **146 passed**.
   - Engine Test Suite (`engine/tests/`): **224 passed**.
   - Total Verified Tests: **370 passed, 0 failed**.

---

## 2. Current Repository Structure

```text
MEDHA/
├── .env                              # Local environment secrets (GEMINI_API_KEY)
├── .env.example                      # Template configuration
├── requirements.txt                  # Python dependencies (FastAPI, PyTorch, Transformers, etc.)
├── app.py                            # Streamlit Chat UI (direct in-process integration)
├── scratch_audit_v2_interfaces.py    # Interface verification scratch script
├── backend/                          # [EMPTY] Target directory for upcoming backend API
├── docs/                             # MEDHA V2 architecture, contracts, audits, and model cards
│   ├── MEDHA_V2_ARCHITECTURE.md
│   ├── MEDHA_V2_API_HANDOFF.md
│   ├── MEDHA_V2_STEP17C_BACKEND_VERIFICATION.md
│   └── ... (30+ V2 validation documents)
├── chatbot/                          # Chatbot Orchestration & State Layer
│   ├── __init__.py
│   ├── conversation_manager.py       # Orchestration engine & session manager
│   ├── interfaces.py                 # Abstract protocols (LLM, Safety, Question, Adapters)
│   ├── plan.md                       # Chatbot implementation trajectory
│   ├── docs/                         # Chatbot architectural reports & Developer Guide
│   │   ├── MEDHA_CHATBOT_DEVELOPER_GUIDE.md
│   │   ├── MEDHA_QUESTION_ENGINE_GUIDE.md
│   │   ├── MEDHA_CHATBOT_SAFETY_TRIGGER_REPORT.md
│   │   └── ...
│   ├── engines/                      # Specialist adapters
│   │   ├── text_adapter.py           # MuRIL NLP adapter
│   │   ├── voice_adapter.py          # Acoustic voice adapter
│   │   ├── behaviour_adapter.py      # Behavioral telemetry adapter
│   │   └── question_engine.py        # Deterministic Question Engine
│   ├── features/
│   │   └── feature_mapper.py         # Authoritative observation mapper
│   ├── llm/
│   │   ├── gemini_provider.py        # Google Gemini LLM provider
│   │   ├── mock_provider.py          # Deterministic offline mock LLM
│   │   ├── observation_schema.py     # Controlled candidate observation schema
│   │   └── prompt_templates.py       # Trauma-informed system prompt
│   ├── safety/
│   │   ├── safety_gateway.py         # Deterministic user-facing crisis interceptor
│   │   └── safety_trigger.py         # Non-blocking explicit safety alert trigger & MockAlertEngine
│   ├── state/
│   │   └── medha_state.py            # Central MedhaState container (62 features, sessions, history)
│   ├── summary/
│   │   ├── conversation_summary_engine.py  # Contextual memory extractor
│   │   └── summary_schema.py         # Summary item dataclasses
│   ├── v2_adapter/
│   │   └── medha_v2_adapter.py       # Adapter bridging MedhaState to MedhaV2Pipeline
│   └── tests/                        # 146 unit & integration tests
│       ├── test_behaviour_adapter.py
│       ├── test_conversation_manager.py
│       ├── test_conversation_summary.py
│       ├── test_end_to_end_integration.py
│       ├── test_feature_mapper.py
│       ├── test_llm_extraction.py
│       ├── test_medha_state.py
│       ├── test_question_engine.py
│       ├── test_safety_gateway.py
│       ├── test_safety_trigger.py
│       ├── test_text_adapter.py
│       ├── test_v2_adapter.py
│       └── test_voice_adapter.py
└── engine/                           # [FROZEN] Core Machine Learning Models & Data
    ├── QuestionEngine/               # Authoritative questions.json database & legacy scripts
    ├── Structured_risk_enigne/       # Legacy structured logic
    ├── behaviour_engine/             # Pre-existing Behaviour artifacts
    ├── configs/                      # Feature configs
    ├── data/                         # Synthetic training and evaluation datasets
    ├── fusion_engine/                # Legacy fusion prototypes
    ├── gru-temporal-risk/            # Legacy V1 GRU scripts (DO NOT USE)
    ├── legacy_v1/                    # Preserved V1 baseline code
    ├── models/                       # Frozen weights, JSONs, PKLs, and checkpoints
    ├── outputs/                      # Final model evaluation artifacts & metrics
    ├── results/                      # Specialist evaluation metrics
    ├── tests/                        # 224 frozen V2 engine unit tests
    ├── text engine/                  # Frozen MuRIL multi-head NLP engine
    ├── voice_engine/                 # Frozen acoustic voice engine
    └── v2/                           # Authoritative V2 Pipeline
        ├── medha_v2_pipeline.py      # Official runtime entry point: MedhaV2Pipeline
        ├── priority_triage.py        # TriageEngine (Demonstration ruleset)
        ├── v2_feature_policy.py      # Canonical V2 feature definitions
        └── ... (V2 training & evaluation scripts)
```

---

## 3. Answers to the 20 Core Audit Questions

### 1. How the chatbot is instantiated
In `app.py` (lines 48–57), the chatbot is instantiated by injecting pluggable adapters into the `ConversationManager`:
```python
st.session_state.manager = ConversationManager(
    text_adapter=MedhaTextAdapter(),
    llm_provider=GeminiProvider(),
    safety_gateway=DeterministicSafetyGateway(),
    question_engine=DeterministicQuestionEngine(),
    feature_mapper=DeterministicFeatureMapper(),
    summary_engine=ConversationSummaryEngine(),
    behaviour_adapter=MedhaBehaviourAdapter(),
    voice_adapter=MedhaVoiceAdapter(),
    safety_trigger=SafetyTrigger(alert_engine=MockAlertEngine())
)
```
If dependencies are omitted, `ConversationManager.__init__` automatically provides defaults for all protocols.

### 2. How `ConversationManager` works
`ConversationManager` (`chatbot/conversation_manager.py`) is the central orchestrator coordinating turn processing and session isolation.
- **Turn Order in `process_message()`:**
  1. *Validation:* Verifies session exists, is active, and message is valid text.
  2. *State Update:* Records user message in `MedhaState.conversation_history`.
  3. *Safety Trigger (Additive & Non-blocking):* Evaluates explicit immediate emergencies. If detected, emits `SafetyEvent` to `AlertEngine` and logs to `state.safety_events`. Does **not** block conversational continuation or ML prediction.
  4. *Behaviour Adapter:* Ingests raw telemetry into `state.behaviour_features`.
  5. *Voice Adapter:* Analyzes audio via `VoiceEngine` and updates `state.voice_features`.
  6. *Safety Gateway (Conversational Intercept):* Deterministically halts the turn with crisis hotline information if explicit clinical threat or emergency criteria are met.
  7. *Text Engine Adapter:* Runs frozen MuRIL NLP model and updates `state.text_features`.
  8. *Question Engine:* Evaluates missing structured features and selects the next question off cooldown.
  9. *Summary Engine:* Updates compact contextual memory in `state.conversation_summary`.
  10. *LLM Provider:* Generates natural response and extracts qualitative candidate observations.
  11. *Candidate Observations Stored:* Logs observations into `state.candidate_observations`.
  12. *Feature Mapper:* Authoritatively updates `state.structured_features` if an approved mapping exists (`Threat_Event`, `Recent_Episode`).
  13. *Record Assistant Reply:* Logs response in `MedhaState.conversation_history` and returns `TurnResult`.

### 3. How `MedhaState` works
`MedhaState` (`chatbot/state/medha_state.py`) is the model-agnostic, central state container.
- **62 Canonical Features:**
  - 42 Structured features (3 categorical: `Case_Type`, `Case_Stage`, `Episode_Severity` + 39 numeric).
  - 5 Text features (`Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`).
  - 5 Voice features (`Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`).
  - 10 Behaviour features (`Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, etc.).
- **Modality Availability Flags:** `struct_available` (1.0), `behav_available` (1.0), `text_available` (1.0/0.0/None), `voice_available` (1.0/0.0/None).
- **CRITICAL RULE — MISSING IS NOT ZERO:** Absent or unassessed features strictly remain `None` (or `np.nan` in DataFrames). They are **never** coerced to `0.0`.
- **Sub-structures:** `conversation_history: List[ChatMessage]`, `question_history: List[QuestionRecord]`, `candidate_observations: List[CandidateObservation]`, `conversation_summary: ConversationSummary`, `safety_events: List[Dict[str, Any]]`.
- **Serialization:** Full JSON export/import via `to_dict()`, `to_json()`, and `from_dict()`.

### 4. How sessions currently work
- Sessions are maintained in-memory in `ConversationManager._sessions: Dict[str, ConversationSession]`.
- Managed via `create_session(victim_id, session_id, timepoint)`, `get_session(session_id)`, `close_session()`, `reopen_session()`, `delete_session()`, `list_sessions()`.
- Each session isolates its own `MedhaState`.
- **Current Limitation:** There is **no database persistence**. If the process restarts, all active sessions in memory are lost.

### 5. How Question Engine is called
- Called in `ConversationManager.process_message()` at Step 8: `next_question = self.question_engine.select_next_question(state=state)`.
- Sourced from [`engine/QuestionEngine/questions.json`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/QuestionEngine/questions.json).
- Checks `state.structured_features` for `None`/`NaN`.
- **Context-Aware Suppression:** If a candidate observation already exists for a domain (e.g. `sleep="poor"`), questioning for that domain is suppressed to prevent interrogating the user.
- Checks cooldowns in `state.question_history` (`_is_off_cooldown`).
- Orders by priority (Priority 1: Safety, Priority 2: Stress, Priority 3: Functioning/Sleep/Social, Priority 4: Wellbeing).
- Selects at most **one** question per turn.

### 6. How `QuestionRecord` is represented
Dataclass in `chatbot/state/medha_state.py`:
```python
@dataclass
class QuestionRecord:
    question_id: str
    question_text: str
    intent: str
    asked_at: str
    answered: bool = False
    cooldown_until: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 7. How Safety Trigger works
- Implemented in `chatbot/safety/safety_trigger.py`.
- Non-blocking, additive background safety layer.
- Prompts the LLM with a strict JSON classification schema checking for 5 allowed emergency types:
  - `immediate_danger`, `self_harm_intent`, `suicidal_intent`, `threat_to_other`, `immediate_protection_concern`.
- Ordinary sadness, stress, and negations ("I am not suicidal") do **not** trigger alerts.
- Checks idempotency against recent events to prevent duplicate alert spam.
- Dispatches `SafetyEvent` to `AlertEngineProtocol.emit_safety_event()`.
- Logs event to `state.safety_events`.
- Wrapped in `try...except`; alert delivery failures **never** crash the conversation or halt the MEDHA V2 pipeline.

### 8. How Safety Gateway works
- Implemented in `chatbot/safety/safety_gateway.py`.
- Synchronous, deterministic conversational gatekeeper.
- Checks:
  - `state.candidate_observations` for: `safety in ["unsafe", "in_danger"]`, `threat_event == "present"`, `urgency == "critical"`.
  - `state.structured_features` for: `Threat_Event == 1.0`, `Recent_Episode == 1.0`.
- If triggered: **Halts regular LLM generation immediately**, records a deterministic crisis hotline response, and returns `TurnResult`.

### 9. How `AlertEngineProtocol` works
- Protocol defined in `chatbot/safety/safety_trigger.py`:
  ```python
  @runtime_checkable
  class AlertEngineProtocol(Protocol):
      def emit_safety_event(self, event: SafetyEvent) -> bool: ...
  ```
- Currently implemented by `MockAlertEngine`, which records events in an in-memory list (`emitted_events`).
- **No external alert backend (webhook, SMS, PagerDuty, or EHR) currently exists.**

### 10. How Behaviour Adapter works
- Implemented in `chatbot/engines/behaviour_adapter.py`.
- Validates and ingests raw interaction telemetry (`Session_Duration_Minutes`, `Interaction_Frequency_7d`, `Response_Delay_Hours`, etc.) into `state.behaviour_features`.
- Missing values remain `None`.
- Does **not** execute ML models directly; inference is owned by `MedhaV2Pipeline.predict_v2()`.

### 11. How Voice Adapter works
- Implemented in `chatbot/engines/voice_adapter.py`.
- Accepts an `audio_path` string pointing to an on-disk audio file.
- Lazily instantiates `VoiceEngine` from `engine/voice_engine/voice_engine.py` and calls `VoiceEngine.analyze(audio_path)`.
- Populates the 5 canonical features: `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`.
- Sets `state.voice_available = 1.0` (or `0.0` if audio is absent/corrupt).
- Does **not** execute the Voice Tabular DDS Ridge model.

### 12. How Feature Mapper works
- Implemented in `chatbot/features/feature_mapper.py`.
- Deterministic gatekeeper converting qualitative candidate observations into V2 structured features.
- **Strict Whitelist:** Only authoritative mappings (`threat_event` -> `Threat_Event: 1.0/0.0`, `recent_episode` -> `Recent_Episode: 1.0/0.0`) are allowed to update structured features.
- All qualitative statements (`sleep="poor"`, `mood="low"`, `stress="high"`) are **intentionally rejected from numeric mapping** because no clinical numeric conversion schema exists. They remain as candidate observations.
- Never overwrites existing non-null structured features from check-ins.

### 13. How Summary Engine works
- Implemented in `chatbot/summary/conversation_summary_engine.py`.
- Compact memory summarizer tracking 8 categories: `important_facts`, `current_concerns`, `recent_events`, `support_context`, `preferences`, `ongoing_topics`, `unresolved_topics`, `important_observations`.
- Stores `SummaryItem` objects with provenance, status (`active`, `superseded`, `unresolved`), and timestamps.
- Functions as conversational context for the LLM; **never used as a numerical risk score**.

### 14. How LLM provider works
- Conforms to `LLMProviderProtocol` in `chatbot/interfaces.py`.
- Primary implementation: `GeminiProvider` (`chatbot/llm/gemini_provider.py`) using `google-genai` SDK.
- Configured via `GEMINI_API_KEY` and `MEDHA_LLM_MODEL` (default: `gemini-3.1-flash-lite`).
- Generates natural, trauma-informed supportive dialogue guided by `chatbot/llm/prompt_templates.py`.
- Simultaneously extracts candidate observations validated against `chatbot/llm/observation_schema.py`.
- Includes offline `MockLLMProvider` and `PlaceholderLLMProvider` for testing without API keys.

### 15. How `MedhaV2Adapter` works
- Implemented in `chatbot/v2_adapter/medha_v2_adapter.py`.
- Translates `MedhaState` into a pandas DataFrame matching the exact schema and column order required by `MedhaV2Pipeline.predict_v2()`.
- Preserves missingness as `np.nan`.
- Sets `Text_Available` and `Voice_Available` explicitly to `1.0` or `0.0`.
- Executes `MedhaV2Pipeline.predict_v2(df)` and maps outputs to `V2PredictionResult`.

### 16. How the frozen V2 pipeline is called
- Module: `engine.v2.medha_v2_pipeline.MedhaV2Pipeline`.
- Execution:
  ```python
  from engine.v2.medha_v2_pipeline import MedhaV2Pipeline
  pipeline = MedhaV2Pipeline()
  output_df = pipeline.predict_v2(input_df)
  ```
- **Internal Pipeline Stages:**
  1. *Specialist Inference:*
     - Structured XGBoost -> `Struct_Pred`
     - Text Ridge -> `Text_Pred` (or NaN if `Text_Available==0`)
     - Voice Ridge -> `Voice_Pred` (or NaN if `Voice_Available==0`)
     - Behaviour Ridge -> `Behav_Pred` (computed using absolute deviations)
  2. *Fusion Inference:*
     - XGBoost Regressor over 8 features (4 predictions + 4 availability flags) -> `Fusion_DDS_Prediction` (0–100).
  3. *Temporal GRU Inference:*
     - PyTorch GRU over 57 whitelisted features with a strict 7-timestep historical window -> `Temporal_Risk_Score` (0–1) and `Future_Escalation_Flag` (1/0).

### 17. What interfaces are already available for integration
- `chatbot/interfaces.py`:
  - `LLMProviderProtocol`, `SafetyGatewayProtocol`, `QuestionEngineProtocol`, `FeatureMapperProtocol`, `SummaryEngineProtocol`, `TextAdapterProtocol`, `BehaviourAdapterProtocol`, `VoiceAdapterProtocol`.
- `chatbot/safety/safety_trigger.py`: `AlertEngineProtocol`.
- `chatbot/conversation_manager.py`: `ConversationManager`.
- `chatbot/v2_adapter/medha_v2_adapter.py`: `MedhaV2Adapter`.
- `engine/v2/medha_v2_pipeline.py`: `MedhaV2Pipeline`.
- `engine/v2/priority_triage.py`: `TriageEngine`.

### 18. What code must remain untouched
- Everything in `engine/`:
  - `engine/v2/`
  - `engine/models/` (JSON configs, pickle files, `.joblib` scalers, `.pth` PyTorch weights)
  - `engine/text engine/`
  - `engine/voice_engine/`
  - `engine/behaviour_engine/`
  - `engine/Structured_risk_enigne/`
  - `engine/fusion_engine/`
  - `engine/gru-temporal-risk/`
  - `engine/QuestionEngine/questions.json`
- Feature lists and orderings in configuration files.
- Internal logic of `chatbot/conversation_manager.py`, `chatbot/state/medha_state.py`, `chatbot/safety/safety_gateway.py`.

### 19. What dependencies are already installed
Verified against active Python 3.14 environment and `requirements.txt`:
- Core Web: `fastapi>=0.100.0`, `uvicorn>=0.22.0`, `pydantic>=2.0.0`, `python-multipart>=0.0.6`.
- Data Science / ML: `numpy>=1.24.0`, `pandas>=2.0.0`, `scipy>=1.10.0`, `scikit-learn>=1.2.0`, `xgboost>=1.7.0`, `shap>=0.42.0`, `joblib>=1.2.0`.
- Deep Learning & NLP: `torch>=2.0.0`, `transformers>=4.30.0`.
- Audio Processing: `librosa>=0.10.0`, `soundfile>=0.12.0`.
- GenAI & App: `google-genai`, `python-dotenv`, `streamlit`.
- Testing: `pytest>=7.4.0`.

### 20. Whether any backend/API code already exists
- **Unified Backend API:** **DOES NOT EXIST.** The `backend/` directory is completely empty.
- **Isolated Prototype Endpoints:**
  - `engine/voice_engine/main.py` (standalone voice test endpoint)
  - `engine/gru-temporal-risk/src/inference_api.py` (legacy V1 GRU endpoint)
  - `engine/behaviour_engine/medha_scoring_api.py` (legacy behaviour endpoint)
- Currently, the application is driven solely through the Streamlit frontend (`app.py`), which interacts directly with `ConversationManager` in-memory.

---

## 4. Existing Architecture & Integration Points

```text
                                 CLIENT LAYER
              ┌──────────────────────────────────────────────────┐
              │ Streamlit UI (app.py) / Future Web / Mobile App  │
              └────────────────────────┬─────────────────────────┘
                                       │
                         [RECOMMENDED BACKEND BOUNDARY]
                                       │
                                       ▼
              ┌──────────────────────────────────────────────────┐
              │             FASTAPI BACKEND SERVICE              │
              │             (To be built in backend/)            │
              │  - Session Management (REST / WebSocket)         │
              │  - Turn Processing Endpoints                     │
              │  - Production Alert Engine Implementation        │
              │  - Persistence Layer (DB / Redis / PostgreSQL)   │
              └───────────────┬──────────────────┬───────────────┘
                              │                  │
                              ▼                  ▼
     ┌────────────────────────────────┐  ┌─────────────────────────────┐
     │      ConversationManager       │  │   AlertEngineProtocol       │
     │     (chatbot orchestration)    │  │   (Production Webhooks/SMS) │
     └───────────────┬────────────────┘  └─────────────────────────────┘
                     │
                     ▼
     ┌────────────────────────────────┐
     │        MedhaV2Adapter          │
     └───────────────┬────────────────┘
                     │
                     ▼
     ┌────────────────────────────────────────────────────────┐
     │    FROZEN MEDHA V2 PIPELINE (engine/v2)                │
     │    - Structured / Text / Voice / Behaviour Models      │
     │    - Fusion XGBoost Regressor (Current DDS)            │
     │    - Temporal GRU Regressor (Future Risk)              │
     │    - Triage Engine (Priority)                          │
     └────────────────────────────────────────────────────────┘
```

---

## 5. Architectural Risks & Fragilities

1. **In-Memory Session Volatility:** All session histories are stored in Python dictionaries (`ConversationManager._sessions`). Any server reboot or process termination erases all active conversations.
2. **Missing Production Alert Implementation:** `SafetyTrigger` currently defaults to `MockAlertEngine`. If an emergency occurs in production, no caseworker webhook or SMS is actually fired.
3. **Audio File Cleanup:** Voice input requires temporary `.wav` files on disk for `librosa`. While `app.py` cleans up temp files in a `finally:` block, high concurrency in a backend service requires careful asynchronous temp file management.
4. **LLM API Rate Limits & Latency:** Real-time calls to `GeminiProvider` depend on external Google GenAI endpoints. Network latency or quota exhaustion must be gracefully handled with timeouts.
5. **Frozen Pipeline Schema Strictness:** As verified in `docs/MEDHA_V2_STEP17C_BACKEND_VERIFICATION.md`, `MedhaV2Pipeline.predict_v2()` requires `Text_Available` and `Voice_Available` explicitly in the input DataFrame; omitting these columns causes an `AttributeError`.

---

## 6. Recommended Backend Integration Boundaries

1. **Build the Backend Inside `backend/`:**
   - Develop a clean, modular FastAPI application inside `backend/` (e.g. `backend/main.py`, `backend/routers/`, `backend/schemas/`, `backend/services/`).
2. **Do Not Duplicate Logic:**
   - The backend service should import and wrap `ConversationManager` and `MedhaV2Adapter`.
   - It should NOT re-implement turn flow, safety rules, question logic, or feature mapping.
3. **Implement Production `AlertEngineProtocol`:**
   - Create a production `AlertEngine` in `backend/` that implements `AlertEngineProtocol` and routes `SafetyEvent` payloads to webhooks, email, SMS, or incident queues.
4. **Implement Session Persistence:**
   - Wrap session storage in a database repository (e.g. SQLAlchemy, PostgreSQL, or Redis) by leveraging `MedhaState.to_dict()` and `MedhaState.from_dict()`.
5. **Keep `engine/` Completely Frozen:**
   - Strictly access V2 inference via `MedhaV2Adapter` or `MedhaV2Pipeline()`. Never edit code in `engine/`.

---

## 7. Audit Verification & Sign-Off

- **Files Inspected:**
  - `chatbot/conversation_manager.py`
  - `chatbot/interfaces.py`
  - `chatbot/state/medha_state.py`
  - `chatbot/engines/text_adapter.py`
  - `chatbot/engines/voice_adapter.py`
  - `chatbot/engines/behaviour_adapter.py`
  - `chatbot/engines/question_engine.py`
  - `chatbot/features/feature_mapper.py`
  - `chatbot/llm/gemini_provider.py`
  - `chatbot/llm/mock_provider.py`
  - `chatbot/llm/observation_schema.py`
  - `chatbot/llm/prompt_templates.py`
  - `chatbot/safety/safety_gateway.py`
  - `chatbot/safety/safety_trigger.py`
  - `chatbot/summary/conversation_summary_engine.py`
  - `chatbot/summary/summary_schema.py`
  - `chatbot/v2_adapter/medha_v2_adapter.py`
  - `engine/v2/medha_v2_pipeline.py`
  - `engine/v2/priority_triage.py`
  - `engine/QuestionEngine/questions.json`
  - `app.py`
  - `requirements.txt`
  - `docs/MEDHA_V2_ARCHITECTURE.md`
  - `docs/MEDHA_V2_API_HANDOFF.md`
  - `docs/MEDHA_V2_STEP17C_BACKEND_VERIFICATION.md`
  - `docs/MEDHA_V2_BEHAVIOUR_DDS.md`
  - `chatbot/docs/MEDHA_CHATBOT_DEVELOPER_GUIDE.md`
  - `chatbot/docs/MEDHA_QUESTION_ENGINE_GUIDE.md`
- **Files Created:** `backend/AUDIT.md`
- **Files Modified:** None
- **Tests Executed:**
  - `pytest chatbot/tests` (146 passed)
  - `pytest engine/tests` (224 passed)
- **Total Test Results:** 370 passed, 0 failed.
- **Architecture Conflicts:** **NONE.** The codebase architecture is completely aligned and ready for backend integration.
