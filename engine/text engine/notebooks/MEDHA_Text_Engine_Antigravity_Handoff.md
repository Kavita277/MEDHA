# MEDHA Text Engine — Antigravity Handoff

## 1. Project Context

Project: **MEDHA**  
SIH Problem Statement: **SIH26094**

The MEDHA Text Engine is now trained and evaluated. The goal at this stage is **NOT to improve/retrain the model**.

The immediate goal is only to make the existing working Text Engine integration-ready.

Current architecture:

```text
Raw text
   ↓
Tokenizer
   ↓
MuRIL V2 → MEDHA
   ↓
5-label classification head
   ↓
5 continuous probabilities
   ↓
MEDHA Text Vector
```

Final Text Vector:

```text
text_distress
fear_signal
threat_context
negative_affect
urgency
```

---

# 2. Final MEDHA Text Model

The trained model is:

```text
MuRIL V2 → MEDHA
```

Model type:

```text
transformers.models.bert.modeling_bert.BertForSequenceClassification
```

Number of labels:

```text
5
```

Model labels:

```python
{
    0: "Distress",
    1: "Fear",
    2: "Threat",
    3: "Negative_Affect",
    4: "Urgency"
}
```

Final checkpoint:

```text
./medha_checkpoints/best_medha_model.pt
```

Best validation epoch:

```text
Epoch 5
```

Best validation Macro F1:

```text
0.9431
```

---

# 3. Training Configuration

```text
Batch size:       16
Learning rate:    2e-05
Weight decay:     0.01
Epochs:           5
Warmup ratio:     0.1
Warmup steps:     661
Total steps:      6610
Max grad norm:    1.0
AMP:              True
Primary metric:  Validation Macro F1
```

Positive class weights:

```text
Distress_Label           : 0.5782
Fear_Label               : 6.8859
Threat_Label             : 9.6175
Negative_Affect_Label    : 0.6192
Urgency_Label            : 13.7182
```

---

# 4. Validation Training Results

## Epoch 1

```text
Train Loss:          0.5837
Validation Loss:     0.2387
Validation Macro F1: 0.8465
Validation Micro F1: 0.8821
Macro Precision:     0.8166
Macro Recall:        0.9010
```

Per-label F1:

```text
Distress_Label       : 0.8847
Fear_Label           : 0.8582
Threat_Label         : 0.7870
Negative_Affect      : 0.9230
Urgency_Label        : 0.7797
```

## Epoch 2

```text
Train Loss:          0.2041
Validation Loss:     0.1912
Validation Macro F1: 0.9059
Validation Micro F1: 0.9233
Macro Precision:     0.9125
Macro Recall:        0.9049
```

Per-label F1:

```text
Distress_Label       : 0.9223
Fear_Label           : 0.8796
Threat_Label         : 0.9526
Negative_Affect      : 0.9407
Urgency_Label        : 0.8345
```

## Epoch 3

```text
Train Loss:          0.1563
Validation Loss:     0.1598
Validation Macro F1: 0.9201
Validation Micro F1: 0.9641
Macro Precision:     0.8958
Macro Recall:        0.9492
```

Per-label F1:

```text
Distress_Label       : 0.9813
Fear_Label           : 0.8887
Threat_Label         : 0.9472
Negative_Affect      : 0.9899
Urgency_Label        : 0.7932
```

## Epoch 4

```text
Train Loss:          0.1287
Validation Loss:     0.1799
Validation Macro F1: 0.9363
Validation Micro F1: 0.9719
Macro Precision:     0.9288
Macro Recall:        0.9461
```

Per-label F1:

```text
Distress_Label       : 0.9885
Fear_Label           : 0.8958
Threat_Label         : 0.9333
Negative_Affect      : 0.9918
Urgency_Label        : 0.8722
```

## Epoch 5 — BEST

