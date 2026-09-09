# MEDHA V2 — FINAL CHATBOT ARCHITECTURE & IMPLEMENTATION SPECIFICATION

## 1. Purpose

The MEDHA chatbot is the conversational interface through which a victim can interact with MEDHA periodically.

The chatbot is **not** the intelligence that calculates distress or future escalation risk.

Its responsibilities are:

1. Hold a natural conversation.
2. Accept free-form text.
3. Ask controlled, useful questions.
4. Collect selected structured information when appropriate.
5. Detect explicit safety-related statements and route them through a governed safety pathway.
6. Send genuine text to the existing MEDHA Text Engine.
7. Maintain the current MEDHA state for the session.
8. Construct/update the V2 input DataFrame.
9. Call the existing `MedhaV2Pipeline.predict_v2()` interface.
10. Present an appropriate conversational response without exposing raw internal risk scores to the victim.

The V2 pipeline itself remains unchanged. Its documented interface is `MedhaV2Pipeline.predict_v2(df)`, operating on the longitudinal DataFrame containing the required structured, text, voice and behaviour features. fileciteturn12file0L35-L61

---

# 2. FINAL HIGH-LEVEL ARCHITECTURE

```text
                         ┌──────────────────────┐
                         │      VICTIM          │
                         │                      │
                         │ Text / Voice /       │
                         │ Check-in interaction │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      CHAT UI         │
                         │                      │
                         │ Text input           │
                         │ Optional voice       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ SAFETY GATEWAY       │
                         │                      │
                         │ Deterministic safety │
                         │ trigger handling     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │     CONVERSATION MANAGER     │
                    │                              │
                    │ Session state                │
                    │ Conversation history         │
                    │ Question history             │
                    │ Context                      │
                    │ Current known information    │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌───────────────────┐        ┌────────────────────┐
          │    LLM LAYER      │        │ QUESTION POLICY    │
          │                   │        │                    │
          │ Understand user  │        │ Decide what to ask │
          │ Generate natural  │        │ next               │
          │ responses         │        │                    │
          │ Extract candidate │        │ Controlled rules   │
          │ information       │        │                    │
          └─────────┬─────────┘        └─────────┬──────────┘
                    │                            │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ FEATURE MAPPER +          │
                    │ VALIDATOR                 │
                    │                           │
                    │ Candidate information     │
                    │ → approved V2 fields      │
                    │                           │
                    │ Reject unsupported fields │
                    │ Validate values/types     │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │       MEDHA STATE         │
                    │                           │
                    │ Current observations      │
                    │ Previous observations     │
                    │ Text features             │
                    │ Voice features            │
                    │ Behaviour features        │
                    │ Structured values         │
                    │ Availability flags        │
                    │ Timepoint                 │
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
       ┌─────────────┐     ┌─────────────┐    ┌─────────────┐
       │ TEXT ENGINE │     │ VOICE ENGINE │    │ BEHAVIOUR   │
       │             │     │             │    │ ENGINE      │
       │ Existing    │     │ Existing    │    │ Existing    │
       │ V2 text     │     │ V2 voice    │    │ V2 behaviour│
       │ inference   │     │ inference   │    │ features    │
       └──────┬──────┘     └──────┬──────┘    └──────┬──────┘
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │     V2 INPUT ADAPTER      │
                    │                           │
                    │ Exact V2 DataFrame        │
                    │ contract                  │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │ MedhaV2Pipeline           │
                    │ .predict_v2(df)            │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
             Current DDS                  Future Risk
```

---

# 3. THE MOST IMPORTANT DESIGN RULE

## The chatbot does NOT replace MEDHA V2.

The existing V2 system already consists of:

| Component | Algorithm | Input |
|---|---|---:|
| Structured DDS | XGBoost | 42 features |
| Text DDS | Ridge | 5 features |
| Voice DDS | Ridge | 5 features |
| Behaviour DDS | Ridge | 10 features |
| Fusion | XGBoost | 8 features |
| Future Risk | GRU | 7 × 57 features |

