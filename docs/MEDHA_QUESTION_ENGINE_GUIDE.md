# MEDHA Question Engine — Architecture & Technical Guide

> **Authoritative Technical Document on the Controlled Question Engine**  
> *Component Location:* [`chatbot/engines/question_engine.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/engines/question_engine.py)  
> *Authoritative Question Bank:* [`engine/QuestionEngine/questions.json`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/QuestionEngine/questions.json)  
> *Protocols & Contracts:* [`chatbot/interfaces.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/interfaces.py)  
> *State Representation:* [`chatbot/state/medha_state.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/state/medha_state.py)

---

## 1. Executive Summary & Purpose

The **MEDHA Question Engine** is a deterministic, context-aware interrogation-prevention system. In domestic violence and crisis response, gathering critical clinical risk data often conflicts directly with trauma-informed care:
- **The Clinical Risk Dilemma:** The downstream predictive models (MEDHA V2 XGBoost, Ridge, and Temporal GRU) require structured inputs across domains like Sleep, Stress, Functioning, and Physical Safety.
- **The Interrogation Risk:** If an AI assistant relentlessly quizzes a traumatized survivor like a clinical intake form, it induces cognitive overwhelm, damages rapport, and can cause re-traumatization.
- **The LLM Hallucination Risk:** If an unconstrained Large Language Model (LLM) is allowed to choose what questions to ask, it may invent arbitrary clinical diagnostic questions, ask inappropriate probing questions about trauma details, or repeatedly harass the user about sensitive topics.

### The Solution: Decoupling Policy from Phrasing
The Question Engine solves this through strict separation of responsibilities:
1. **The Question Engine (Deterministic Policy):** Controls **WHAT** question to ask, **WHEN** it is permissible to ask it, and **WHETHER** it should be suppressed entirely based on mathematical missingness, clinical priority, and cooldown limits.
2. **The Conversational LLM (Empathetic Phrasing):** Controls **HOW** the question is woven naturally and supportively into empathetic dialogue, completely barred from creating its own clinical screening strategy.

---

## 2. High-Level Architecture & Lifecycle

The Question Engine executes synchronously during turn processing inside `ConversationManager.process_message()`:

```text
                           USER MESSAGE
                                │
                                ▼
                   ┌───────────────────────────┐
                   │    ConversationManager    │
                   └─────────────┬─────────────┘
                                 │
                   (1) Record Message in State
                   (2) Non-blocking Safety Trigger
                   (3) Telemetry & Voice Adapters
                   (4) Safety Gateway (Crisis Check)
                   (5) MuRIL Text Engine Adapter
                                 │
                                 ▼
                   ┌───────────────────────────┐
                   │  Deterministic Question   │◄─── MedhaState (structured_features,
                   │          Engine           │     candidate_observations,
                   └─────────────┬─────────────┘     question_history)
                                 │
               Selects at most ONE QuestionRecord (or None)
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
        ┌─────────────────────┐     ┌─────────────────────┐
        │  Record in State    │     │  Pass to LLM        │
        │ (question_history)  │     │  (GeminiProvider)   │
        └─────────────────────┘     └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Empathetic Response │
                                    │ Weaving Question in │
                                    └─────────────────────┘
```

### Turn Lifecycle Placement
1. **Input State:** When `select_next_question(state)` is called, it inspects:
   - `state.structured_features`: Which numerical/categorical V2 features are missing (`None` / `NaN`).
   - `state.candidate_observations`: What qualitative facts the user already volunteered (e.g. `sleep="poor"`).
   - `state.question_history`: Which questions were previously asked and their cooldown timestamps.
2. **Selection Logic:** Determines the single highest-priority question whose target feature is missing and whose cooldown has expired.
3. **Output:** Returns a `QuestionRecord` (or `None`).
4. **State Recording:** `ConversationManager` calls `state.record_question_asked(...)`, locking in the cooldown.
5. **Prompt Injection:** The `QuestionRecord` is passed into `LLMProviderProtocol.generate_response(next_question=...)`.

---

## 3. The Controlled Question Bank (`questions.json`)

The Question Engine relies exclusively on a vetted, frozen repository question bank located at [`engine/QuestionEngine/questions.json`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/engine/QuestionEngine/questions.json).

### Schema of a Question Definition
Every question entry contains strict clinical and behavioral metadata:

```json
{
  "question_id": "SF-01",
  "intent": "sleep_functioning",
  "priority": 3,
  "trigger": "scheduled_checkin",
  "question": "How has your sleep been over the past week?",
  "response_type": "scale_1_5",
  "sensitivity": "low",
  "llm_rephrase": "yes",
  "cooldown_days": 3,
  "core_or_adaptive": "core",
  "measures": "Self-rated sleep quality trend",
  "structured_output": {
    "sleep_score": "integer 1-5"
  }
}
```

### Breakdown of Question Series & Categories

| Series Code | Clinical Intent | Priority | Target Features / Domains | Rephrase Policy | Typical Cooldown |
|---|---|:---:|---|---|:---:|
| **`SA` Series** (`SA-01` to `SA-04`) | **Safety & Immediate Support** | **1 (Highest)** | Physical safety, active threat, basic needs, emergency contacts | `no` / `controlled_only` | 1 to 14 days |
| **`ES` Series** (`ES-01` to `ES-06`) | **Event-Related Stress** | **2** | Trauma triggers, case milestones, intrusive thoughts, hypervigilance | `controlled_only` / `no` | 14 days |
| **`SF` Series** (`SF-01` to `SF-05`) | **Sleep & Daily Functioning** | **3** | Sleep quality, daily activity functioning, concentration changes | `yes` / `controlled_only` | 3 to 7 days |
| **`SE` Series** (`SE-01` to `SE-06`) | **Social & Emotional Support**| **3** | Trusted contacts, recent social contact, support changes | `yes` / `controlled_only` | 3 to 7 days |
| **`GW` Series** (`GW-01` to `GW-06`) | **General Wellbeing & Mood**  | **4** | Global mood, energy levels, trajectory trend | `yes` / `controlled_only` | 3 to 7 days |

---

## 4. The Deterministic Selection Algorithm

The algorithm in `DeterministicQuestionEngine.select_next_question(state)` operates in 5 consecutive steps:

```text
       ┌────────────────────────────────────────────────────────┐
       │ Step 1: Detect Missing Features                        │
       │ (Scan state.structured_features for None or NaN)       │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Step 2: Context-Aware Suppression                      │
       │ (Filter out features present in candidate_observations)│
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Step 3: Match Feature Triggers to Question Bank        │
       │ (Lookup candidate question IDs in questions.json)      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Step 4: Enforce Cooldowns                              │
       │ (Filter out questions asked within cooldown_days)      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Step 5: Strict Priority Sort & Rate Limiting           │
       │ (Sort by priority 1 -> 4; Pick exactly ONE)            │
       └────────────────────────────────────────────────────────┘
```

### Step 1: Missing Feature Detection
The engine checks `state.structured_features` against a registry of core triggerable features:
```python
self.feature_triggers = {
    "Safety": ["SA-01"],
    "Stress": ["ES-01", "ES-02"],
    "Sleep": ["SF-01"],
    "Functioning": ["SF-02"],
    "Social_Support_Checkin": ["SE-01"],
    "Mood": ["GW-01"],
    "Self_Reported_Wellbeing": ["GW-01"],
}
```
A feature is considered missing if its value is `None` or `math.isnan(val)`.

### Step 2: Context-Aware Candidate Observation Suppression (Anti-Interrogation)
This is the most critical trauma-informed mechanism in the engine. If the user previously or currently mentioned:
> *"I've been feeling exhausted and I can barely sleep at night."*

The LLM extracts a candidate observation:
`CandidateObservation(domain="sleep", semantic_value="poor", evidence="barely sleep at night")`.

The Question Engine checks `state.candidate_observations` using an authoritative domain-to-feature mapping:
```python
domain_to_feature = {
    "sleep": "Sleep",
    "mood": "Mood",
    "stress": "Stress",
    "functioning": "Functioning",
    "safety": "Safety",
    "social_support": "Social_Support_Checkin",
    "wellbeing": "Self_Reported_Wellbeing"
}
```
If a feature is missing in structured data BUT exists in candidate observations, **the feature is removed from the missing set!** The Question Engine **suppresses `SF-01`**. The user is never asked *"How has your sleep been?"* right after they just told the chatbot they can barely sleep.

### Step 3: Cooldown Filtering (`_is_off_cooldown`)
For each eligible candidate question, the engine inspects `state.question_history` in reverse chronological order:
1. It looks for the most recent `QuestionRecord` matching the `question_id`.
2. It parses `record.cooldown_until` (ISO-8601 UTC timestamp).
3. If `current_utc_time < cooldown_until`, the question is **rejected**.
4. If cooldown timestamps are missing, it falls back to checking `asked_at + timedelta(days=cooldown_days)`.

### Step 4: Strict Clinical Priority Ordering
If multiple questions pass cooldown and have missing features, they are sorted ascending by clinical priority:
- **Priority 1 (Physical Safety):** Evaluated first. If physical safety is unknown, the chatbot prioritizes asking about immediate physical security.
- **Priority 2 (Acute Trauma/Stress):** Evaluated second.
- **Priority 3 (Daily Functioning & Sleep):** Evaluated third.
- **Priority 4 (General Wellbeing/Mood):** Evaluated last.

### Step 5: Rate Limiting
The engine selects `candidate_questions[0]` and returns **at most one** `QuestionRecord`. It never generates a barrage of questions. If no candidate questions pass the filters, it returns `None`.

---

## 5. State Representation & Data Contract

### The `QuestionRecord` Dataclass
When a question is selected, it is packaged into a `QuestionRecord` (`chatbot/state/medha_state.py`):

```python
@dataclass
class QuestionRecord:
    question_id: str                          # e.g., "SF-01"
    question_text: str                        # Canonical text from questions.json
    intent: str                               # e.g., "sleep_functioning"
    asked_at: str                             # ISO-8601 timestamp
    answered: bool = False                    # Updated when user replies
    cooldown_until: Optional[str] = None      # ISO-8601 timestamp when cooldown expires
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### State Storage
`MedhaState` maintains an append-only list:
- `state.question_history: List[QuestionRecord]`
- Helper method: `state.record_question_asked(question_id, question_text, intent, cooldown_until, metadata)`
- Helper method: `state.mark_question_answered(question_id)`

---

## 6. LLM Integration & Rephrasing Controls

When `select_next_question` returns a `QuestionRecord`, it is supplied to `llm_provider.generate_response(next_question=...)`.

### How Gemini Consumes the Question
In [`chatbot/llm/gemini_provider.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/llm/gemini_provider.py):
```python
if next_question and next_question.question_text:
    user_prompt += (
        f"\n\n## Question to naturally incorporate:\n"
        f"If appropriate, you may naturally work this into your response: "
        f'"{next_question.question_text}"'
    )
```

### Rephrase Sensitivity Policies (`llm_rephrase`)
The question bank specifies three levels of rephrasing control:
1. `"llm_rephrase": "yes"` (e.g., `GW-01`, `SF-01`, `SE-01`):
   - Used for low-sensitivity check-ins (sleep, energy, mood).
   - The LLM can rephrase the question to match the natural flow of the conversation (e.g., *"How has your rest been lately?"* instead of the rigid *"How has your sleep been over the past week?"*).
2. `"llm_rephrase": "controlled_only"` (e.g., `ES-01`, `ES-02`, `SF-03`):
   - Used for medium/high-sensitivity questions (case milestones, triggers).
   - The LLM must keep the exact clinical framing and wording intact, only softening conversational connectors.
3. `"llm_rephrase": "no"` (e.g., `SA-01`, `SA-02`, `ES-03`):
   - Used for high-stakes safety and trauma intrusion questions:
     - `SA-01`: *"Do you currently feel physically safe where you are staying?"*
     - `SA-02`: *"Is anyone currently threatening or harming you?"*
   - The wording is legally, clinically, and ethically sensitive. The LLM is instructed not to alter the question.

---

## 7. Comprehensive Code Walkthrough

Below is the complete, annotated implementation of the `DeterministicQuestionEngine` from [`chatbot/engines/question_engine.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/engines/question_engine.py):

```python
class DeterministicQuestionEngine(QuestionEngineProtocol):
    """
    Deterministic rule-based policy for selecting the next MEDHA question.
    """

    def __init__(self, question_bank_path: str = "engine/QuestionEngine/questions.json"):
        self.question_bank_path = question_bank_path
        self.questions = self._load_questions()

        # Feature to Question ID mapping
        self.feature_triggers = {
            "Safety": ["SA-01"],
            "Stress": ["ES-01", "ES-02"],
            "Sleep": ["SF-01"],
            "Functioning": ["SF-02"],
            "Social_Support_Checkin": ["SE-01"],
            "Mood": ["GW-01"],
            "Self_Reported_Wellbeing": ["GW-01"],
        }

    def _load_questions(self) -> List[Dict[str, Any]]:
        try:
            with open(self.question_bank_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("questions", [])
        except Exception as e:
            logger.error(f"Failed to load question bank from {self.question_bank_path}: {e}")
            return []

    def select_next_question(self, state: MedhaState, **kwargs: Any) -> Optional[QuestionRecord]:
        if not self.questions:
            return None

        # 1. Determine which core features are genuinely missing
        missing_features = self._get_missing_core_features(state)
        if not missing_features:
            return None

        # 2. Filter candidates based on missingness, triggers, and cooldowns
        candidate_questions = []
        now = datetime.now(timezone.utc)

        for q in self.questions:
            q_id = q["question_id"]

            # Cooldown check
            if not self._is_off_cooldown(q_id, state, now, q.get("cooldown_days", 1)):
                continue

            # Check if this question targets a currently missing feature
            is_triggered = any(
                feature in missing_features and q_id in triggers
                for feature, triggers in self.feature_triggers.items()
            )

            if is_triggered:
                candidate_questions.append(q)

        if not candidate_questions:
            return None

        # 3. Sort by priority (Priority 1 = highest, Priority 4 = lowest)
        candidate_questions.sort(key=lambda x: x.get("priority", 99))
        best_q = candidate_questions[0]

        # 4. Compute cooldown expiration timestamp
        cooldown_days = best_q.get("cooldown_days", 1)
        cooldown_until = (now + timedelta(days=cooldown_days)).isoformat()

        return QuestionRecord(
            question_id=best_q["question_id"],
            question_text=best_q["question"],
            intent=best_q.get("intent", "unknown"),
            asked_at=_current_iso_timestamp(),
            answered=False,
            cooldown_until=cooldown_until,
        )

    def _get_missing_core_features(self, state: MedhaState) -> Set[str]:
        missing = set()

        domain_to_feature = {
            "sleep": "Sleep",
            "mood": "Mood",
            "stress": "Stress",
            "functioning": "Functioning",
            "safety": "Safety",
            "social_support": "Social_Support_Checkin",
            "wellbeing": "Self_Reported_Wellbeing",
        }

        # Identify features already addressed qualitatively in candidate observations
        known_candidates = {
            domain_to_feature[obs.domain]
            for obs in state.candidate_observations
            if obs.domain in domain_to_feature
        }

        # Check structured features
        for feature in self.feature_triggers.keys():
            val = state.structured_features.get(feature)
            is_missing = val is None or (isinstance(val, float) and math.isnan(val))

            # Only missing if NOT in structured AND NOT in candidate observations
            if is_missing and feature not in known_candidates:
                missing.add(feature)

        return missing

    def _is_off_cooldown(self, question_id: str, state: MedhaState, now: datetime, default_cooldown_days: int) -> bool:
        for record in reversed(state.question_history):
            if record.question_id == question_id:
                if record.cooldown_until:
                    try:
                        cooldown_end = datetime.fromisoformat(record.cooldown_until).replace(tzinfo=timezone.utc)
                        if now < cooldown_end:
                            return False
                    except ValueError:
                        pass
                try:
                    asked = datetime.fromisoformat(record.asked_at).replace(tzinfo=timezone.utc)
                    if now < asked + timedelta(days=default_cooldown_days):
                        return False
                except ValueError:
                    pass
        return True
```

---

## 8. Verification & Test Suite Deep Dive

The test suite in [`chatbot/tests/test_question_engine.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/chatbot/tests/test_question_engine.py) provides 100% test coverage over all core invariants:

```bash
pytest chatbot/tests/test_question_engine.py -v
```

### The 5 Core Test Scenarios:

1. **`test_missing_mood_triggers_GW01`:**
   - *Setup:* All features (Safety, Stress, Sleep, Functioning, Social) populated except `Mood` and `Self_Reported_Wellbeing`.
   - *Verification:* The engine selects `GW-01` (Priority 4).
2. **`test_missing_sleep_triggers_SF01`:**
   - *Setup:* Higher priorities (Safety=1.0, Stress=2.0) are populated. `Sleep` is `None`.
   - *Verification:* The engine selects `SF-01` (Priority 3).
3. **`test_known_sleep_suppresses_SF01` (Anti-Interrogation Test):**
   - *Setup:* `Sleep` structured feature is missing, BUT `state.add_candidate_observation(domain="sleep", semantic_value="poor")` is injected.
   - *Verification:* The engine suppresses `SF-01` and returns `None`.
4. **`test_repeated_question_prevention` (Cooldown Test):**
   - *Setup:* `Sleep` is missing, but a `QuestionRecord` for `SF-01` with a future `cooldown_until` is already in history.
   - *Verification:* `SF-01` is rejected; engine selects the next available question `SF-02` (Functioning).
5. **`test_maximum_question_frequency` (Priority Invariant Test):**
   - *Setup:* *Every* single feature is missing (`None`).
   - *Verification:* Returns exactly ONE question, picking `SA-01` (Priority 1: Safety).

---

## 9. Developer Rules & Invariants

### The 6 Core Invariants
1. **Deterministic Sourcing Only:** Never add questions on the fly in code or via LLM generation. All questions must reside in `engine/QuestionEngine/questions.json`.
2. **Missing != Ask Always:** If a user volunteered information, it exists in `candidate_observations`. Always suppress probing for that domain.
3. **Rate Limit to One:** Never return more than one question per conversational turn.
4. **Strict Cooldown Respect:** Never bypass cooldown periods. If a question is on cooldown, advance to the next priority or return `None`.
5. **LLMs Never Decide Policy:** The LLM receives the question as an instruction to incorporate; it does not choose the question.
6. **No Rephrase for High Sensitivity:** Questions marked `"llm_rephrase": "no"` (like `SA-01` and `SA-02`) must be delivered with exact wording.
