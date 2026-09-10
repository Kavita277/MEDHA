# STEP 12: CHATBOT ↔ BACKEND INTEGRATION — IMPLEMENTATION SUMMARY

## 1. Objective

Step 12 wires the MEDHA Streamlit frontend (`app.py`) to the FastAPI backend
rather than having it import the `ConversationManager` directly.

**Before Step 12:**
```
Streamlit ──(direct import)──► ConversationManager  [in-memory, no auth]
```

**After Step 12:**
```
Streamlit ──(HTTP)──► FastAPI Backend ──► ConversationManager ──► PostgreSQL
                          ↓ also
                       Event ingestion (raw behaviour events per turn)
```

The Streamlit app is now a thin API client. The backend is the single source of truth.

---

## 2. What Changed

### `app.py`

The entry point was fully rewritten:

| Before | After |
|--------|-------|
| `ConversationManager` imported directly | `MedhaBackendClient` calls the API |
| `victim_id="V_UI"` hardcoded | Real authenticated user identity from JWT |
| No auth, no login screen | Login screen enforced; JWT stored in `st.session_state` |
| State lost on app restart | State persisted in PostgreSQL via backend session |
| No event emission | `BackendEventEmitter` submits events per turn |
| Audio: local voice adapter + features | Audio: local transcription + features forwarded via metadata |

### New `backend_client/` Package

| File | Description |
|------|-------------|
| [`backend_client/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/__init__.py) | Package exports |
| [`backend_client/client.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/client.py) | HTTP client for all backend API calls |
| [`backend_client/event_emitter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/event_emitter.py) | Idempotent raw event construction + submission |
| [`backend_client/exceptions.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/exceptions.py) | Typed exception hierarchy |

---

## 3. Unchanged (Zero Modifications)

- `chatbot/` — all frozen: `ConversationManager`, `MedhaState`, all engines
- `engine/` — all frozen V2 models, weights, scalers, pipelines
- `backend/services/chatbot_service.py` — unchanged
- `backend/api/v1/` — no new endpoints needed (Step 12 only adds a client, not an endpoint)
- Frozen V2 Behaviour Specialist (Step 10 still blocked)

---

## 4. Architecture After Step 12

```
User
  │  browser / localhost:8501
  ▼
Streamlit app.py
  ├── Login: POST /api/v1/auth/login → JWT stored in st.session_state
  ├── Session: POST /api/v1/sessions → backend session + DB record
  ├── Chat:    POST /api/v1/chat/sessions/{id}/message → response
  ├── Events:  POST /api/v1/events/batch → raw behaviour events
  │
  │  HTTP (httpx, synchronous)
  ▼
FastAPI Backend  (localhost:8000)
  ├── Auth: JWT validation, RBAC
  ├── SessionService: MedhaState restore from PostgreSQL
  ├── ChatbotService: ConversationManager (per-request, stateless)
  │   └── ConversationManager.process_message()
  │       ├── Safety Gateway
  │       ├── Text Engine (MuRIL)
  │       ├── Behaviour Adapter (Session_Duration_Minutes etc.)
  │       ├── Voice Adapter (features forwarded via metadata)
  │       ├── Question Engine
  │       └── LLM Provider (Gemini)
  ├── Event Ingestion: raw_events table (Step 9)
  └── PostgreSQL: sessions, chat_messages, raw_events, ...
```

---

## 5. Login Flow

1. Streamlit renders login form.
2. User submits credentials → `POST /api/v1/auth/login`
3. On 200: `access_token`, `user_role`, `user_name` stored in `st.session_state`
4. `POST /api/v1/sessions` → creates backend session, returns UUID and `session_identifier`
5. `BackendEventEmitter` created with the new session UUID
6. Chat page rendered

**Error handling:**
- HTTP 401 → `MedhaAuthError` → "Login failed" shown in UI
- HTTP 403 → `MedhaForbiddenError` → "Account access denied" shown
- `ConnectError` → `MedhaConnectionError` → backend URL shown to user