These are frozen V2 components. fileciteturn13file0L10-L24

The chatbot sits **above these models**.

Therefore:

```text
BAD:

Chatbot
   ↓
LLM
   ↓
"Risk = 83%"
```

and:

```text
BAD:

Chatbot
   ↓
LLM
   ↓
New ML risk model
```

Instead:

```text
Chatbot
   ↓
Collect / understand information
   ↓
Existing MEDHA engines
   ↓
V2 Data Contract
   ↓
predict_v2()
   ↓
Current DDS + Future Risk
```

---

# 4. WHAT THE CHATBOT ACTUALLY DOES

The chatbot has six major responsibilities.

## 4.1 Conversation

The victim should be able to say things naturally.

Examples:

```text
"I've been feeling terrible today."

"I couldn't sleep last night."

"I'm really scared about tomorrow."

"I don't want to talk about it."

"Everything about the case is stressing me out."

"They contacted me again."

"I don't know what I'm supposed to do."
```

The chatbot should understand these statements conversationally.

It should **not force every interaction into a questionnaire**.

---

# 5. LLM RESPONSIBILITIES

The LLM is allowed to:

### A. Understand conversational language

For example:

```text
"I haven't slept properly for three days."
```

can be understood as information concerning sleep.

### B. Generate natural responses

Example:

```text
User:
"I've been feeling overwhelmed lately."

Bot:
"I'm sorry things have been feeling so overwhelming.
Would you like to tell me what has been weighing on you the most?"
```

### C. Extract candidate information

For example:

```text
User:
"I can't concentrate on college because I keep thinking about the case."
```

Candidate information:

```json
{
  "functioning": "impaired",
  "case_related_stress": "present"
}
```

### D. Generate ordinary conversational wording

The LLM can make the chatbot sound natural.

---

# 6. WHAT THE LLM MUST NOT DO

The LLM must NOT:

- calculate DDS
- calculate future escalation probability
- invent a safety score
- diagnose depression/PTSD/etc.
- invent model features
- invent numerical V2 values
- directly modify arbitrary V2 fields
- decide which clinical risk model to use
- override the V2 pipeline
- decide that someone is "lying"
- create a new risk model
- replace therapist judgement

This separation is especially important because the existing Text Engine contract explicitly says that its five continuous outputs must come from the existing model and that no new ML outputs should be added. fileciteturn14file2L241-L265

---

# 7. QUESTION ENGINE

The chatbot needs a **simple question policy**, not a complicated AI question-selection model.

The purpose is:

> "What useful information should MEDHA ask about next?"

The question system should avoid turning every conversation into the same questionnaire.

## Final question categories

### CORE

These are the main recurring wellbeing areas:

1. Mood
2. Sleep
3. Stress
4. Functioning
5. Social connection

These are supported by the broader MEDHA specification as the primary comparable wellbeing variables. fileciteturn14file5L737-L750

### CONTEXTUAL

Ask only when relevant:

6. Case-related stress
7. Threat/contact concerns
8. Legal/hearing-related stress
9. Financial/compensation stress
10. Relocation/housing/livelihood concerns

### EVENT FOLLOW-UP

If the system already knows about a recent event:

11. Follow-up after important event
12. Follow-up after therapist-recorded episode
13. Follow-up after major case development

### SAFETY

14. Safety-related check when triggered by an appropriate condition.

Safety is a separate governed pathway, not another normal chatbot feature.

---

# 8. HOW QUESTION SELECTION WORKS

We do NOT need an ML question selector.

Use:

```text
Current state
     +
What has already been asked
     +
What information is missing
     +
Recent event/context
     +
Recent conversation
     ↓
Simple question policy
     ↓
Select next question
```

Example:

```text
Today:
Mood known
Stress known
Sleep unknown
No recent event

→ Ask about sleep
```

Another example:

```text
User mentions:
"Tomorrow's hearing is making me extremely anxious."

→ Existing conversation already contains legal/hearing context.

→ Ask a short follow-up about how the hearing is affecting them.

```

Another:

```text
Recent therapist-recorded event exists

→ Temporarily ask:
"How have you been feeling since that happened?"
```

The question policy should prevent unnecessary repetition.

---

# 9. CONTROLLED QUESTION BANK

The safest implementation is:

```text
Question Intent
       ↓
Approved Question Templates
       ↓
Optional LLM wording adaptation
       ↓
Victim
```

For normal conversational questions, the LLM can make wording natural.

For sensitive/safety questions, use fixed approved wording.

This prevents the LLM from inventing inappropriate clinical questions.

---

# 10. WHAT INFORMATION SHOULD THE CHATBOT COLLECT?

This is one of the most important decisions.

The chatbot should **NOT attempt to collect all 42 structured V2 features**.

That would turn the chatbot into a 42-feature medical questionnaire.

Instead, it should naturally collect a small set of meaningful wellbeing/context information.

## Primary conversational information

### 1. Mood

Examples:

```text
"I've been feeling low."

"I feel okay today."

"I've been miserable lately."
```

---

### 2. Stress

Examples:

```text
"Everything is stressing me out."

"I've been under a lot of pressure."

"I feel overwhelmed."
```

---

### 3. Sleep

Examples:

```text
"I barely slept last night."

"I've been sleeping normally."

"I keep waking up."
```

---

### 4. Functioning

Examples:

```text
"I can't concentrate on college."

"I haven't been able to do my work."

"I managed to get everything done today."
```

---

### 5. Social connection

Examples:

```text
"I don't really talk to anyone anymore."

"My family has been supportive."

"I've been avoiding everyone."
```

---

### 6. Feeling of safety

Examples:

```text
"I don't feel safe going home."

"I feel safe here."

"I'm worried they might come back."
```

This can activate the separate safety pathway.

It should **not automatically become a numeric safety prediction**.

---

### 7. Case-related stress

Examples:

```text
"The investigation is stressing me out."

"I keep thinking about the case."

"The case isn't bothering me today."
```

---

### 8. Threat/event context

Examples:

```text
"They called me again."

"Someone threatened me."

"Nothing has happened recently."
```

---

### 9. Important upcoming event

Examples:

```text
"I have a hearing tomorrow."

"I'm worried about the next court date."

"The compensation decision is next week."
```

This should be stored as contextual information **only if the V2 data contract actually has an approved corresponding structured field**.

The chatbot must not invent a new V2 ML field just because the conversation contains useful context.

---

# 11. VERY IMPORTANT: NATURAL LANGUAGE ≠ AUTOMATIC NUMERIC FEATURE

We should NOT do this:

```text
"I feel terrible"

        ↓

Mood = 9.4
```

unless the exact V2 training semantics explicitly define that mapping.

Likewise:

```text
"I'm stressed"

        ↓

Stress = 8.2
```

would be an invented transformation if the training semantics don't support it.

Therefore the chatbot will use:

```text
Natural language
      ↓
Semantic interpretation
      ↓
Approved feature/value mapping
      ↓
Validator
      ↓
V2 field
```

The exact numerical/category mappings must be taken from the authoritative V2 feature configuration/preprocessor rather than invented by the LLM.

The V2 Data Contract explicitly permits missing structured values and states that the preprocessor handles them. fileciteturn13file7L431-L470

This means we **do not need to force the chatbot to fill every feature**.

---

# 12. STRUCTURED FEATURE STRATEGY

Every possible V2 structured feature belongs to one of these categories:

### A. Automatically available

Provided by the existing system/database.

Examples may include case/profile information.

### B. Passively generated

Generated by behaviour tracking.

### C. Generated by existing specialist engines

Text and voice features.

### D. Conversationally collectable

Information that can legitimately be obtained from a check-in.