```text
Train Loss:          0.1054
Validation Loss:     0.2010
Validation Macro F1: 0.9431
Validation Micro F1: 0.9755
Macro Precision:     0.9502
Macro Recall:        0.9370
```

Per-label F1:

```text
Distress_Label       : 0.9900
Fear_Label           : 0.9073
Threat_Label         : 0.9401
Negative_Affect      : 0.9930
Urgency_Label        : 0.8850
```

---

# 5. Optimized Thresholds

The final continuous probabilities must NOT be replaced by binary predictions.

Optimized thresholds:

```text
Distress_Label       : 0.24
Fear_Label           : 0.50
Threat_Label         : 0.45
Negative_Affect      : 0.29
Urgency_Label        : 0.72
```

Threshold tuning results:

```text
Distress_Label       Threshold: 0.24  F1: 0.9924
Fear_Label           Threshold: 0.50  F1: 0.9073
Threat_Label         Threshold: 0.45  F1: 0.9455
Negative_Affect      Threshold: 0.29  F1: 0.9932
Urgency_Label        Threshold: 0.72  F1: 0.8917
```

Important:

The thresholds are for binary decision interpretation only.

The actual Text Vector remains:

```text
continuous probability ∈ [0, 1]
```

---

# 6. FINAL MEDHA TEST RESULTS

```text
Macro F1:        0.9480
Micro F1:        0.9762
Macro Precision: 0.9478
Macro Recall:    0.9501
```

Per-label:

| Label | Precision | Recall | F1 |
|---|---:|---:|---:|
| Distress_Label | 0.9871 | 0.9931 | 0.9901 |
| Fear_Label | 0.8475 | 0.9259 | 0.8850 |
| Threat_Label | 0.9516 | 0.9762 | 0.9638 |
| Negative_Affect_Label | 0.9851 | 0.9950 | 0.9900 |
| Urgency_Label | 0.9679 | 0.8604 | 0.9110 |

---

# 7. LANGUAGE-WISE FINAL TEST RESULTS

Test dataset contains:

```text
English:    1517
Hindi:      1517
Hinglish:   1517
```

## English

```text
Samples:              1517
Macro F1:             0.9505
Macro Precision:      0.9456
Macro Recall:         0.9570
Label-wise Accuracy:  0.9844
Exact-match Accuracy: 0.9314
```

Per-label F1:

```text
Distress_Label       : 0.9872
Fear_Label           : 0.8717
Threat_Label         : 0.9568
Negative_Affect      : 0.9904
Urgency_Label        : 0.9464
```

## Hindi

```text
Samples:              1517
Macro F1:             0.9455
Macro Precision:      0.9465
Macro Recall:         0.9472
Label-wise Accuracy:  0.9852
Exact-match Accuracy: 0.9328
```

Per-label F1:

```text
Distress_Label       : 0.9913
Fear_Label           : 0.8848
Threat_Label         : 0.9791
Negative_Affect      : 0.9904
Urgency_Label        : 0.8818
```

## Hinglish

```text
Samples:              1517
Macro F1:             0.9479
Macro Precision:      0.9518
Macro Recall:         0.9462
Label-wise Accuracy:  0.9855
Exact-match Accuracy: 0.9347
```

Per-label F1:

```text
Distress_Label       : 0.9918
Fear_Label           : 0.8984
Threat_Label         : 0.9558
Negative_Affect      : 0.9893
Urgency_Label        : 0.9041
```

---

# 8. FINAL CONFUSION MATRIX VALUES

These are one-vs-rest confusion matrices for each of the five labels.

## Distress_Label

```text
TN = 1594
FP = 38
FN = 20
TP = 2899
```

## Fear_Label

```text
TN = 3921
FP = 90
FN = 40
TP = 500
```

## Threat_Label

```text
TN = 4022
FP = 25
FN = 12
TP = 492
```

## Negative_Affect_Label

```text
TN = 1713
FP = 42
FN = 14
TP = 2782
```

## Urgency_Label

```text
TN = 4190
FP = 10
FN = 49
TP = 302
```

