import os
import sys
import torch
import numpy as np

# Adjust imports to grab from MEDHA structure
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import importlib.util

# Load text engine from folder with space
spec = importlib.util.spec_from_file_location("medha_text_engine", "engine/text engine/medha_text_engine.py")
medha_text_engine = importlib.util.module_from_spec(spec)
sys.modules["medha_text_engine"] = medha_text_engine
spec.loader.exec_module(medha_text_engine)
get_medha_text_features = medha_text_engine.get_medha_text_features

from tools.train_gated_fusion import GatedFusionModel
from tools.synchronize_multimodal_dataset import TextGRU, BehaviourGRU, VoiceGRU

# We need the behaviour artifact loader since we're using real data mockups
import joblib

# Load frozen behaviour model
try:
    beh_artifacts = joblib.load(os.path.join("engine", "behaviour_engine", "medha_scoring_artifacts.joblib"))
except:
    print("Could not load behaviour joblib, mocking behaviour output")
    beh_artifacts = None

# 1. Instantiate Sub-Models
text_model = TextGRU()
text_model.load_state_dict(torch.load("Models/text_gru/text_gru.pt"))
text_model.eval()

beh_model = BehaviourGRU()
beh_model.load_state_dict(torch.load("Models/behaviour_gru/behaviour_gru.pt"))
beh_model.eval()

voice_model = VoiceGRU(input_size=768) # Upgraded to Wav2Vec2 input size
try:
    voice_model.load_state_dict(torch.load("Models/voice_gru/voice_gru.pt"))
except Exception as e:
    print("Could not load Voice GRU, it may be in middle of retrain.")
voice_model.eval()

fusion_model = GatedFusionModel(struct_dim=19)
fusion_model.load_state_dict(torch.load("Models/fusion_model/fusion_model.pt"))
fusion_model.eval()


def get_behaviour_vector(pure_vals):
    if not beh_artifacts:
        return [0.0, 0.0, 0.0]
    
    # Very simplified mockup of what medha_scoring_api does
    scaler = beh_artifacts["scaler"]
    imputer = beh_artifacts["imputer"]
    iso_forest = beh_artifacts["iso_forest"]
    ref_scores = beh_artifacts["reference_raw_scores"]
    
    # Pure vals: completion_baseline_z, latency_baseline_z, question_skip_rate
    # To get anomaly score
    try:
        X = scaler.transform(imputer.transform([pure_vals]))
        raw = float(-iso_forest.decision_function(X)[0])
        anomaly_score = float(np.searchsorted(ref_scores, raw, side="left") / len(ref_scores))
    except:
        anomaly_score = 0.5
        
    return [anomaly_score, pure_vals[0] * 0.5, 0.0] # mockup engagement/inactivity


def run_case(case_name, text_input, voice_vector, behaviour_pure, struct_vector):
    print(f"\n{'='*60}")
    print(f"CASE: {case_name}")
    print(f"{'='*60}")
    
    # 1. Engine Layer
    with torch.no_grad():
        text_features = get_medha_text_features(text_input) # 5-dim
    beh_features = get_behaviour_vector(behaviour_pure) # 3-dim
    
    # 2. Modality GRU Layer (Simulating a 20-day escalating trajectory)
    # GRU expects shape (batch, seq_len, features)
    # We repeat the extreme features 20 times to build up the GRU's hidden state
    text_seq = torch.tensor([text_features] * 20, dtype=torch.float32).unsqueeze(0)
    voice_seq = torch.tensor([voice_vector] * 20, dtype=torch.float32).unsqueeze(0)
    beh_seq = torch.tensor([beh_features] * 20, dtype=torch.float32).unsqueeze(0)
    
    with torch.no_grad():
        z_text = text_model(text_seq).item()
        z_voice = voice_model(voice_seq).item()
        z_beh = beh_model(beh_seq).item()
        
    # 3. Gated Fusion Layer
    Z = torch.tensor([[z_text, z_voice, z_beh]], dtype=torch.float32)
    M = torch.tensor([[1.0, 1.0, 1.0]], dtype=torch.float32) # All modalities available
    S = torch.tensor([struct_vector], dtype=torch.float32)
    
    with torch.no_grad():
        z_final, future_logit, w = fusion_model(Z, M, S)
        
    current_distress_prob = torch.sigmoid(z_final).item()
    future_escalation_prob = torch.sigmoid(future_logit).item()
    gate_weights = w[0].numpy()
    
    print(f"INPUT TEXT: '{text_input}'")
    print(f"Text Distressed Logit:  {z_text:.4f}")
    print(f"Voice Logit:            {z_voice:.4f}")
    print(f"Behaviour Logit:        {z_beh:.4f}")
    
    print("\n--- GATED FUSION ---")
    print(f"Gate Attention [Text, Voice, Behaviour]: {gate_weights[0]:.2f}, {gate_weights[1]:.2f}, {gate_weights[2]:.2f}")
    
    print("\n--- FINAL PREDICTIONS ---")
    print(f"Current Distress Probability:   {current_distress_prob*100:.1f}%")
    print(f"Future Escalation Probability:  {future_escalation_prob*100:.1f}%")


# ==========================================================
# TEST CASES
# ==========================================================

# Struct Vector (19 dims) Mockup (index 0 is threat_event)
no_struct = [0.0] * 19
high_struct = [0.0] * 19
high_struct[0] = 1.0 # threat_event = 1
high_struct[14] = 1.0 # recent_episode = 1
high_struct[15] = 1.0 # episode_severity = 1

# Case 1: Neutral / Safe
run_case(
    case_name="Safe & Neutral (Ground Truth: Low Distress)",
    text_input="I went to the store today and bought some groceries. It was a normal day.",
    voice_vector=[0.0]*768, # Normal voice (baseline zeros)
    behaviour_pure=[0.0, 0.0, 0.0], # normal baseline, no skips
    struct_vector=no_struct
)

# Case 2: High Text Distress, No Structural Threat
run_case(
    case_name="High Emotional Distress, No Active Threat (Ground Truth: Medium Distress)",
    text_input="I feel completely overwhelmed. I just can't stop crying, everything feels so heavy right now.",
    voice_vector=[0.5]*768, # Sad voice (shifted tensor)
    behaviour_pure=[1.5, 2.0, 0.5], # slow latency, high skip rate
    struct_vector=no_struct
)

# Case 3: High Text Threat, High Structural Threat
run_case(
    case_name="Active Threat (Ground Truth: Immediate Triage/High Escalation)",
    text_input="He's outside the house again. I told him to leave but he won't. I'm hiding in the bathroom.",
    voice_vector=[1.0]*768, # Fear/Angry voice (max shifted)
    behaviour_pure=[-1.0, -1.5, 0.0], # Fast, rushed completion
    struct_vector=high_struct
)

# Case 4: Stoic Text, High Behavioural/Structural Threat (Masked Trauma)
run_case(
    case_name="Stoic Masking (Ground Truth: High Distress hidden in behaviour)",
    text_input="I'm fine. Everything is normal. Nothing to report.",
    voice_vector=[-0.5]*768, # Flat voice
    behaviour_pure=[3.0, 4.0, 0.9], # EXTREMELY abnormal behaviour: skipped 90% questions, very slow
    struct_vector=high_struct # Past history of severe violence
)