### E. Therapist/system-only

Information that should not be inferred from casual conversation.

### F. Missing

If information is unavailable, leave it missing.

This is critical because the V2 contract explicitly distinguishes **column existence** from **modality availability** and permits missing values. fileciteturn13file7L431-L456

---

# 13. TEXT PIPELINE

Every genuine chatbot message should be eligible to go through the existing Text Engine.

```text
Chatbot message
      ↓
Existing Text Engine
      ↓
5 existing probabilities
```

The five canonical outputs are:

```text
Text_Distress
Fear
Threat_Context
Negative_Affect
Urgency
```

The V2 architecture documents these exact five inputs to the Text specialist. fileciteturn13file4L251-L287

The existing Text Engine handoff also explicitly supports:

```text
source = chatbot
```

and says chatbot, diary, Question Engine and Whisper transcripts should use the same inference function. fileciteturn14file3L478-L536

Therefore:

```text
Chatbot
   ↓
"text"
   ↓
Existing Text Engine
   ↓
5-value text vector
```

No second chatbot NLP model is required.

---

# 14. TEXT ENGINE OUTPUT

The chatbot integration should preserve:

```json
{
  "text_available": 1,
  "text_vector": {
    "text_distress": "...",
    "fear_signal": "...",
    "threat_context": "...",
    "negative_affect": "...",
    "urgency": "..."
  }
}
```

The values remain continuous model probabilities.

The Text Engine documentation specifically requires the five probabilities to remain continuous rather than being converted into binary values. fileciteturn14file1L152-L182

---

# 15. VOICE

Voice should be **optional**.

If the user presses the microphone button:

```text
Audio
  │
  ├──→ Whisper
  │       ↓
  │    Transcript
  │       ↓
  │    Text Engine
  │
  └──→ Existing Voice Engine
          ↓
      5 Voice Features
```

The existing V2 Voice specialist consumes:

```text
Voice_Distress
Pause_Ratio
Speech_Rate_Deviation
Energy_Deviation
Acoustic_Indicator
```

These are part of the frozen V2 architecture. fileciteturn13file4L262-L287

### But:

Voice is **optional for the first chatbot implementation**.

The chatbot must work completely without it.

---

# 16. BEHAVIOUR

The chatbot should not ask the victim to manually enter behavioural metrics.

The application should collect them passively where possible.

Examples:

```text
Response delay
Interaction frequency
Session duration
Engagement
Missed check-ins
```

The V2 Behaviour specialist uses 10 behaviour features and produces `Behav_Pred`. fileciteturn13file4L280-L287

Therefore:

```text
Chat interaction
      ↓
App behaviour tracking
      ↓
Behaviour features
      ↓
Existing Behaviour Engine
```

The user should not see this happening as a questionnaire.

---

# 17. DIARY

Diary/journal should be **optional**, not required for chatbot operation.

If a diary entry exists:

```text
Diary text
    ↓
Existing Text Engine
```

If there is no diary entry:

```text
No diary
    ≠
Bad mood
    ≠
Risk
```

Therefore the chatbot never penalizes a victim for not writing.

The Text Engine integration already supports `source = diary` separately from `source = chatbot`. fileciteturn14file1L68-L124

---

# 18. SAFETY GATEWAY

This needs to be separate from ordinary conversation.

The chatbot should have a deterministic safety gateway:

```text
User message
     ↓
Safety Gateway
     │
     ├── No explicit safety concern
     │          ↓
     │     Normal conversation
     │
     └── Safety concern detected
                ↓
        Safety response/pathway
                ↓
        Human professional review
```

Important:

## The gateway is NOT a suicide prediction model.

It should not output:

```text
Suicide risk = 87%
```

It should not infer:

```text
sadness → suicide
```

It should identify when a conversation contains an explicit safety-related concern requiring the governed pathway.

The MEDHA specification explicitly separates general distress from safety and states that safety escalation requires human intervention. fileciteturn12file5L621-L642