Total label errors:

```text
340
```

---

# 9. CURRENT MODEL BEHAVIOR TESTS

The existing inference was tested successfully.

Example:

### English — calm

```text
I feel calm today and things are going well.
```

Output:

```text
Distress_Label       0.002
Fear_Label           0.002
Threat_Label         0.002
Negative_Affect      0.002
Urgency_Label        0.001
```

All predictions: NO.

### English — fear

```text
I am scared about what might happen to my family.
```

Output:

```text
Distress_Label       0.023
Fear_Label           0.997
Threat_Label         0.025
Negative_Affect      0.019
Urgency_Label        0.023
```

Prediction:

```text
Fear = YES
```

### Hindi

```text
मुझे डर लग रहा है कि आगे क्या होगा और मैं अपने परिवार को लेकर चिंतित हूँ।
```

Output:

```text
Distress_Label       0.012
Fear_Label           0.995
Threat_Label         0.025
Negative_Affect      0.010
Urgency_Label        0.017
```

Prediction:

```text
Fear = YES
```

### Hinglish

```text
Mujhe darr lag raha hai aur tension ho rahi hai ki mere parivar ke saath kya hoga.
```

Output:

```text
Distress_Label       0.003
Fear_Label           0.989
Threat_Label         0.617
Negative_Affect      0.016
Urgency_Label        0.006
```

Predictions:

```text
Fear = YES
Threat = YES
```

---

# 10. IMPORTANT DATASET NOTE

The dataset may contain imperfect/synthetic labels.

For the current project stage, **do not redesign or retrain the model because of individual suspicious examples**.

The current model has strong test metrics and the immediate task is integration.

Do not spend time overanalyzing individual errors unless specifically requested.

---

# 11. TEXT ENGINE INTEGRATION REQUIREMENT

The existing Text Engine already works:

```text
Raw text
↓
MuRIL model
↓
5 MEDHA outputs
↓
Text Vector
```

Do NOT rebuild this.

Do NOT retrain.

Do NOT change the checkpoint.

Do NOT change the tokenizer.

Do NOT change the classification head.

Do NOT change preprocessing unless absolutely required for the wrapper.

Do NOT change probability calculation.

The only required change is a thin integration wrapper.

---

# 12. REQUIRED INPUT FORMAT

The Text Engine must accept:

```json
{
  "victim_id": "V0104",
  "session_id": "S001",
  "timestamp": "2026-08-30T11:30:00",
  "text": "I am scared about the upcoming hearing.",
  "language": "en",
  "source": "question_engine"
}
```

Fields:

```text
victim_id
    Metadata identifying the victim.

session_id
    Metadata identifying the interaction/session.

timestamp
    Metadata timestamp.

text
    The ONLY field passed into MuRIL.

language
    Metadata only.
    Supported values:
        en
        hi
        hinglish

source
    Metadata only.
    Supported values:
        question_engine
        diary
        chatbot
        voice_transcript
```

Critical rule:

```text
language must NOT be passed separately into MuRIL.
source must NOT be passed into MuRIL.
victim_id must NOT be passed into MuRIL.
session_id must NOT be passed into MuRIL.
timestamp must NOT be passed into MuRIL.
```

Only:

```text
input["text"]
```

goes into the existing inference function.

---

# 13. REQUIRED OUTPUT FORMAT

Return:

```json
{
  "victim_id": "V0104",
  "session_id": "S001",
  "timestamp": "2026-08-30T11:30:00",
  "language": "en",
  "source": "question_engine",
  "text_available": 1,
  "text_vector": {
    "text_distress": 0.81,
    "fear_signal": 0.92,
    "threat_context": 0.88,
    "negative_affect": 0.76,
    "urgency": 0.73
  }
}
```

The five probabilities must come directly from the existing inference.

Metadata must be passed through unchanged:

```text
victim_id
session_id
timestamp
language
source
```

The five-value vector is the only ML output:

