import streamlit as st
import uuid
import tempfile
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (API keys, models)
load_dotenv()

from chatbot.conversation_manager import ConversationManager
from chatbot.engines.text_adapter import MedhaTextAdapter
from chatbot.llm.gemini_provider import GeminiProvider
from chatbot.safety.safety_gateway import DeterministicSafetyGateway
from chatbot.engines.question_engine import DeterministicQuestionEngine
from chatbot.features.feature_mapper import DeterministicFeatureMapper
from chatbot.summary.conversation_summary_engine import ConversationSummaryEngine
from chatbot.engines.behaviour_adapter import MedhaBehaviourAdapter
from chatbot.engines.voice_adapter import MedhaVoiceAdapter

st.set_page_config(page_title="MEDHA Assistant", page_icon="🧠", layout="centered")


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
                "Please transcribe the spoken words in this audio clearly and accurately. Return ONLY the transcribed text. Do not add quotes, notes, or timestamps. If there is no speech, return an empty string."
            ]
        )
        return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"[ASR Warning] Transcription error: {e}")
        return ""


# ==========================================
# INITIALIZE SESSION STATE
# ==========================================
if "manager" not in st.session_state:
    st.session_state.manager = ConversationManager(
        text_adapter=MedhaTextAdapter(),
        llm_provider=GeminiProvider(),
        safety_gateway=DeterministicSafetyGateway(),
        question_engine=DeterministicQuestionEngine(),
        feature_mapper=DeterministicFeatureMapper(),
        summary_engine=ConversationSummaryEngine(),
        behaviour_adapter=MedhaBehaviourAdapter(),
        voice_adapter=MedhaVoiceAdapter()
    )

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.manager.create_session(victim_id="V_UI", session_id=st.session_state.session_id)
    st.session_state.session_start_time = datetime.now()

if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = datetime.now()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hello. How can I help you today?"})

# Track processed audio so we don't process the same recording twice
if "last_processed_audio_hash" not in st.session_state:
    st.session_state.last_processed_audio_hash = None

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("MEDHA Chat Session")
    
    if st.button("New Conversation", type="primary", use_container_width=True):
        # Reset session
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.manager.create_session(victim_id="V_UI", session_id=st.session_state.session_id)
        st.session_state.session_start_time = datetime.now()
        st.session_state.messages = [{"role": "assistant", "content": "Hello. How can I help you today?"}]
        st.session_state.last_processed_audio_hash = None
        st.rerun()
    
    st.divider()
    st.markdown("### 🎙️ Voice Input")
    st.caption("Use microphone (requires `http://localhost:8501`) or upload an audio file.")
    
    voice_input_mode = st.radio("Voice Source", ["Microphone", "Upload File"], horizontal=True, label_visibility="collapsed")
    
    if voice_input_mode == "Microphone":
        audio_value = st.audio_input("Record audio", label_visibility="collapsed")
    else:
        audio_value = st.file_uploader("Upload audio (.wav, .mp3, .ogg)", type=["wav", "mp3", "ogg", "m4a"], label_visibility="collapsed")

    st.divider()
    
    # Session Context & Summary Inspector
    with st.expander("📋 Session Context & Summary", expanded=False):
        current_state = st.session_state.manager.get_state(st.session_state.session_id)
        
        # Modality Indicators
        st.markdown("**Active Modalities:**")
        col1, col2 = st.columns(2)
        with col1:
            txt_on = current_state.text_available == 1.0
            st.markdown(f"Text: {'🟢 Active' if txt_on else '⚪ Inactive'}")
            voi_on = current_state.voice_available == 1.0
            st.markdown(f"Voice: {'🟢 Active' if voi_on else '⚪ Inactive'}")
        with col2:
            st.markdown(f"Behaviour: {'🟢 Active' if current_state.behav_available == 1.0 else '⚪ Inactive'}")
            st.markdown(f"Structured: {'🟢 Active' if current_state.struct_available == 1.0 else '⚪ Inactive'}")
            
        st.divider()
        st.markdown("**Conversation Summary:**")
        summary_dict = current_state.conversation_summary.to_dict()
        has_summary_items = False
        for category, items in summary_dict.items():
            if isinstance(items, list) and items:
                has_summary_items = True
                cat_title = category.replace("_", " ").title()
                st.markdown(f"*{cat_title}:*")
                for itm in items:
                    st.markdown(f"- {itm.get('content', '')}")
        if not has_summary_items:
            st.caption("No persistent summary items extracted yet.")
            
        st.divider()
        st.download_button(
            label="Download Session JSON",
            data=current_state.to_json(indent=2),
            file_name=f"medha_session_{st.session_state.session_id[:8]}.json",
            mime="application/json",
            use_container_width=True
        )

# ==========================================
# RENDER CHAT HISTORY
# ==========================================
st.title("MEDHA V2 Assistant")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# HANDLE INPUT
# ==========================================
prompt = st.chat_input("Type your message here...")

new_audio_available = False
audio_bytes = None

if audio_value is not None:
    audio_bytes = audio_value.getvalue()
    audio_hash = hash(audio_bytes)
    if audio_hash != st.session_state.last_processed_audio_hash:
        new_audio_available = True
        st.session_state.last_processed_audio_hash = audio_hash

# Process turn if there is text OR new audio
if prompt or new_audio_available:
    user_text = prompt if prompt else ""
    display_text = user_text
    
    audio_path = None
    if new_audio_available:
        # Save audio to a temporary file for the acoustic Voice Engine
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio.write(audio_bytes)
        temp_audio.close()
        audio_path = temp_audio.name
        
        # If user spoke without typing text, transcribe speech for LLM & Text Engine
        if not user_text:
            with st.spinner("Processing spoken message..."):
                transcribed = transcribe_audio_gemini(audio_bytes)
                if transcribed:
                    user_text = transcribed
        
        display_text = f"🎤 *[Voice Message]* {user_text}" if user_text else "🎤 *[Voice Message]*"

    # Display user's input immediately
    if display_text:
        st.chat_message("user").markdown(display_text)
        st.session_state.messages.append({"role": "user", "content": display_text})
        
    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("MEDHA is thinking..."):
            try:
                # Compute session behavioural telemetry
                elapsed_min = (datetime.now() - st.session_state.session_start_time).total_seconds() / 60.0
                turn_behaviour = {
                    "Session_Duration_Minutes": round(max(0.1, elapsed_min), 2),
                    "Interaction_Frequency_7d": 1.0,
                    "Response_Delay_Hours": 0.0,
                }
                
                turn_result = st.session_state.manager.process_message(
                    session_id=st.session_state.session_id,
                    message=user_text,
                    audio_path=audio_path,
                    behaviour_data=turn_behaviour
                )
                
                # Render Safety Gateway warnings if triggered
                if turn_result.safety_result and turn_result.safety_result.is_triggered:
                    st.error("⚠️ Safety Protocol Triggered")
                
                assistant_response = turn_result.assistant_response
                st.markdown(assistant_response)
                
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except Exception as e:
                error_msg = "I encountered an error processing your message. Please try again later."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                print(f"[UI Error] process_message failed: {e}")
                
            finally:
                # Cleanup temp audio file
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except Exception:
                        pass