---

# 19. WHAT THE CHATBOT SHOULD SAY ABOUT RISK

The victim-facing chatbot should NOT normally say:

```text
Your DDS is 78.
```

or:

```text
Your future escalation risk is 83%.
```

These are internal system outputs intended for the MEDHA professional workflow.

The chatbot should instead respond naturally.

For example:

```text
"Thank you for telling me that. It sounds like today has been particularly difficult. Would you like to talk a little more about what has been weighing on you?"
```

The therapist/professional interface can receive the appropriate system-level information.

---

# 20. MEDHA STATE

We need one central state object.

Conceptually:

```text
MEDHA_STATE
│
├── victim_id
├── session_id
├── timepoint
│
├── conversation
│
├── current_observations
│
├── structured_features
│
├── text_features
│
├── voice_features
│
├── behaviour_features
│
├── availability
│
├── recent_events
│
├── question_history
│
└── previous_predictions
```

The state is **not a new ML model**.

It is simply the application's current representation of what MEDHA knows.

---

# 21. CONVERSATION MANAGER

The Conversation Manager is responsible for:

### Session management

```text
session_id
timestamp
victim_id
```

### History

Stores recent conversation context.

### Question history

Tracks:

```text
question_id
last asked
answer
```

This prevents repetitive questioning.

### Current information

Tracks what is already known.

Example:

```text
Mood → known
Sleep → unknown
Stress → known
Functioning → unknown
```

The Question Policy can then decide:

```text
Ask sleep
```

instead of asking mood again.

---

# 22. FEATURE MAPPER

The Feature Mapper is a critical safety boundary.

The LLM should produce **candidate information**, not directly modify the V2 DataFrame.

Example:

```text
User:
"I haven't been sleeping properly for days."
```

LLM:

```json
{
  "candidate": "sleep",
  "semantic_value": "poor",
  "evidence": "I haven't been sleeping properly for days."
}
```

Then:

```text
Feature Mapper
       ↓
Approved V2 mapping
       ↓
Validator
       ↓
Structured state
```

This prevents:

```text
LLM hallucination
      ↓
wrong V2 feature
      ↓
wrong model input
```

---

# 23. VALIDATOR

The Validator checks:

### Feature name

Is this a real approved V2 feature?

### Value

Is the value allowed?

### Type

Numeric/categorical/etc.

### Range

If the feature has a numeric range, is the value valid?

### Source

Where did this information come from?

```text
therapist
system
chatbot
text_engine
voice_engine
behaviour_engine
```

### Confidence

If the semantic extraction is ambiguous, do not force a value.

Instead:

```text
unknown / missing
```

This is much safer than guessing.

---

# 24. FINAL V2 ADAPTER

The adapter's only job is to convert MEDHA state into the exact DataFrame expected by V2.

```text
MEDHA STATE
     ↓
V2 ADAPTER
     ↓
Longitudinal DataFrame
     ↓
predict_v2()
```

The V2 Data Contract requires:

```text
Victim_ID
Timepoint
42 structured features
5 text features
5 voice features
10 behaviour features
Text_Available
Voice_Available
```

with the relevant missing-value behavior defined by the contract. fileciteturn13file7L420-L470

---

# 25. NEVER CREATE FAKE MODALITY DATA

If the victim does not provide voice:

```text
Voice_Available = 0
```

Do NOT do:

```text
Voice_Distress = 0
Pause_Ratio = 0
...
```

because "no voice" does not mean "no distress."

The V2 contract explicitly requires modality availability to be represented separately from feature-column existence. fileciteturn13file7L431-L456

Likewise:

```text
No chatbot message
```

does not mean:

```text
Text distress = 0
```

---

# 26. CALLING V2

Once enough information has been collected:

```text
MEDHA_STATE
     ↓
V2_ADAPTER
     ↓
input_df
     ↓
MedhaV2Pipeline.predict_v2(input_df)
```

