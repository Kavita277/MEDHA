# MEDHA Question Engine (NLP Interface)

The Question Engine is an interactive component designed to dynamically generate, ask, and parse questions based on the victim's current state and risk profile. It acts as the interactive "agent" interacting with the victim during check-ins.

## Codebase File Directory
- **`nlp_interface.py`**: The core Natural Language Processing logic for interacting with the user or parsing their free-text responses.
- **`medha_state.py`**: Manages the state-machine logic for the conversation flow.
- **`patient_context.py`**: Stores and retrieves the current context of the victim to tailor the questions appropriately.
- **`questions.json`**: A structured database of predefined questions categorized by trauma type, risk level, or stage of the legal process.
- **`model_adapters.py`**: Adapters connecting the Question Engine to underlying LLMs or NLP models.
- **`session_demo.py`**: A sandbox script to run a mock interactive session.
- **`test_*.py`**: A comprehensive testing suite for the NLP interface and state integration.

## Integration Guide (For Backend Developers)

The Question Engine is highly stateful and operates differently from the passive "Risk Engines". It does not feed directly into the `compute_fusion()` mathematical pipeline in a single pass. Instead, it interacts with the user to *generate* the unstructured text that is eventually fed into the **Text Engine**.

**Current Status:** The engine is built and functional, but a standardized webhook/socket integration for a frontend chat UI is **yet to be built**.

When connecting this to a chat interface, integration will look conceptually like this:
```python
# [PROPOSED INTEGRATION - Webhooks/Sockets Yet To Be Built]
from QuestionEngine.nlp_interface import get_next_question, process_answer
from QuestionEngine.patient_context import load_patient

patient = load_patient("Victim_X")

# Get a dynamically selected question to ask the user
question_text = get_next_question(patient)
# -> Send to Frontend UI

# ... Wait for user response ...

# Process the response
state_update = process_answer(patient, user_response_text)
# -> The 'user_response_text' can also now be sent to the Text Engine for distress scoring!
```