```text
text_distress
fear_signal
threat_context
negative_affect
urgency
```

---

# 14. MULTI-SOURCE SUPPORT

The same function must support:

## Question Engine

```json
{
  "victim_id": "V001",
  "session_id": "S001",
  "timestamp": "2026-08-30T12:00:00",
  "text": "I am scared about the upcoming hearing.",
  "language": "en",
  "source": "question_engine"
}
```

## Diary

```json
{
  "victim_id": "V001",
  "session_id": "S002",
  "timestamp": "2026-08-30T12:10:00",
  "text": "आज मुझे बहुत चिंता हो रही है।",
  "language": "hi",
  "source": "diary"
}
```

## Chatbot

```json
{
  "victim_id": "V001",
  "session_id": "S003",
  "timestamp": "2026-08-30T12:20:00",
  "text": "Mujhe darr lag raha hai ki aage kya hoga.",
  "language": "hinglish",
  "source": "chatbot"
}
```

## Whisper voice transcript

```json
{
  "victim_id": "V001",
  "session_id": "S004",
  "timestamp": "2026-08-30T12:30:00",
  "text": "मुझे डर लग रहा है कि आगे क्या होगा।",
  "language": "hi",
  "source": "voice_transcript"
}
```

All four sources must call the SAME existing inference function.

The source must not change model behavior.

---

# 15. MISSING TEXT

Do not generate a fake vector when text is missing.

Do NOT do:

```python
{
    "text_distress": 0,
    "fear_signal": 0,
    "threat_context": 0,
    "negative_affect": 0,
    "urgency": 0
}
```

Instead, empty/missing text should produce a clear validation error.

The normal Question Engine flow should call the Text Engine only when actual free text exists.

If `language` is absent, safe optional handling is acceptable.

---

# 16. THRESHOLD RULE

Do not convert the vector to binary values.

Wrong:

```text
text_distress = 1
fear_signal = 1
...
```

Correct:

```text
text_distress = 0.81
fear_signal = 0.92
...
```

Thresholds are only used when interpreting probabilities as YES/NO:

```text
Distress       >= 0.24
Fear           >= 0.50
Threat         >= 0.45
Negative Affect>= 0.29
Urgency        >= 0.72
```

The downstream MEDHA fusion system needs the continuous vector.

---

# 17. REQUIRED REGRESSION TEST

Before modifying the integration code:

1. Select 3–5 known texts.
2. Run the CURRENT direct inference.
3. Save the five probabilities.

Example structure:

```python
baseline_vectors = {
    "text_1": [...],
    "text_2": [...],
    "text_3": [...],
}
```

Then implement the wrapper.

Run:

```text
JSON input
↓
extract text
↓
existing inference
↓
Text Vector
↓
attach metadata
```

Compare the old and new five probabilities.

Expected:

```python
np.allclose(old_vector, new_vector, atol=1e-6)
```

or an appropriately small floating-point tolerance.

If probabilities meaningfully differ:

**STOP. Do not modify the model to make them match. Investigate the wrapper/inference change.**

---

# 18. WHAT ANTIGRAVITY MUST INSPECT

Before changing code, identify:

### 1. Model loading

Find the cell/function that loads:

```python
medha_model
```

or the equivalent trained model.

### 2. Tokenizer loading

Find the existing tokenizer initialization.

### 3. Existing inference

Find the function that currently accepts raw text and runs:

```text
text
↓
tokenizer
↓
model
↓
logits
↓
sigmoid/probabilities
```

### 4. Five probabilities

Find where the five model probabilities are produced.

### 5. Text Vector

Find where the five probabilities are assembled into the current Text Vector.

Only after locating these should the wrapper be added.

---

# 19. DESIRED CODE ARCHITECTURE

The final architecture should be approximately:

```python
def existing_text_inference(text):
    # EXISTING WORKING CODE
    # DO NOT REWRITE
    ...
    return existing_vector
```