The pipeline then performs:

```text
Structured → Structured XGBoost
Text → Text Ridge
Voice → Voice Ridge
Behaviour → Behaviour Ridge
                 ↓
        Fusion XGBoost
                 ↓
           Current DDS

History
   ↓
7-timestep GRU
   ↓
Future Risk
```

This is the actual frozen V2 processing flow. fileciteturn12file0L35-L61

---

# 27. OUTPUTS WE CARE ABOUT

The pipeline returns:

```text
Fusion_DDS_Prediction
Temporal_Risk_Score
Temporal_Available
Future_Escalation_Flag
```

along with specialist outputs and availability fields.

The API handoff explicitly documents these outputs. fileciteturn14file6L807-L833

The chatbot itself does not reinterpret these into a new ML score.

---

# 28. CONVERSATION LOOP

The final chatbot loop is:

```text
              USER MESSAGE
                    │
                    ▼
             Safety Gateway
                    │
                    ▼
          Conversation Manager
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
      LLM Understanding   Question Policy
          │                   │
          └─────────┬─────────┘
                    ▼
             Candidate Info
                    │
                    ▼
           Feature Mapper
                    │
                    ▼
                Validator
                    │
                    ▼
              MEDHA State
                    │
          ┌─────────┼──────────┐
          │         │          │
          ▼         ▼          ▼
       Text       Voice     Behaviour
       Engine     Engine     Engine
          │         │          │
          └─────────┼──────────┘
                    ▼
                V2 Adapter
                    │
                    ▼
            predict_v2()
                    │
             ┌──────┴──────┐
             ▼             ▼
         Current DDS    Future Risk
             │             │
             └──────┬──────┘
                    ▼
            Conversation Manager
                    │
                    ▼
             Natural Response
                    │
                    ▼
                  USER
```

---

# 29. EXAMPLE — NORMAL CONVERSATION

### User

```text
I've been feeling terrible today.
```

### Chatbot

Understands:

```text
possible low mood/distress
```

Sends actual text to:

```text
Existing Text Engine
```

The Text Engine generates its five existing probabilities.

The chatbot may respond:

```text
"I'm sorry you're having a difficult day. Would you like to tell me what has been making today especially difficult?"
```

No fake structured numerical values are created.

---

# 30. EXAMPLE — MULTI-INFORMATION MESSAGE

### User

```text
I haven't slept properly for three days and I can't concentrate on college because I keep thinking about the case.
```

Candidate information:

```text
Sleep → poor
Functioning → impaired
Case-related stress → present
```

The actual text simultaneously goes through:

```text
Text Engine
```

Therefore the same message provides:

```text
Conversation understanding
+
Text specialist signals
```

This is exactly what we want.

---

# 31. EXAMPLE — HEARING

### User

```text
I'm really scared about tomorrow's hearing.
```

The system can identify:

```text
Fear/context
Upcoming important event
Case-related stress
```

The actual sentence goes through the Text Engine and therefore contributes to:

```text
Fear
Threat_Context
Text_Distress
Negative_Affect
Urgency
```

where supported by the existing model.

The Text Engine contract explicitly supports chatbot messages and preserves the same five-value output regardless of source. fileciteturn14file3L508-L536

The chatbot can then ask a short contextual follow-up.

---

# 32. EXAMPLE — SAFETY

### User

```text
I don't feel safe going home.
```

Flow:

```text
Message
   ↓
Safety Gateway
   ↓
Safety concern
   ↓
Governed safety response
   ↓
Human/professional pathway
```

It should NOT become:

```text
Safety = 9.2
```

and the LLM should not autonomously decide an emergency intervention.

---

# 33. EXAMPLE — USER DOES NOT WANT TO ANSWER

### User

```text
I don't want to talk about it.
```

The chatbot should respect this.

It should not repeatedly ask:

```text
Why?
Why?
Why?
```

Instead:

