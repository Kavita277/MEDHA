"""
MEDHA V2 — Streamlit Frontend (Step 12: Backend-Connected)
=============================================================

This file is the Streamlit entry point for the MEDHA user-facing chat application.

Architecture after Step 12:
  Streamlit (this file)
       ↓ HTTP (httpx via MedhaBackendClient)
  FastAPI Backend  (uvicorn backend.main:app)
       ↓ ConversationManager + MedhaState → PostgreSQL

What changed from the standalone version:
  - All chat turns are routed through POST /api/v1/chat/sessions/{id}/message
  - Session lifecycle (create / end) managed via POST /api/v1/sessions
  - Behaviour events submitted to POST /api/v1/events/batch after each turn
  - Login screen added; JWT stored in st.session_state for the browser session
  - Audio: transcription stays local (Gemini ASR), voice features forwarded
    via chat payload metadata. No binary upload to the backend.
  - victim_id="V_UI" is eliminated; real authenticated user identity is used.

What did NOT change:
  - ConversationManager, MedhaState, all chatbot engines — UNTOUCHED
  - Frozen V2 ML pipeline — UNTOUCHED
  - Audio transcription logic (Gemini ASR) — UNTOUCHED
  - MedhaBehaviourAdapter, MedhaVoiceAdapter — not imported here anymore
    (they run inside the backend process, not the Streamlit process)

Backend URL:
  Set MEDHA_BACKEND_URL env var (default: http://localhost:8000).

Usage:
  streamlit run app.py
"""

import hashlib
import os
import sys
import tempfile
import uuid
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from backend_client import (
    MedhaBackendClient,
    BackendEventEmitter,
    MedhaAuthError,
    MedhaConnectionError,
    MedhaForbiddenError,
    MedhaClientError,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="MEDHA Assistant", page_icon="🧠", layout="centered")

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------
if "backend_client" not in st.session_state:
    st.session_state.backend_client = MedhaBackendClient()

_client: MedhaBackendClient = st.session_state.backend_client


# ---------------------------------------------------------------------------
# Audio transcription (local — Gemini ASR, no upload to backend)
# ---------------------------------------------------------------------------