---

## 6. Chat Turn Flow

For each turn:

1. User types or speaks
2. If audio: transcribed locally via Gemini ASR; Voice adapter run locally for feature values
3. `MedhaBackendClient.send_message()` called with `message`, `behaviour_data`, optional `metadata`
4. Backend: `ChatbotService.process_message()` runs full pipeline → response
5. Response displayed in Streamlit
6. `BackendEventEmitter.emit_turn()` submits `chat_message_sent` (and `session_start` on turn 1)

---

## 7. Voice Audio Handling

Audio transcription and voice feature extraction run **locally inside the Streamlit process**.
The transcribed text and voice feature values are forwarded to the backend via the `metadata`
field of the chat payload. No binary audio is uploaded to the backend.

```python
metadata["voice_features"] = {
    "Voice_Distress": 0.34,
    "Pause_Ratio": 0.12,
    ...
}
```

The backend `ChatbotService` already handles `metadata` as a pass-through in `process_message()`.

---

## 8. Session Lifecycle

| Action | Streamlit | Backend |
|--------|-----------|---------|
| App load, not logged in | Show login page | — |
| Login success | Store token | — |
| First render after login | Create session | `POST /sessions` → DB record |
| Each chat turn | Call API | Process + update snapshot |
| Emit events | BackendEventEmitter | `POST /events/batch` |
| "New Conversation" | `emit_session_end` → `end_session` → `create_session` | `POST /sessions/{id}/end` |
| "Sign Out" | Clear token + session state | `POST /sessions/{id}/end` (best-effort) |
| Browser refresh | Token lost → login again | Session in DB survives (orphaned until GC) |

---

## 9. Event Emission

Events are submitted per turn via `BackendEventEmitter`:

| Turn | Events Emitted |
|------|---------------|
| 1st turn | `session_start` + `chat_message_sent` |
| Subsequent turns | `chat_message_sent` only |
| "New Conversation" | `session_end` |
| "Sign Out" | `session_end` (best-effort) |

**Idempotency:** Event IDs are UUIDv5 derived from `(MEDHA_NS, session_id, turn_index, event_type)`.
Re-renders of the Streamlit page never double-submit the same event.

**Non-blocking:** `BackendEventEmitter` has `silent=True` by default. Event ingestion failures
never interrupt the chat flow.

---

## 10. Backend URL Configuration

```bash
# Default (both servers running locally)
MEDHA_BACKEND_URL=http://localhost:8000

# Or in .env
MEDHA_BACKEND_URL=https://medha-backend.example.com
```

---

## 11. Test Coverage

| Suite | Tests | Result |
|-------|-------|--------|
| `backend_client/tests/test_backend_client.py` | **19 passed** | ✅ |
| `backend/tests/test_step12_integration.py` | **13 passed** | ✅ |
| Full regression (`backend/tests/` — 102 tests) | **102 passed** | ✅ |

**Total across all backend suites: 115 tests, 0 failures.**

---

## 12. Files Created

| File | Description |
|------|-------------|
| [`backend_client/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/__init__.py) | Package init |
| [`backend_client/client.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/client.py) | HTTP client |
| [`backend_client/event_emitter.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/event_emitter.py) | Event emitter |
| [`backend_client/exceptions.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/exceptions.py) | Typed exceptions |
| [`backend_client/tests/__init__.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/tests/__init__.py) | Test package |
| [`backend_client/tests/test_backend_client.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend_client/tests/test_backend_client.py) | 19 unit tests |
| [`backend/tests/test_step12_integration.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/backend/tests/test_step12_integration.py) | 13 integration tests |

## 13. Files Modified

| File | Change |
|------|--------|
| [`app.py`](file:///c:/Users/jnark/Documents/MEDHA/MEDHA/app.py) | Full rewrite: login screen, API routing, event emission |