```text
"That's okay. We don't have to talk about it right now. We can check in about how you're doing more generally."
```

The system retains the information as unavailable rather than fabricating an answer.

---

# 34. WHAT WE ARE NOT BUILDING

To keep this implementation realistic, the chatbot will NOT contain:

### ❌ New risk model

No chatbot-specific XGBoost/RNN/etc.

### ❌ Vector database

Not necessary for the first implementation.

### ❌ Complex agent system

No autonomous multi-agent clinical reasoning.

### ❌ Autonomous clinical reasoning

LLM cannot decide clinical conclusions.

### ❌ 42-question questionnaire

The chatbot does not attempt to fill every V2 structured feature conversationally.

### ❌ ML question selector

Simple controlled rules are enough.

### ❌ New fusion engine

V2 already has the frozen fusion model.

### ❌ New temporal model

V2 already has the frozen GRU.

### ❌ New Text Engine

Use the existing Text Engine.

### ❌ New Voice model

Use existing Voice Engine if voice is enabled.

### ❌ LLM-generated numerical risk

Never.

### ❌ Diagnosis

Never.

### ❌ Lie detection

Never.

---

# 35. MVP FEATURES — FINAL DECISION

## MUST HAVE

| Feature | Decision |
|---|---|
| Chat UI | YES |
| Text conversation | YES |
| Conversation Manager | YES |
| Session management | YES |
| Conversation history | YES |
| Controlled question policy | YES |
| Question history/repetition control | YES |
| LLM natural conversation | YES |
| Candidate information extraction | YES |
| Feature Mapper | YES |
| Validator | YES |
| MEDHA state | YES |
| Safety Gateway | YES |
| Existing Text Engine | YES |
| Behaviour tracking | YES |
| V2 Adapter | YES |
| `predict_v2()` integration | YES |
| Current DDS | YES |
| Future Risk | YES |
| Missing modality handling | YES |

---

# 36. OPTIONAL FEATURES

These should only be added after the basic chatbot works.

| Feature | Priority |
|---|---|
| Voice input | HIGH |
| Whisper integration | HIGH |
| Existing Voice Engine | HIGH |
| Diary | MEDIUM |
| Persistent long-term conversation history | MEDIUM |
| Therapist event-triggered questions | MEDIUM |
| Case-stage-aware questions | MEDIUM |
| Conversation summaries | MEDIUM |

---

# 37. REMOVE FROM MVP

| Feature | Decision |
|---|---|
| Vector database | REMOVE |
| Complex memory architecture | REMOVE |
| ML question selector | REMOVE |
| New fusion model | REMOVE |
| New risk model | REMOVE |
| Autonomous clinical agent | REMOVE |
| Complex evidence graph | REMOVE |
| Complex confidence propagation | REMOVE |
| 42-feature conversational questionnaire | REMOVE |
| LLM-generated safety assessment | REMOVE |
| LLM-generated risk scores | REMOVE |

---

# 38. FINAL COMPONENT LIST

The chatbot backend should therefore contain approximately these components:

```text
chatbot/
│
├── conversation_manager
│
├── llm/
│   ├── conversation
│   └── extraction
│
├── question_engine/
│   ├── question_policy
│   ├── question_bank
│   └── question_history
│
├── safety/
│   └── safety_gateway
│
├── features/
│   ├── feature_mapper
│   └── validator
│
├── state/
│   └── medha_state
│
├── engines/
│   ├── text_adapter
│   ├── voice_adapter
│   └── behaviour_adapter
│
└── v2/
    └── medha_v2_adapter
```

The exact filenames can be decided during implementation.

---

# 39. FINAL DATA FLOW

The complete production-oriented MVP becomes:

```text
                    VICTIM
                       │
                       ▼
                  CHAT UI
                       │
                       ▼
                SAFETY GATEWAY
                       │
                       ▼
             CONVERSATION MANAGER
                       │
              ┌────────┴────────┐
              ▼                 ▼
             LLM          QUESTION POLICY
              │                 │
              └────────┬────────┘
                       ▼
               FEATURE MAPPER
                       │
                       ▼
                  VALIDATOR
                       │
                       ▼
                  MEDHA STATE
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    TEXT ENGINE    VOICE ENGINE   BEHAVIOUR
    Existing V2    Existing V2    Existing V2
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 V2 ADAPTER
                       │
                       ▼
            MedhaV2Pipeline
                .predict_v2()
                       │
               ┌───────┴────────┐
               ▼                ▼
          CURRENT DDS       FUTURE RISK
               │                │
               └───────┬────────┘
                       ▼
              THERAPIST SYSTEM
```

---

# 40. THE KEY ARCHITECTURAL PRINCIPLE

The easiest way to remember the chatbot architecture is:

```text
LLM = TALK
Question Engine = ASK
Feature Mapper = TRANSLATE
Validator = PROTECT
MEDHA State = REMEMBER
Existing Engines = ANALYSE
V2 Pipeline = PREDICT
Therapist = DECIDE
```

That separation is the final design.

---

# 41. WHY THIS IS THE RIGHT DESIGN FOR MEDHA V2

The existing V2 artifacts are explicitly frozen and the reproducibility documentation states that the canonical model/preprocessor files must not be modified. The documented pipeline is initialized through `MedhaV2Pipeline()` and inference is performed through `predict_v2()`. fileciteturn12file4L467-L519

Therefore the chatbot should **adapt to V2 rather than modify V2**.

The Text Engine already has a standardized integration contract supporting `chatbot` as a source and requires the same existing inference function for chatbot text. fileciteturn14file3L478-L536

The V2 contract also explicitly allows missing structured/text/voice information rather than requiring the chatbot to manufacture values. fileciteturn13file7L431-L470

So the architecture remains simple:

```text
                 CHATBOT
                    │
          ┌─────────┴─────────┐
          │                   │
      CONVERSATION         DATA
          │               COLLECTION
          │                   │
          └─────────┬─────────┘
                    ▼
               MEDHA STATE
                    │
                    ▼
             EXISTING V2
                    │
                    ▼
              PREDICTIONS
```

# 42. FINAL FREEZE DECISION

Before coding, I would freeze the chatbot specification as follows:

### The chatbot IS:

- conversational
- multilingual-capable through the existing text pipeline
- context-aware
- adaptive
- lightweight
- controlled
- connected to the existing Text Engine
- optionally connected to Voice
- connected to Behaviour tracking
- connected to the frozen V2 pipeline
- human-in-the-loop

### The chatbot IS NOT:

- a new ML model
- a therapist
- a diagnostic system
- a suicide prediction model
- a risk calculator
- a replacement for V2
- a replacement for the therapist
- a 42-feature questionnaire
- an autonomous clinical agent

### FINAL ARCHITECTURE

```text
USER
 ↓
CHAT UI
 ↓
SAFETY GATEWAY
 ↓
CONVERSATION MANAGER
 ├── LLM
 ├── QUESTION POLICY
 └── CONVERSATION HISTORY
 ↓
FEATURE MAPPER
 ↓
VALIDATOR
 ↓
MEDHA STATE
 ├── Existing Text Engine
 ├── Existing Voice Engine (optional)
 └── Existing Behaviour Engine
 ↓
V2 ADAPTER
 ↓
MedhaV2Pipeline.predict_v2()
 ↓
 ├── Current DDS
 └── Future Risk
 ↓
THERAPIST / PROFESSIONAL SYSTEM
```

**This is the architecture I recommend we code. We should not redesign the V2 models while implementing it.**

The next coding phase should begin with the **interfaces/contracts between these components**, especially `MEDHA_STATE → V2_ADAPTER → predict_v2()`, and the exact approved feature mappings. We should verify the authoritative V2 feature configuration before writing any mapper that converts conversational information into structured values.