def transcribe_audio_gemini(audio_bytes: bytes) -> str:
    """Transcribes spoken audio using Gemini so LLM and text adapter can understand speech."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                (
                    "Please transcribe the spoken words in this audio clearly and accurately. "
                    "Return ONLY the transcribed text. Do not add quotes, notes, or timestamps. "
                    "If there is no speech, return an empty string."
                ),
            ],
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"[ASR Warning] Transcription error: {e}")
        return ""


# ---------------------------------------------------------------------------
# Login / Logout helpers
# ---------------------------------------------------------------------------

def _is_logged_in() -> bool:
    return bool(st.session_state.get("access_token"))


def _do_login(email: str, password: str) -> bool:
    """
    Authenticates via the backend. Returns True on success.
    Sets: access_token, user_role, user_name, user_email.
    """
    try:
        result = _client.login(email=email.strip(), password=password)
        st.session_state.access_token = result.access_token
        st.session_state.user_role = result.role
        st.session_state.user_name = result.name
        st.session_state.user_email = result.email
        return True
    except MedhaAuthError as e:
        st.error(f"Login failed: {e}")
    except MedhaForbiddenError as e:
        st.error(f"Account access denied: {e}")
    except MedhaConnectionError:
        st.error(
            "Cannot reach the MEDHA backend. "
            "Please ensure the server is running at "
            f"{os.environ.get('MEDHA_BACKEND_URL', 'http://localhost:8000')}."
        )
    except MedhaClientError as e:
        st.error(f"Unexpected error during login: {e}")
    return False


def _do_logout() -> None:
    """Clears all session state and forces re-login."""
    token = st.session_state.get("access_token")
    session_id = st.session_state.get("backend_session_id")

    # Best-effort: end backend session before logout
    if token and session_id:
        try:
            emitter = st.session_state.get("event_emitter")
            if emitter:
                emitter.emit_session_end(token)
            _client.end_session(token, session_id)
        except Exception:
            pass

    for key in [
        "access_token", "user_role", "user_name", "user_email",
        "backend_session_id", "backend_session_identifier",
        "messages", "session_start_time",
        "last_processed_audio_hash", "turn_index", "event_emitter",
    ]:
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Backend session lifecycle helpers
# ---------------------------------------------------------------------------

def _create_backend_session() -> bool:
    """
    Creates a new backend session and initialises local state.
    Returns True on success.
    """
    token = st.session_state.get("access_token")
    if not token:
        return False
    try:
        session = _client.create_session(token=token)
        st.session_state.backend_session_id = session.id
        st.session_state.backend_session_identifier = session.session_identifier
        st.session_state.session_start_time = datetime.now()
        st.session_state.turn_index = 0
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello. How can I help you today?"}
        ]
        st.session_state.last_processed_audio_hash = None
        st.session_state.event_emitter = BackendEventEmitter(
            client=_client,
            session_id=session.id,
            silent=True,
        )
        return True
    except MedhaForbiddenError:
        st.error("No active case found. Please contact your therapist to set up your account.")
    except MedhaConnectionError:
        st.error("Cannot reach the MEDHA backend.")
    except MedhaClientError as e:
        st.error(f"Failed to create session: {e}")
    return False


def _end_and_restart_session() -> None:
    """
    Ends the current backend session cleanly, then creates a new one.
    Called when the user clicks 'New Conversation'.
    """
    token = st.session_state.get("access_token")
    old_session_id = st.session_state.get("backend_session_id")
    emitter = st.session_state.get("event_emitter")

    # 1. Emit session_end for the old session
    if token and old_session_id and emitter:
        try:
            emitter.emit_session_end(token)
        except Exception:
            pass

    # 2. End old backend session
    if token and old_session_id:
        try:
            _client.end_session(token, old_session_id)
        except Exception:
            pass

    # 3. Clear local state
    for key in [
        "backend_session_id", "backend_session_identifier",
        "messages", "session_start_time",
        "last_processed_audio_hash", "turn_index", "event_emitter",
    ]:
        st.session_state.pop(key, None)

    # 4. Create new session
    _create_backend_session()


# ===========================================================================
# LOGIN SCREEN
# ===========================================================================

def render_login_page() -> None:
    """Renders the MEDHA login screen. Only shown when not authenticated."""
    st.title("🧠 MEDHA")
    st.subheader("Mental Health Digital Assistant")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Sign In")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email",
                placeholder="you@example.com",
                autocomplete="email",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Your password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "Sign In",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                with st.spinner("Signing in…"):
                    success = _do_login(email, password)
                if success:
                    with st.spinner("Starting session…"):
                        session_ok = _create_backend_session()
                    if session_ok:
                        st.rerun()
                    else:
                        # Login worked but session creation failed; clean up token
                        st.session_state.pop("access_token", None)

    st.markdown("---")
    st.caption(
        "MEDHA is an AI-assisted mental health support tool. "
        "In a crisis, please contact emergency services or a crisis helpline immediately."
    )


# ===========================================================================
# MAIN CHAT UI
# ===========================================================================

def render_chat_page() -> None:
    """Renders the main MEDHA chat interface (authenticated users only)."""
    token: str = st.session_state.access_token
    session_id: str = st.session_state.backend_session_id
    emitter: BackendEventEmitter = st.session_state.event_emitter

    # ------------------------------------------------------------------
    # SIDEBAR
    # ------------------------------------------------------------------
    with st.sidebar:
        st.header("MEDHA Chat Session")
        user_name = st.session_state.get("user_name", "")
        if user_name:
            st.caption(f"Signed in as **{user_name}**")

        if st.button("New Conversation", type="primary", use_container_width=True):
            _end_and_restart_session()
            st.rerun()

        if st.button("Sign Out", use_container_width=True):
            _do_logout()
            st.rerun()

        st.divider()
        st.markdown("### 🎙️ Voice Input")
        st.caption("Use microphone (requires `http://localhost:8501`) or upload an audio file.")

        voice_input_mode = st.radio(
            "Voice Source",
            ["Microphone", "Upload File"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if voice_input_mode == "Microphone":
            audio_value = st.audio_input("Record audio", label_visibility="collapsed")
        else:
            audio_value = st.file_uploader(
                "Upload audio (.wav, .mp3, .ogg)",
                type=["wav", "mp3", "ogg", "m4a"],
                label_visibility="collapsed",
            )

        st.divider()

        with st.expander("📋 Session Info", expanded=False):
            st.markdown(f"**Session:** `{st.session_state.get('backend_session_identifier', 'N/A')}`")
            st.markdown(f"**Turns:** {st.session_state.get('turn_index', 0)}")
            st.markdown(f"**Backend:** `{_client._base_url}`")

    # ------------------------------------------------------------------
    # CHAT HISTORY
    # ------------------------------------------------------------------
    st.title("MEDHA V2 Assistant")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ------------------------------------------------------------------
    # INPUT HANDLING
    # ------------------------------------------------------------------
    prompt = st.chat_input("Type your message here…")

    new_audio_available = False
    audio_bytes = None

    if audio_value is not None:
        audio_bytes = audio_value.getvalue()
        audio_hash = hash(audio_bytes)
        if audio_hash != st.session_state.last_processed_audio_hash:
            new_audio_available = True
            st.session_state.last_processed_audio_hash = audio_hash

    if not prompt and not new_audio_available:
        return  # Nothing to process

    # ------------------------------------------------------------------
    # PROCESS TURN
    # ------------------------------------------------------------------
    user_text = prompt if prompt else ""
    display_text = user_text
    audio_path = None
    voice_metadata: dict = {}

    if new_audio_available:
        # Save audio locally for the local Voice adapter transcription
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio.write(audio_bytes)
        temp_audio.close()
        audio_path = temp_audio.name

        # If user spoke without typing, transcribe locally via Gemini ASR
        if not user_text:
            with st.spinner("Processing spoken message…"):
                transcribed = transcribe_audio_gemini(audio_bytes)
                if transcribed:
                    user_text = transcribed

        display_text = f"🎤 *[Voice Message]* {user_text}" if user_text else "🎤 *[Voice Message]*"

        # Run local Voice adapter to get feature values, then pass as metadata
        # The backend's ConversationManager will receive these via behaviour_data/metadata
        # so voice features are still captured in the backend MedhaState snapshot.
        try:
            from chatbot.engines.voice_adapter import MedhaVoiceAdapter
            from chatbot.state.medha_state import MedhaState, VOICE_FEATURES

            _va = MedhaVoiceAdapter()
            _tmp_state = MedhaState(victim_id="local_voice_probe", session_id="probe", timepoint=1)
            _va.process_and_update_state(_tmp_state, audio_path)

            if _tmp_state.voice_available == 1.0:
                voice_metadata = {
                    k: _tmp_state.voice_features.get(k)
                    for k in VOICE_FEATURES
                    if _tmp_state.voice_features.get(k) is not None
                }
        except Exception as e:
            print(f"[Voice] Local feature extraction failed (non-fatal): {e}")
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

    if display_text:
        st.chat_message("user").markdown(display_text)
        st.session_state.messages.append({"role": "user", "content": display_text})

    # ------------------------------------------------------------------
    # CALL BACKEND
    # ------------------------------------------------------------------
    with st.chat_message("assistant"):
        with st.spinner("MEDHA is thinking…"):
            # Compute session behaviour telemetry for this turn
            elapsed_sec = (
                datetime.now() - st.session_state.session_start_time
            ).total_seconds()

            behaviour_data: dict = {
                "Session_Duration_Minutes": round(max(0.1, elapsed_sec / 60.0), 2),
                "Interaction_Frequency_7d": 1.0,
                "Response_Delay_Hours": 0.0,
            }

            # Forward voice feature values in metadata (not as raw audio)
            turn_metadata: dict = {}
            if voice_metadata:
                turn_metadata["voice_features"] = voice_metadata

            try:
                result = _client.send_message(
                    token=token,
                    session_id=session_id,
                    message=user_text,
                    behaviour_data=behaviour_data,
                    metadata=turn_metadata if turn_metadata else None,
                )

                # Render safety warning if triggered
                if result.safety_triggered:
                    st.error("⚠️ Safety Protocol Triggered")

                st.markdown(result.assistant_response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": result.assistant_response}
                )

                # Update turn counter
                st.session_state.turn_index = result.turn_index

                # Emit behaviour events (silent, non-blocking)
                emitter.emit_turn(
                    token=token,
                    turn_index=result.turn_index,
                    session_duration_seconds=elapsed_sec,
                    message_length=len(user_text),
                    safety_triggered=result.safety_triggered,
                )

            except MedhaAuthError:
                st.error("Your session has expired. Please sign in again.")
                _do_logout()
                st.rerun()

            except MedhaConnectionError:
                err = (
                    "Could not reach the MEDHA backend. "
                    "Please check that the server is running and try again."
                )
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})

            except MedhaClientError as e:
                err = "I encountered an error processing your message. Please try again."
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
                print(f"[UI Error] send_message failed: {e}")

            except Exception as e:
                err = "I encountered an unexpected error. Please try again later."
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
                print(f"[UI Error] Unexpected: {e}")


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if not _is_logged_in():
    render_login_page()
else:
    # Ensure backend session exists (may have been lost on page refresh)
    if "backend_session_id" not in st.session_state:
        with st.spinner("Starting session…"):
            ok = _create_backend_session()
        if not ok:
            st.stop()

    render_chat_page()
