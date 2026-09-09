# MEDHA Chatbot — Developer Guide

> **Authoritative Technical Manual for Engineering, Maintenance, Integration, and Extension**  
> *Target Audience: New Developers, Backend Engineers, Frontend Engineers, ML Engineers, Caseworker Integrators, and Maintainers*

---

## Table of Contents

1. [Overview](#1-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Component-by-Component Explanation](#3-component-by-component-explanation)
   - [3.1 MedhaState](#31-medhastate)
   - [3.2 Conversation Manager](#32-conversation-manager)
   - [3.3 Safety Trigger](#33-safety-trigger)
   - [3.4 Alert Engine](#34-alert-engine)
   - [3.5 Safety Gateway](#35-safety-gateway)
   - [3.6 Text Engine Adapter](#36-text-engine-adapter)
   - [3.7 Voice Adapter](#37-voice-adapter)
   - [3.8 Behaviour Adapter](#38-behaviour-adapter)
   - [3.9 LLM Provider / Gemini](#39-llm-provider--gemini)
   - [3.10 Feature Mapper / Validator](#310-feature-mapper--validator)
   - [3.11 Question Engine](#311-question-engine)
   - [3.12 Conversation Summary](#312-conversation-summary)
   - [3.13 MEDHA V2 Adapter](#313-medha-v2-adapter)
   - [3.14 MEDHA V2 Pipeline (Frozen Boundary)](#314-medha-v2-pipeline-frozen-boundary)
4. [End-to-End Message Lifecycle](#4-end-to-end-message-lifecycle)
5. [Data Flow & Schema Specifications](#5-data-flow--schema-specifications)
6. [Feature Contract](#6-feature-contract)
7. [Running the Chatbot](#7-running-the-chatbot)
8. [Developer Integration Guide](#8-developer-integration-guide)
9. [Extension Guide](#9-extension-guide)
10. [Safety and Privacy Rules](#10-safety-and-privacy-rules)
11. [FROZEN MEDHA V2 — DO NOT MODIFY](#11-frozen-medha-v2--do-not-modify)
12. [Testing Guide](#12-testing-guide)
13. [Test Architecture](#13-test-architecture)
14. [Troubleshooting](#14-troubleshooting)
15. [Known Limitations](#15-known-limitations)
16. [Security and Production Considerations](#16-security-and-production-considerations)
17. [File and Directory Map](#17-file-and-directory-map)
18. ["Where Do I Make This Change?" Lookup Table](#18-where-do-i-make-this-change-lookup-table)
19. [Developer Rules (Do's and Don'ts)](#19-developer-rules-dos-and-donts)
20. [Quick Start for a New Developer](#20-quick-start-for-a-new-developer)
21. [Architecture Invariants](#21-architecture-invariants)

---

## 1. Overview

### What is the MEDHA Chatbot?
The **MEDHA Chatbot** is a trauma-informed, privacy-preserving conversational orchestration system designed to support victims and individuals under crisis while systematically gathering multi-modal evidence for the **MEDHA V2 Predictive Engine**.

### Why Does it Exist and What Problem Does it Solve?
Traditional risk assessment protocols require users to complete rigid, stressful, clinical questionnaires. The MEDHA Chatbot replaces this friction with an empathetic, supportive conversational interface. As the user chats naturally (via text or voice), the system:
- Provides supportive conversational companionship.
- Extracts semantic candidate observations and acoustic emotional markers in the background.
- Selects controlled, low-burden follow-up questions only when critical clinical information is missing.
- Dispatches immediate safety alerts to backend responders if imminent danger or self-harm is detected.
- Converts accumulated session state into clean, mathematically valid longitudinal inputs for the frozen MEDHA V2 clinical machine learning models.

### How it Relates to MEDHA V2
> **CRITICAL ARCHITECTURAL BOUNDARY:**  
> The chatbot is an **orchestration and interaction layer around the existing MEDHA V2 system. It is NOT a replacement for MEDHA V2.**

The chatbot **never** computes the Dynamic Distress Score (DDS), **never** predicts Future Risk, **never** alters ML weights, and **never** diagnoses clinical conditions. All predictive scoring and temporal forecasting belong strictly to the frozen `engine/` repository.

### Separation of Concerns
The system enforces strict decoupling between 7 core pillars:
1. **Conversational Intelligence:** Generating empathetic, supportive natural language replies (via `LLMProviderProtocol`).
2. **Semantic Extraction:** Extracting qualitative observations without inventing numerical numbers (via `observation_schema.py`).
3. **Safety Handling:** Deterministically escalating immediate crises to the user (via `SafetyGateway`) and emitting non-blocking backend alerts (via `SafetyTrigger`).
4. **Feature Mapping:** Authoritatively validating which semantic notes can update MEDHA V2 structured features (via `DeterministicFeatureMapper`).
5. **Specialist Engines:** Processing raw text through fine-tuned MuRIL NLP and raw audio through acoustic feature extraction (via adapters).
6. **MEDHA V2 Prediction:** Executing frozen XGBoost, Ridge, and GRU models across longitudinal timepoints (via `MedhaV2Adapter`).
7. **Alerting:** Notifying caseworkers or crisis professionals via the `AlertEngineProtocol`.

---

## 2. High-Level Architecture

The following diagram illustrates the complete conversational turn and the decoupled alert and prediction paths:

```text
                                  USER
                                   │
                                   ▼
                             ┌───────────┐
                             │  Chat UI  │ (Streamlit / app.py)
                             └─────┬─────┘
                                   │
                         User Message / Audio
                                   │
                                   ▼
                     ┌───────────────────────────┐
                     │    ConversationManager    │
                     └─────────────┬─────────────┘
                                   │
   ┌───────────────────────────────┴──────────────────────────────┐
   │                                                              │
   ▼                                                              ▼
┌──────────────────────┐                               ┌──────────────────────┐
│    Safety Trigger    │ (Immediate danger evaluation) │  Specialist Adapters │
└──────────┬───────────┘                               └──────────┬───────────┘
           │ [Explicit Concern]                                   │
           ▼                                                      ├─► Behaviour Adapter
┌──────────────────────┐                                          ├─► Voice Adapter
│  AlertEngineProtocol │                                          └─► Text Adapter (MuRIL)
└──────────┬───────────┘                                                  │
           │                                                              ▼
           ▼                                                   ┌──────────────────────┐
┌──────────────────────┐                                       │     Safety Gateway   │
│   Backend Caseworker │                                       └──────────┬───────────┘
│   / Crisis System    │                                                  │ (Not triggered)
└──────────────────────┘                                                  ▼
                                                               ┌──────────────────────┐
                                                               │   Question Engine    │
                                                               └──────────┬───────────┘
                                                                          │
                                                                          ▼
                                                               ┌──────────────────────┐
                                                               │    Summary Engine    │
                                                               └──────────┬───────────┘
                                                                          │
                                                                          ▼
                                                               ┌──────────────────────┐
                                                               │  LLM / Gemini Engine │
                                                               └──────────┬───────────┘
                                                                          │ Candidate Observations
                                                                          ▼
                                                               ┌──────────────────────┐
                                                               │    Feature Mapper    │
                                                               └──────────┬───────────┘
                                                                          │
                                                                          ▼
                                                               ┌──────────────────────┐
                                                               │      MedhaState      │
                                                               └──────────┬───────────┘
                                                                          │
                                      LONGITUDINAL EVALUATION             ▼
                                                               ┌──────────────────────┐
                                                               │   MEDHA V2 Adapter   │
                                                               └──────────┬───────────┘
                                                                          │
                                                                          ▼
                                                      ┌─────────────────────────────────────────┐
                                                      │ FROZEN: MedhaV2Pipeline.predict_v2()    │
                                                      │  - Structured / Text / Voice / Behaviour│
                                                      │  - Fusion XGBoost (Current DDS)         │
                                                      │  - Temporal GRU (Future Risk Score)     │
                                                      └─────────────────────────────────────────┘
```

---

## 3. Component-by-Component Explanation

### 3.1 MedhaState
- **Purpose:** Central model-agnostic session and longitudinal state container. Holds all features, conversational turns, candidate observations, question histories, summary context, and safety logs.
- **Location:** [`chatbot/state/medha_state.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/state/medha_state.py)
- **Inputs:** Raw user messages, specialist features from adapters, candidate observations from LLM, question records, and metadata.
- **Outputs:** Serialized dictionaries (`to_dict()`) and JSON strings (`to_json()`) used by downstream adapters and the UI.
- **Dependencies:** Standard library (`dataclasses`, `json`, `math`, `uuid`). Completely decoupled from external ML frameworks and LLMs.
- **Responsibilities:**
  - Enforce canonical feature naming for 62 V2 features: 42 Structured (3 categorical + 39 numeric), 5 Text, 5 Voice, 10 Behaviour.
  - Track modality availability flags (`struct_available=1.0`, `behav_available=1.0`, `text_available`, `voice_available`).
  - Maintain conversation history (`List[ChatMessage]`) and question history (`List[QuestionRecord]`).
  - Maintain candidate observations (`List[CandidateObservation]`) separate from V2 features.
  - Store safety events (`List[Dict[str, Any]]`) for auditability and deduplication.
- **Critical Rule: MISSING IS NOT ZERO!**
  > When a feature is unassessed or absent, it is strictly stored as `None` (or `np.nan` when passed to DataFrame).  
  > **Never replace missing values with `0.0` or default neutral scores!** In clinical risk modeling, an unassessed risk factor is unknown; setting it to 0.0 asserts that the patient has zero risk, corrupting the ML models.
- **How to Test:** Run `pytest chatbot/tests/test_medha_state.py -v`.

---

### 3.2 Conversation Manager
- **Purpose:** Orchestrator coordinating session lifecycles, turn execution order, dependency injection, and state transitions.
- **Location:** [`chatbot/conversation_manager.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/conversation_manager.py)
- **Inputs:** `session_id`, `message`, optional `audio_path`, optional `behaviour_data`, optional `language`, optional `metadata`.
- **Outputs:** `TurnResult` containing the user message, assistant response, updated state, specialist results, safety results, and question records.
- **Dependencies:** Interfaces defined in [`chatbot/interfaces.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/interfaces.py).
- **Execution Lifecycle (Order of Operations in `process_message`):**
  1. *Validation:* Verifies session exists, is active, and message is valid text.
  2. *Record Message:* Adds user message to `MedhaState.conversation_history`.
  3. *Safety Trigger (Additive & Non-Blocking):* Evaluates explicit immediate danger and emits to backend `AlertEngine`.
  4. *Behaviour Adapter:* Parses session telemetry and updates `state.behaviour_features`.
  5. *Voice Adapter:* Processes raw audio via the Voice Engine and updates `state.voice_features`.
  6. *Safety Gateway (Conversational Intercept):* Deterministically halts the turn with crisis hotline info if clinical criteria are met.
  7. *Text Engine Adapter:* Runs frozen MuRIL NLP model and updates `state.text_features`.
  8. *Question Engine:* Evaluates missing structured features and selects the next approved question if off cooldown.
  9. *Summary Engine:* Updates compact conversational memory.
  10. *LLM Provider:* Generates natural response and extracts qualitative candidate observations.
  11. *Feature Mapper:* Authoritatively maps supported observations to `state.structured_features`.
  12. *Record Assistant Response & Return:* Appends response and returns `TurnResult`.
- **How to Test:** Run `pytest chatbot/tests/test_conversation_manager.py -v`.

---

### 3.3 Safety Trigger
- **Purpose:** Evaluates every user message for *explicit, immediate* safety concerns and dispatches asynchronous alerts to the backend Alert Engine.
- **Location:** [`chatbot/safety/safety_trigger.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/safety/safety_trigger.py)
- **Inputs:** `message`, `state: MedhaState`, `llm_provider`.
- **Outputs:** Optional `SafetyEvent` object; emits to `AlertEngineProtocol`.
- **Allowed Trigger Types (Strict Schema):**
  - `immediate_danger`
  - `self_harm_intent`
  - `suicidal_intent`
  - `threat_to_other`
  - `immediate_protection_concern`
- **Important Policies:**
  - **Distinction from Safety Gateway:** The Safety Trigger generates *backend alerts* for caseworkers without interrupting the user conversation or stopping the MEDHA V2 predictive pipeline.
  - **No False Positives on General Distress:** General expressions of sadness ("I feel empty"), academic stress ("I am overwhelmed by finals"), past trauma ("I was assaulted last year"), or negations ("I am not suicidal") do **NOT** trigger alerts.
  - **Idempotency:** Implements `_is_duplicate()` to inspect the last 5 safety events in the session, preventing alert floods.
  - **Failure Isolation:** Errors in alert delivery are logged and swallowed; they **never** crash the user's chat or stop the V2 pipeline.
- **How to Test:** Run `pytest chatbot/tests/test_safety_trigger.py -v`.

---

### 3.4 Alert Engine
- **Purpose:** Protocol and interface for dispatching urgent safety events to external backend services (e.g., caseworker dashboards, SMS gateways, hospital triage).
- **Location:** Protocol in [`chatbot/safety/safety_trigger.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/safety/safety_trigger.py).
- **Current Repository Status:**
  > **NOTE:** The repository currently defines the `AlertEngineProtocol` and a fully functioning in-memory `MockAlertEngine`.  
  > **No external production webhook or SMS backend is currently connected.** A production alert service should be integrated by implementing `AlertEngineProtocol`.
- **Payload (`SafetyEvent`):**
  - `case_id`: Victim identifier.
  - `session_id`: Active session ID.
  - `source`: `"chatbot"`.
  - `safety_trigger`: `True`.
  - `trigger_type`: One of the 5 allowed trigger strings.
  - `evidence`: Quoted user phrase justifying the alert.
  - `confidence`: Optional float between 0.0 and 1.0.
  - `timestamp`: UTC ISO-8601 string.
- **Delivery vs. Detection:**
  `SafetyTrigger detected an event != Alert Engine delivered the event`.  
  The trigger verifies detection; the alert engine confirms network delivery.

---

### 3.5 Safety Gateway
- **Purpose:** Deterministic rule-based gatekeeper controlling *user-facing* crisis intervention.
- **Location:** [`chatbot/safety/safety_gateway.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/safety/safety_gateway.py)
- **When it Runs:** Step 3 of turn processing, before LLM generation.
- **Trigger Conditions:**
  1. Candidate observations contain:
     - `domain == "safety"` and `value in ["unsafe", "in_danger"]`
     - `domain == "threat_event"` and `value == "present"`
     - `domain == "urgency"` and `value == "critical"`
  2. Structured features contain:
     - `Threat_Event == 1.0`
     - `Recent_Episode == 1.0`
- **What it Does When Triggered:**
  Halts conversational turn processing, bypasses regular LLM generation, and immediately delivers a deterministic, supportive crisis hotline referral.
- **Comparison Table:**

| Feature / Property | Safety Trigger | Safety Gateway |
|---|---|---|
| **Location** | `chatbot/safety/safety_trigger.py` | `chatbot/safety/safety_gateway.py` |
| **Primary Audience** | Backend Caseworker / Alert System | The User in the Chat UI |
| **User-Facing Interrupt?** | **No.** Conversational flow continues. | **Yes.** Replaces LLM response with crisis text. |
| **Emits Backend Alert?** | **Yes.** Emits `SafetyEvent` to `AlertEngine`. | **No.** Acts strictly on conversational routing. |
| **Detection Method** | Structured semantic LLM classification | Deterministic check of observations & features |
| **Pipeline Continuity** | Pipeline continues to Text, Voice, & V2 | Halts turn; returns crisis text immediately |

- **How to Test:** Run `pytest chatbot/tests/test_safety_gateway.py -v`.

---

### 3.6 Text Engine Adapter
- **Purpose:** Thin integration adapter connecting user text to the frozen multi-head MuRIL transformer model in `engine/text engine/medha_text_engine.py`.
- **Location:** [`chatbot/engines/text_adapter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/engines/text_adapter.py)
- **5 Canonical Text Features:**
  1. `Text_Distress` (from `text_distress`)
  2. `Fear` (from `fear_signal`)
  3. `Threat_Context` (from `threat_context`)
  4. `Negative_Affect` (from `negative_affect`)
  5. `Urgency` (from `urgency`)
- **Key Rules:**
  - Preserves continuous probabilities (`0.0` to `1.0`). No thresholding or binarization.
  - When text is analyzed: `Text_Available = 1.0`.
  - When text is empty, whitespace, or engine fails: `Text_Available = 0.0`, and all 5 text features remain `None`.
  - Does **not** modify or fine-tune MuRIL.
- **How to Test:** Run `pytest chatbot/tests/test_text_adapter.py -v`.

---

### 3.7 Voice Adapter
- **Purpose:** Thin adapter connecting raw conversational audio files (`.wav`, `.mp3`) to the frozen acoustic voice analyzer in `engine/voice_engine/voice_engine.py`.
- **Location:** [`chatbot/engines/voice_adapter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/engines/voice_adapter.py)
- **5 Canonical Voice Features:**
  1. `Voice_Distress` (continuous probability)
  2. `Pause_Ratio` (ratio of speech pauses)
  3. `Speech_Rate_Deviation` (deviation from baseline 150 wpm)
  4. `Energy_Deviation` (RMS energy deviation)
  5. `Acoustic_Indicator` (composite pitch/formant indicator)
- **Key Rules:**
  - Populates `MedhaState.voice_features` and sets `Voice_Available = 1.0` if audio succeeds.
  - If audio is missing or corrupted: sets `Voice_Available = 0.0` and features remain `None`.
  - **No Duplicate Inference:** Does **not** execute the V2 Voice Tabular DDS Ridge model. Inference is strictly deferred to `MedhaV2Pipeline.predict_v2()`.
- **How to Test:** Run `pytest chatbot/tests/test_voice_adapter.py -v`.

---

### 3.8 Behaviour Adapter
- **Purpose:** Validates and ingests authoritative session behavioral telemetry into `MedhaState`.
- **Location:** [`chatbot/engines/behaviour_adapter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/engines/behaviour_adapter.py)
- **10 Behaviour Features:**
  `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Hours`, `Response_Delay_Deviation`, `Baseline_Response_Delay`, `Baseline_Engagement`, `Baseline_Checkin_Distress`.
- **Key Rules:**
  - The adapter does **not** perform ML inference. It marshals verified metrics.
  - The adapter **never** converts conversational LLM statements into behavioral numbers.
  - Missing behavioral features remain `None`.
- **How to Test:** Run `pytest chatbot/tests/test_behaviour_adapter.py -v`.

---

### 3.9 LLM Provider / Gemini
- **Purpose:** Conversational response generator and qualitative candidate observation extractor.
- **Location:** [`chatbot/llm/gemini_provider.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/llm/gemini_provider.py)
- **Model:** `gemini-3.1-flash-lite` (configurable via `MEDHA_LLM_MODEL`).
- **Prompt Architecture:** Defined in [`chatbot/llm/prompt_templates.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/llm/prompt_templates.py). Contains strict anti-fabrication rules and trauma-informed behavioral guardrails.
- **Controlled Observation Extraction:**
  Extracted observations are bound by [`chatbot/llm/observation_schema.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/llm/observation_schema.py).
  - Every observation requires `domain`, `value`, and `evidence` (quote from the user).
  - Controlled domains include: `mood`, `stress`, `sleep`, `functioning`, `safety`, `social_support`, `threat_event`, `recent_episode`, etc.
- **Critical Invariant:**
  > **The LLM is strictly prohibited from generating numerical V2 features or clinical scores.**  
  > An observation such as `domain="sleep", value="poor"` is a qualitative semantic label, NOT a V2 numeric feature.
- **How to Test:** Run `pytest chatbot/tests/test_llm_extraction.py -v`.

---

### 3.10 Feature Mapper / Validator
- **Purpose:** Authoritative gatekeeper that deterministically converts candidate observations into V2 structured features.
- **Location:** [`chatbot/features/feature_mapper.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/features/feature_mapper.py)
- **Authoritative vs. Rejected Mappings:**
  - **Accepted Mappings (Authoritative binary indicators):**
    - `threat_event` (`"present"`, `"recent"`, `"yes"` -> `Threat_Event = 1.0`; `"absent"`, `"no"` -> `0.0`)
    - `recent_episode` (`"present"` -> `Recent_Episode = 1.0`; `"absent"` -> `0.0`)
  - **Rejected Mappings (Qualitative self-reports without mapping contracts):**
    - `sleep = "poor"` -> **REJECTED** (does not become `Sleep = 3.0` or `1.0`)
    - `mood = "low"` -> **REJECTED**
    - `stress = "high"` -> **REJECTED**
- **Precedence Rule:** Conversational observations **never** overwrite existing, authoritative check-in data already populated in `MedhaState.structured_features`.
- **How to Test:** Run `pytest chatbot/tests/test_feature_mapper.py -v`.

---

### 3.11 Question Engine
- **Purpose:** Deterministic policy for asking follow-up questions to fill missing core V2 structured features.
- **Location:** [`chatbot/engines/question_engine.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/engines/question_engine.py)
- **Question Bank:** Sourced from [`engine/QuestionEngine/questions.json`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/QuestionEngine/questions.json).
- **Priority and Cooldown:**
  - **Priority 1 (Safety):** `SA-01` to `SA-04` (targeted if `Safety` is missing).
  - **Priority 2 (Stress):** `ES-01` to `ES-06` (targeted if `Stress` is missing).
  - **Priority 3 (Functioning/Sleep):** `SF-01` (Sleep), `SF-02` (Functioning), `SE-01` (Social Support).
  - **Priority 4 (General Wellbeing):** `GW-01` (Mood / Wellbeing).
  - **Cooldown:** Questions enforce cooldown periods (default: 1 day) recorded in `QuestionRecord.cooldown_until`.
  - **Suppression:** If a feature is already addressed by a recent candidate observation, its question is suppressed.
- **How to Test:** Run `pytest chatbot/tests/test_question_engine.py -v`.

---

### 3.12 Conversation Summary
- **Purpose:** Maintains bounded, structured memory of ongoing context across turns without altering predictive features.
- **Location:** [`chatbot/summary/conversation_summary_engine.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/summary/conversation_summary_engine.py)
- **Categories:**
  `important_facts`, `current_concerns`, `recent_events`, `support_context`, `preferences`, `ongoing_topics`, `unresolved_topics`, `important_observations`.
- **Item Metadata:** Every `SummaryItem` stores `content`, `turn_index`, `status` (`active`, `superseded`, `unresolved`), `timestamp`, and `evidence`.
- **Rule:**
  > **Conversation summary is contextual memory, NOT clinical risk.**
- **How to Test:** Run `pytest chatbot/tests/test_conversation_summary.py -v`.

---

### 3.13 MEDHA V2 Adapter
- **Purpose:** Bridges `MedhaState` to the frozen MEDHA V2 pipeline contract.
- **Location:** [`chatbot/v2_adapter/medha_v2_adapter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/v2_adapter/medha_v2_adapter.py)
- **Responsibilities:**
  - Validates minimum schema requirements (`victim_id`, `timepoint`).
  - Constructs a pandas DataFrame matching the exact feature whitelist and column order expected by V2.
  - Converts missing features into `np.nan`.
  - Enforces `Voice_Available = 0.0` and `Text_Available = 0.0` when modalities are absent.
  - Calls `MedhaV2Pipeline.predict_v2(df)`.
  - Wraps results in `V2PredictionResult`.
- **How to Test:** Run `pytest chatbot/tests/test_v2_adapter.py -v`.

---

### 3.14 MEDHA V2 Pipeline (Frozen Boundary)
- **Purpose:** Authoritative clinical prediction engine.
- **Location:** [`engine/v2/medha_v2_pipeline.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/v2/medha_v2_pipeline.py)
- **Outputs Returned to Adapter:**
  - `Fusion_DDS_Prediction`: Continuous distress score (0.0 to 100.0) from XGBoost fusion.
  - `Temporal_Risk_Score`: Probability of risk escalation (0.0 to 1.0) from 7-step GRU.
  - `Future_Escalation_Flag`: Binary flag (`1` if `Temporal_Risk_Score >= threshold`, else `0`).
  - `Struct_Pred`, `Text_Pred`, `Voice_Pred`, `Behav_Pred`: Specialist model predictions.
- **Status:** **FROZEN.** No changes permitted under `engine/`.

---

## 4. End-to-End Message Lifecycle

### Scenario A: Normal Turn (Distress & Sleep Issues)
*User sends:* **"I've been feeling really overwhelmed lately and haven't been sleeping well."**

```text
1. UI (app.py) captures text input.
2. ConversationManager.process_message() initiates turn.
3. Safety Trigger evaluates message:
   - Evaluates for explicit emergency. Recognizes emotional distress/sleep issues without immediate threat.
   - Result: No alert emitted.
4. Voice & Behaviour Hooks:
   - Voice: No audio provided -> Voice_Available = 0.0, voice features remain None.
   - Behaviour: Captures turn duration and response delay telemetry.
5. Safety Gateway evaluates state:
   - No explicit danger flags -> Gatekeeper remains untriggered.
6. Text Adapter runs:
   - MuRIL processes text -> Text_Distress ≈ 0.68, Urgency ≈ 0.42, Negative_Affect ≈ 0.71.
   - Text_Available = 1.0.
7. Question Engine evaluates missing features:
   - Sleep is missing, but candidate observation for sleep is anticipated.
   - Selects highest priority missing feature off cooldown (e.g., Functioning: SF-02).
8. Summary Engine runs:
   - Records "User experiencing stress and sleep disturbance" under current_concerns.
9. LLM Provider (Gemini) generates response:
   - Empathetic acknowledgment + naturally weaves in SF-02 follow-up.
   - Extracts candidate observations: [domain="stress", value="high"], [domain="sleep", value="poor"].
10. Feature Mapper validates observations:
    - Rejects "stress" and "sleep" from numeric mapping (no authoritative schema).
    - Stores observations in MedhaState.candidate_observations.
11. TurnResult returned to UI:
    - User sees only empathetic response. Internal scores remain hidden.
```

---

### Scenario B: Emergency Turn (Immediate Danger / Safety Trigger)
*User sends:* **"My partner has a knife and is threatening to kill me right now."**

```text
1. UI captures message.
2. ConversationManager initiates turn.
3. Safety Trigger evaluates message:
   - Detects explicit, imminent threat to life.
   - Generates SafetyEvent(trigger_type="immediate_danger", evidence="threatening to kill me right now").
   - Dispatches event to AlertEngine.emit_safety_event().
   - Alert Engine delivers warning to backend caseworker queue.
   - Logs event to MedhaState.safety_events.
   - CONTINUES TO STEP 4 (Pipeline is NOT blocked).
4. Behaviour & Voice adapters update session metrics.
5. Safety Gateway evaluates state:
   - Detects conversational threat / danger.
   - TRIGGERS IMMEDIATE GATEWAY INTERCEPT.
   - Sets assistant response to deterministic crisis helpline referral.
6. Turn completes immediately:
   - UI renders: "⚠️ Safety Protocol Triggered" and crisis contact numbers.
   - Backend has already received the asynchronous SafetyEvent.
   - MedhaState preserves all evidence for audit.
```

---

## 5. Data Flow & Schema Specifications

### Summary of Major Data Structures

| Structure Name | Source File | Key Fields | User-Facing? | Safe to Modify? |
|---|---|---|---|---|
| `ChatMessage` | `chatbot/state/medha_state.py` | `role`, `content`, `timestamp`, `metadata` | Yes (Content only) | Yes (via State methods) |
| `MedhaState` | `chatbot/state/medha_state.py` | `structured_features`, `text_features`, `voice_features`, `behaviour_features`, `availability` | No | Yes (via State methods) |
| `CandidateObservation` | `chatbot/state/medha_state.py` | `domain`, `semantic_value`, `evidence`, `status`, `confidence` | No | No (bound by schema) |
| `SafetyEvent` | `chatbot/safety/safety_trigger.py` | `case_id`, `session_id`, `trigger_type`, `evidence`, `confidence`, `timestamp` | No (Backend alert) | No (Strict schema) |
| `TurnResult` | `chatbot/conversation_manager.py` | `session_id`, `turn_index`, `user_message`, `assistant_response`, `state`, `safety_result` | Partially (`assistant_response`) | No |
| `V2PredictionResult` | `chatbot/v2_adapter/medha_v2_adapter.py` | `current_dds`, `future_risk`, `struct_pred`, `text_pred`, `voice_pred`, `behav_pred` | No (Clinical backend) | No |

---

## 6. Feature Contract

All 62 feature names across the 4 modalities match canonical V2 definitions:

### 1. Structured Modality (42 Features)
- **Categorical (3):** `Case_Type`, `Case_Stage`, `Episode_Severity`.
- **Numeric (39):** `Checkin_Available`, `Mood`, `Stress`, `Sleep`, `Functioning`, `Safety`, `Social_Support_Checkin`, `Self_Reported_Wellbeing`, `Threat_Event`, `Upcoming_Hearing`, `Hearing_Completed`, `Investigation_Delay`, `Compensation_Delay`, `Relocation_Stress`, `Rehabilitation_Issue`, `Protection_Event`, `Family_Support`, `Social_Support`, `Therapist_Engagement`, `Access_To_Services`, `Stable_Housing`, `Other_Protective_Factors`, `Recent_Episode`, `Family_Reported_Episode`, `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Hours`, `Response_Delay_Deviation`, `Baseline_Response_Delay`, `Baseline_Engagement`, `Baseline_Checkin_Distress`, `Behaviour_Trend`, `Engagement_Trend`, `Diary_Available`, `Therapist_Observation_Available`, `Therapist_Observation_Score`.
- *Availability:* `struct_available = 1.0`.

### 2. Text Modality (5 Features)
- `Text_Distress`, `Fear`, `Threat_Context`, `Negative_Affect`, `Urgency`.
- *Availability:* `text_available = 1.0` if text analyzed, else `0.0`.

### 3. Voice Modality (5 Features)
- `Voice_Distress`, `Pause_Ratio`, `Speech_Rate_Deviation`, `Energy_Deviation`, `Acoustic_Indicator`.
- *Availability:* `voice_available = 1.0` if audio analyzed, else `0.0`.

### 4. Behaviour Modality (10 Features)
- `Missed_Checkin`, `Interaction_Frequency_7d`, `Session_Duration_Minutes`, `Engagement_Score`, `Engagement_Deviation`, `Response_Delay_Hours`, `Response_Delay_Deviation`, `Baseline_Response_Delay`, `Baseline_Engagement`, `Baseline_Checkin_Distress`.
- *Availability:* `behav_available = 1.0`.

---

## 7. Running the Chatbot

### Requirements
- **OS:** Windows / Linux / macOS
- **Python:** 3.10 to 3.14 (Verified on Python 3.14.4)
- **Primary Dependencies:** `streamlit`, `torch`, `transformers`, `xgboost`, `scikit-learn`, `pandas`, `numpy`, `google-genai`, `python-dotenv`, `librosa`, `soundfile`, `pytest`.

### Installation
Clone the repository and install requirements:
```bash
pip install -r requirements.txt
pip install streamlit google-genai
```

### Environment Setup
Create a `.env` file in the root directory:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
MEDHA_LLM_MODEL=gemini-3.1-flash-lite
```

### Starting the Application
Start the Streamlit web application:
```bash
python -m streamlit run app.py
```
Open `http://localhost:8501` in your browser.

### Using Text and Voice Input
1. **Text Input:** Type directly into the chat bar at the bottom.
2. **Microphone Input:** Under the sidebar "Voice Input", select "Microphone" and click the record button.
3. **File Upload:** Select "Upload File" in the sidebar to test `.wav` or `.mp3` audio files.
4. **New Conversation:** Click the "New Conversation" button in the sidebar to reset session state.

---

## 8. Developer Integration Guide

Developers integrating the chatbot as a library or backend service can instantiate components directly:

```python
from chatbot.conversation_manager import ConversationManager
from chatbot.engines.text_adapter import MedhaTextAdapter
from chatbot.engines.voice_adapter import MedhaVoiceAdapter
from chatbot.engines.behaviour_adapter import MedhaBehaviourAdapter
from chatbot.engines.question_engine import DeterministicQuestionEngine
from chatbot.features.feature_mapper import DeterministicFeatureMapper
from chatbot.safety.safety_gateway import DeterministicSafetyGateway
from chatbot.safety.safety_trigger import SafetyTrigger, MockAlertEngine
from chatbot.summary.conversation_summary_engine import ConversationSummaryEngine
from chatbot.llm.gemini_provider import GeminiProvider
from chatbot.v2_adapter.medha_v2_adapter import MedhaV2Adapter

# 1. Initialize dependencies
alert_engine = MockAlertEngine()
safety_trigger = SafetyTrigger(alert_engine=alert_engine)

manager = ConversationManager(
    text_adapter=MedhaTextAdapter(),
    voice_adapter=MedhaVoiceAdapter(),
    behaviour_adapter=MedhaBehaviourAdapter(),
    question_engine=DeterministicQuestionEngine(),
    feature_mapper=DeterministicFeatureMapper(),
    safety_gateway=DeterministicSafetyGateway(),
    safety_trigger=safety_trigger,
    summary_engine=ConversationSummaryEngine(),
    llm_provider=GeminiProvider()
)

# 2. Create an isolated session
session = manager.create_session(victim_id="VIC_999", session_id="sess_alpha_1")

# 3. Process conversation turn
turn_result = manager.process_message(
    session_id="sess_alpha_1",
    message="I feel threatened by someone watching my house.",
    audio_path=None,
    behaviour_data={"Session_Duration_Minutes": 3.5}
)

print(f"Assistant: {turn_result.assistant_response}")

# 4. Optional: Run frozen MEDHA V2 predictive pipeline
v2_adapter = MedhaV2Adapter()
prediction = v2_adapter.predict_from_state(turn_result.state)

if prediction:
    print(f"Current DDS Prediction: {prediction.current_dds}")
    print(f"Priority Triage Level: {prediction.priority_level}")
```

---

## 9. Extension Guide

### How to Safely Extend Components

| Goal | Where to Make Changes | Files NOT to Touch | Required Tests |
|---|---|---|---|
| **Add New LLM Provider** | Implement `LLMProviderProtocol` in `chatbot/llm/` | `conversation_manager.py` | Protocol compliance test |
| **Add Production Alert Engine** | Implement `AlertEngineProtocol` in `chatbot/safety/` | `engine/*`, `medha_state.py` | Delivery & failure isolation tests |
| **Add New Question** | Add entry to `engine/QuestionEngine/questions.json` | Model weights, V2 pipeline | `test_question_engine.py` |
| **Add Candidate Domain** | Add to `CANDIDATE_OBSERVATION_DOMAINS` in `observation_schema.py` | `engine/*` | Schema validation test |
| **Add Authoritative Feature Mapping** | Add rule in `DeterministicFeatureMapper.process_observations()` | `medha_v2_pipeline.py` | `test_feature_mapper.py` |
| **Add New UI** | Build on `manager.process_message()` | `chatbot/` internal logic | End-to-end integration test |

---

## 10. Safety and Privacy Rules

1. **No Clinical Diagnoses:** The chatbot must never tell a user they have PTSD, depression, or an anxiety disorder.
2. **No Risk Score Exposure:** The chatbot must never reveal DDS scores (e.g. "Your risk score is 74.2%") to the user.
3. **No Internal Reasoning Leaks:** Chain-of-thought, classification labels, and raw candidate observations must never be rendered to the chat interface.
4. **Safety Alerts are Strictly Backend:** `SafetyEvent` payloads are sent to caseworkers; they are never shown in the chat window.
5. **No Alert Engine Crashes:** If the external alert backend times out, the chat conversation must continue safely.
6. **No Storing Raw Audio Permanently:** Temporary audio files created during voice processing must be purged after turn completion.
7. **Secrets Isolation:** Never commit `.env` or hardcode API keys in code.

---

## 11. FROZEN MEDHA V2 — DO NOT MODIFY

The core machine learning engine inside `engine/` is **FROZEN**.

```text
╔═══════════════════════════════════════════════════════════════════╗
║                   FROZEN REPOSITORY BOUNDARY                      ║
║                                                                   ║
║  The following directories and files are FROZEN and must NEVER    ║
║  be modified, refactored, or retrained:                           ║
║                                                                   ║
║   - engine/v2/                                                    ║
║   - engine/models/                                                ║
║   - engine/text engine/                                           ║
║   - engine/voice_engine/                                          ║
║   - engine/behaviour_engine/                                      ║
║   - engine/Structured_risk_enigne/                                ║
║   - engine/fusion_engine/                                         ║
║   - engine/gru-temporal-risk/                                     ║
╚═══════════════════════════════════════════════════════════════════╝
```

All extensions and modifications must live in `chatbot/` or `app.py`.

---

## 12. Testing Guide

### Running Test Suites

Run the full chatbot test suite:
```bash
pytest chatbot/tests -v
```

Run the frozen engine verification test suite:
```bash
pytest engine/tests -v
```

Run specific component suites:
```bash
# Safety Trigger & Alert Engine
pytest chatbot/tests/test_safety_trigger.py -v

# Full End-to-End Integration
pytest chatbot/tests/test_end_to_end_integration.py -v

# V2 Adapter Contract
pytest chatbot/tests/test_v2_adapter.py -v
```

### Expected Results
- Chatbot tests: **146 passed**.
- Engine tests: **224 passed**.

---

## 13. Test Architecture

The test suite enforces the following safety invariants:
- `test_medha_state.py`: Verifies `None != 0.0`, schema immutability, serialization.
- `test_safety_trigger.py`: Verifies 16 safety edge cases (imminent danger, self-harm, negations, non-emergencies, multilingual, alert failure).
- `test_safety_gateway.py`: Verifies deterministic crisis intervention and helpline response.
- `test_feature_mapper.py`: Verifies rejection of unmapped qualitative observations.
- `test_v2_adapter.py`: Verifies longitudinal matrix construction and missing-modality handling.
- `test_end_to_end_integration.py`: Verifies multi-turn pipeline continuity through `MedhaV2Pipeline`.

---

## 14. Troubleshooting

| Problem / Error | Likely Cause | Resolution / What to Check |
|---|---|---|
| **Chatbot crashes on startup** | Missing `.env` or `GEMINI_API_KEY` | Check that `.env` exists in root and contains a valid API key. |
| **Microphone recording fails** | Insecure browser context | Streamlit audio input requires `http://localhost:8501` or HTTPS. |
| **Voice features remain `None`** | `librosa` or audio backend error | Verify `soundfile` and `librosa` are installed. Adapter safely sets `Voice_Available = 0.0`. |
| **Text features remain `None`** | MuRIL torch checkpoint loading failed | Verify PyTorch installation and ensure `engine/text engine/` models are present. |
| **LLM observations not mapped** | Expected behavior for qualitative scales | Feature mapper intentionally rejects qualitative strings (e.g. `sleep="poor"`) without an authoritative contract. |
| **Safety trigger not firing** | User statement was general distress | Safety trigger only fires on explicit, immediate danger or self-harm intent. Check `test_safety_trigger.py`. |

---

## 15. Known Limitations

1. **Mock Alert Engine:** The current repository implements `AlertEngineProtocol` and `MockAlertEngine`. Production alerts require implementing an HTTP/webhook backend.
2. **In-Memory Session Registry:** `ConversationManager._sessions` stores active sessions in memory. Server restarts clear active sessions unless persistent DB storage is attached.
3. **Voice ASR Dependency:** Spoken voice transcription in `app.py` relies on Gemini API. Offline ASR (e.g., Whisper) is not currently packaged.
4. **Qualitative-to-Numeric Gap:** Qualitative statements like "I feel horrible" intentionally do not update `Mood` in V2 because no clinical mapping formula exists.

---

## 16. Security and Production Considerations

Before deploying to a clinical or production environment:
- **Authentication:** Add role-based authentication (OAuth2 / SSO) to protect session access.
- **Data at Rest Encryption:** Encrypt session JSON and database state containing sensitive victim disclosures.
- **Production Alerting:** Replace `MockAlertEngine` with a redundant webhook service (e.g., PagerDuty, Twilio, or Hospital EHR integration).
- **Audit Logging:** Store emitted `SafetyEvent` payloads in an immutable, append-only security log.
- **Rate Limiting:** Implement token bucket rate limiting on `process_message` to protect against API exhaustion.

---

## 17. File and Directory Map

```text
MEDHA/
├── app.py                             # Streamlit Chat UI with Text and Voice input
├── requirements.txt                   # Core Python dependencies
├── .env.example                       # Environment configuration template
├── chatbot/
│   ├── conversation_manager.py        # Central turn and session orchestrator
│   ├── interfaces.py                  # Component protocols (LLM, Safety, Engines)
│   ├── engines/
│   │   ├── text_adapter.py            # Adapter to frozen MuRIL Text Engine
│   │   ├── voice_adapter.py           # Adapter to frozen acoustic Voice Engine
│   │   ├── behaviour_adapter.py       # Adapter for session telemetry
│   │   └── question_engine.py         # Deterministic question selection engine
│   ├── features/
│   │   └── feature_mapper.py          # Authoritative observation-to-feature mapper
│   ├── llm/
│   │   ├── gemini_provider.py         # Google Gemini LLM implementation
│   │   ├── mock_provider.py           # Offline mock provider for testing
│   │   ├── observation_schema.py      # Controlled semantic observation vocabulary
│   │   └── prompt_templates.py        # Trauma-informed system prompts
│   ├── safety/
│   │   ├── safety_gateway.py          # Deterministic user-facing crisis gateway
│   │   └── safety_trigger.py          # Non-blocking explicit safety alert trigger
│   ├── state/
│   │   └── medha_state.py             # Canonical MedhaState and feature registries
│   ├── summary/
│   │   ├── conversation_summary_engine.py # Contextual memory summarizer
│   │   └── summary_schema.py          # Summary data schema
│   ├── v2_adapter/
│   │   └── medha_v2_adapter.py        # Adapter to frozen MedhaV2Pipeline
│   ├── docs/                          # Architecture reports and specifications
│   └── tests/                         # Comprehensive pytest test suite
└── engine/                            # [FROZEN] Authoritative V2 ML Models & Pipelines
```

---

## 18. "Where Do I Make This Change?" Lookup Table

| I want to... | Look at File / Directory | Notes |
|---|---|---|
| **Adjust Chat UI layout or colors** | `app.py` | UI only; does not affect orchestration |
| **Change the LLM model or temperature** | `chatbot/llm/gemini_provider.py` | Defaults to `gemini-3.1-flash-lite` |
| **Add a new follow-up question** | `engine/QuestionEngine/questions.json` | Register question ID, cooldown, and priority |
| **Change system prompt phrasing** | `chatbot/llm/prompt_templates.py` | Maintain trauma-informed guardrails |
| **Add a new observation concept** | `chatbot/llm/observation_schema.py` | Must be in `CANDIDATE_OBSERVATION_DOMAINS` |
| **Connect a real Alert Engine (Webhook)** | `chatbot/safety/safety_trigger.py` | Implement `AlertEngineProtocol` |
| **Modify Crisis Hotline text** | `chatbot/safety/safety_gateway.py` | Update `_create_trigger_result()` |
| **Debug missing features in V2** | `chatbot/v2_adapter/medha_v2_adapter.py` | Inspect DataFrame construction |

---

## 19. Developer Rules (Do's and Don'ts)

### DO:
- **DO** preserve missingness (`None` and `np.nan`). Missing is never zero.
- **DO** verify that `engine/` remains completely unmodified.
- **DO** use existing protocols defined in `chatbot/interfaces.py`.
- **DO** write comprehensive tests in `chatbot/tests/` for every new component.
- **DO** ensure that backend safety alerts do not crash the user's conversational flow.

### DON'T:
- **DON'T** let the LLM calculate risk scores or diagnoses.
- **DON'T** map qualitative words (e.g. "poor sleep") to arbitrary numeric floats.
- **DON'T** trigger emergency alerts for normal emotional distress or past trauma.
- **DON'T** bypass `ConversationManager` to call specialist models directly.
- **DON'T** expose internal reasoning or model probabilities in the Chat UI.

---

## 20. Quick Start for a New Developer

### Onboarding Checklist
1. Read this guide ([`chatbot/docs/MEDHA_CHATBOT_DEVELOPER_GUIDE.md`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/docs/MEDHA_CHATBOT_DEVELOPER_GUIDE.md)).
2. Inspect `chatbot/state/medha_state.py` to understand feature representation.
3. Inspect `chatbot/conversation_manager.py` to trace turn execution.
4. Run tests to confirm local environment: `pytest chatbot/tests -v`.
5. Create `.env` and start the app: `python -m streamlit run app.py`.
6. Inspect `chatbot/safety/safety_trigger.py` and `chatbot/safety/safety_gateway.py` to understand safety handling.

### Recommended Reading Order
1. `chatbot/interfaces.py`
2. `chatbot/state/medha_state.py`
3. `chatbot/conversation_manager.py`
4. `chatbot/safety/safety_trigger.py`
5. `chatbot/safety/safety_gateway.py`
6. `chatbot/v2_adapter/medha_v2_adapter.py`

---

## 21. Architecture Invariants

Every developer working on this codebase must ensure the following 10 invariants remain strictly true:

1. **MEDHA V2 remains frozen:** Code and checkpoints under `engine/` are read-only.
2. **Missing != Zero:** Missing features remain `None` / `np.nan`. Never impute `0.0`.
3. **No LLM Feature Fabrication:** The LLM cannot invent numerical V2 features or clinical scores.
4. **Safety Trigger != Safety Gateway:** The trigger generates background alerts; the gateway intercepts conversations.
5. **Safety Trigger != Risk Engine:** The trigger only detects explicit, immediate safety crises.
6. **Pipeline Continuity:** Safety-triggered messages continue through the V2 predictive pipeline.
7. **No Alerts for General Distress:** Normal sadness and stress do not emit emergency alerts.
8. **Frontend Privacy:** The UI never exposes internal scores, model reasoning, or safety flags.
9. **Failure Isolation:** Alert Engine errors never crash the user's chat session.
10. **All Tests Pass:** All 146 chatbot tests and 224 engine tests must pass before merging code.
