# MEDHA V2 CHATBOT — STEP 10
## BEHAVIOUR INTEGRATION REPORT

**Author**: Antigravity Chatbot Team
**Component**: Behaviour Engine Adapter & Orchestration
**Date**: September 9, 2026
**Status**: `STEP 10 STATUS: PASS`

---

## 1. ARCHITECTURE INTEGRATION

The frozen MEDHA V2 Behaviour Engine calculates continuous risk outputs based on user behaviour (engagement, delays, missing check-ins). It operates securely inside the `MedhaV2Pipeline.predict_v2()` method.

To integrate this into the chatbot layer **without duplicating inference or fabricating numbers**, we implemented the following architecture:

```text
Authoritative Behaviour Input (Analytics / Logs)
         ↓
Conversation Manager (process_message)
         ↓
MedhaBehaviourAdapter (Validates keys and types)
         ↓
MedhaState.behaviour_features (Safe Storage)
         ↓
MedhaV2Adapter (Constructs V2 DataFrame)
         ↓
MedhaV2Pipeline.predict_v2() (Natively runs Behaviour ML Inference)
```

## 2. DOUBLE-INFERENCE CHECK

**Is the Behaviour Engine called directly by the adapter?**
No.

**Is it called internally by `MedhaV2Pipeline.predict_v2()`?**
Yes. Lines 154-167 of `engine/v2/medha_v2_pipeline.py` natively run `self.behav_preproc.transform` and `self.behav_model.predict`.

**How was duplicate inference prevented?**
The `MedhaBehaviourAdapter` does NOT import, load, or invoke the joblib/pkl model files. It functions purely as a data validation and type-checking layer. It ensures that incoming metrics conform to the 10 canonical V2 Behaviour Features and safely maps them to `MedhaState`. The state is then consumed by the standard V2 pipeline, which handles inference natively.

## 3. COMPLIANCE CHECKLIST

- [x] **Zero V2 Modifications**: The `engine/` directory was completely untouched.
- [x] **No Duplicate Inference**: The chatbot adapter maps state data; `predict_v2()` executes the inference.
- [x] **No 0.0 Imputation**: Missing metrics remain `None` and translate to `np.nan`, safely triggering the V2 Behaviour Engine's fitted imputer.
- [x] **No Semantic Extraction**: The LLM is structurally decoupled from `BEHAVIOUR_FEATURES`. It cannot generate or manipulate continuous behavioural metrics (verified by `test_6_no_conversational_fabrication`).
- [x] **Authoritative Schemas Only**: The adapter strictly whitelists the exact 10 features defined in `v2_behaviour_dds_features.json`.

## 4. VERIFICATION RESULTS

- Chatbot test suite (`chatbot/tests/`): **106 passed**, 0 failed.
- Frozen V2 regression suite (`engine/tests/`): **224 passed**, 0 failed.
- Total Tests: **330 passed**.

All integration constraints were perfectly satisfied. The chatbot is now capable of correctly marshalling longitudinal behaviour metrics into the V2 predictive engine without violating any clinical safety rules.

**STEP 10 STATUS: PASS**