Then a thin wrapper:

```python
def medha_text_engine(request):
    text = request.get("text")

    if not text or not str(text).strip():
        raise ValueError("Text is required and cannot be empty.")

    vector = existing_text_inference(text)

    return {
        "victim_id": request.get("victim_id"),
        "session_id": request.get("session_id"),
        "timestamp": request.get("timestamp"),
        "language": request.get("language"),
        "source": request.get("source"),
        "text_available": 1,
        "text_vector": {
            "text_distress": vector[0],
            "fear_signal": vector[1],
            "threat_context": vector[2],
            "negative_affect": vector[3],
            "urgency": vector[4]
        }
    }
```

IMPORTANT:

The above is a conceptual wrapper.

**Do not blindly replace the existing inference function.**

Use the actual existing function/vector representation from the notebook.

If the existing inference already returns a dictionary, preserve it and map its existing values into the required output.

---

# 20. REQUIRED TESTS

Test A — Existing direct inference:

```text
raw text
↓
existing inference
↓
five-value vector
```

It must continue working exactly as before.

Test B — New integration inference:

```text
JSON
↓
wrapper
↓
existing inference
↓
metadata + five-value vector
```

Test C — English.

Test D — Hindi.

Test E — Hinglish.

Test F — source = question_engine.

Test G — source = diary.

Test H — source = chatbot.

Test I — source = voice_transcript.

Test J — missing/empty text should raise a clear error.

Test K — regression comparison between direct and wrapped inference.

---

# 21. IMPORTANT NON-GOALS

Do NOT:

- retrain the model
- change the architecture
- replace MuRIL
- change tokenizer
- change checkpoint
- change classification head
- change thresholds
- convert probabilities to binary outputs
- add new ML outputs
- add diagnosis
- add suicide risk
- add depression score
- add sleep score
- add safety score
- add event type
- add case stage
- add event date
- add contextual metadata into the ML input
- create fake vectors for missing text

This task is strictly an **integration wrapper task**.

---

# 22. FINAL SUCCESS CONDITION

The task is complete when:

```text
Question Engine free-text
        \
Diary --------\
Chatbot ------- > SAME MEDHA TEXT ENGINE
Whisper -------/
        ↓
Existing MuRIL inference
        ↓
Same 5-value Text Vector
        ↓
Standardized JSON output
```

And:

```text
OLD:
raw text → existing inference → Vector A

NEW:
JSON → wrapper → existing inference → Vector B
```

satisfies:

```text
Vector A ≈ Vector B
```

for all regression test texts.

The model's predictions must not be meaningfully changed.

---

# 23. FINAL TEXT ENGINE CONTRACT

### Input

```json
{
  "victim_id": "string",
  "session_id": "string",
  "timestamp": "ISO-8601 timestamp",
  "text": "string",
  "language": "en | hi | hinglish",
  "source": "question_engine | diary | chatbot | voice_transcript"
}
```

### Output

```json
{
  "victim_id": "string",
  "session_id": "string",
  "timestamp": "ISO-8601 timestamp",
  "language": "en | hi | hinglish",
  "source": "question_engine | diary | chatbot | voice_transcript",
  "text_available": 1,
  "text_vector": {
    "text_distress": 0.0,
    "fear_signal": 0.0,
    "threat_context": 0.0,
    "negative_affect": 0.0,
    "urgency": 0.0
  }
}
```

The values inside `text_vector` are the **existing model probabilities** and must remain continuous values in `[0, 1]`.

---

# 24. Bottom Line for Antigravity

**Do not touch the trained model.**

Find the existing working raw-text inference.

Wrap it.

```text
INPUT JSON
   ↓
request["text"]
   ↓
EXISTING INFERENCE — unchanged
   ↓
EXISTING FIVE PROBABILITIES — unchanged
   ↓
STANDARD JSON WRAPPER
   ↓
OUTPUT
```

The integration layer is the only thing that needs to be added.
