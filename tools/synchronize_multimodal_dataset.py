import os
import json
import torch
import torch.nn as nn
import pandas as pd
import numpy as np

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
TEXT_CSV = os.path.join(DATASET_DIR, "text_engine_outputs_500x30.csv")
VOICE_NPZ = os.path.join(DATASET_DIR, "voice_engine_outputs_150x30.npz")
BEHAVIOUR_CSV = os.path.join(DATASET_DIR, "behaviour_engine_outputs_500x30.csv")
STRUCT_CSV = os.path.join(DATASET_DIR, "structured_context_1000x30.csv")
TARGETS_CSV = os.path.join(DATASET_DIR, "targets_1000x30.csv")
PATIENTS_CSV = os.path.join(DATASET_DIR, "selected_150_voice_patients.csv")
OUT_CSV = os.path.join(DATASET_DIR, "synchronized_multimodal_150x30.csv")

class TextGRU(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(5, 64, 1, batch_first=True)
        self.fc = nn.Linear(64, 1)
    def forward(self, x):
        return self.fc(self.gru(x)[0][:, -1, :]).squeeze(-1)

class VoiceGRU(nn.Module):
    # Wav2Vec2 dimensions
    def __init__(self, input_size=768, hidden_size=64, num_layers=1):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
    def forward(self, x):
        return self.fc(self.gru(x)[0][:, -1, :]).squeeze(-1)

class BehaviourGRU(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(3, 32, 1, batch_first=True)
        self.fc = nn.Linear(32, 1)
    def forward(self, x):
        return self.fc(self.gru(x)[0][:, -1, :]).squeeze(-1)

def get_logits_from_csv(df, features, model, patient_ids):
    logits_dict = {}
    model.eval()
    with torch.no_grad():
        for pid in patient_ids:
            p_df = df[df['patient_id'] == pid].sort_values(by='day_index')
            if len(p_df) == 0:
                continue
            x_seq = p_df[features].values
            logits = []
            for t in range(1, len(p_df) + 1):
                x_sub = torch.tensor(np.array([x_seq[:t]]), dtype=torch.float32)
                l = model(x_sub).item()
                logits.append(l)
            logits_dict[pid] = logits
    return logits_dict

def get_logits_from_npz(npz_path, model, patient_ids):
    logits_dict = {}
    mask_dict = {}
    
    npz = np.load(npz_path)
    X_voice = npz["X_voice"]
    voice_mask = npz["voice_mask"]
    npz_pids = list(npz["patient_ids"])
    
    model.eval()
    with torch.no_grad():
        for pid in patient_ids:
            if pid not in npz_pids:
                continue
            idx = npz_pids.index(pid)
            x_seq = X_voice[idx] # (30, 768)
            mask_seq = voice_mask[idx]
            
            logits = []
            for t in range(1, 31):
                x_sub = torch.tensor(np.array([x_seq[:t]]), dtype=torch.float32)
                l = model(x_sub).item()
                logits.append(l)
                
            logits_dict[pid] = logits
            mask_dict[pid] = list(mask_seq)
            
    return logits_dict, mask_dict

def main():
    if not os.path.exists(VOICE_NPZ) or not os.path.exists("Models/voice_gru/voice_gru.pt"):
        print("Voice GRU or features not ready yet.")
        return
        
    print("Loading models...")
    text_model = TextGRU()
    text_model.load_state_dict(torch.load("Models/text_gru/text_gru.pt"))
    
    beh_model = BehaviourGRU()
    beh_model.load_state_dict(torch.load("Models/behaviour_gru/behaviour_gru.pt"))
    
    voice_model = VoiceGRU()
    voice_model.load_state_dict(torch.load("Models/voice_gru/voice_gru.pt"))
    
    print("Loading data...")
    selected_patients = pd.read_csv(PATIENTS_CSV)['patient_id'].tolist()
    
    text_df = pd.read_csv(TEXT_CSV)
    beh_df = pd.read_csv(BEHAVIOUR_CSV)
    struct_df = pd.read_csv(STRUCT_CSV)
    targ_df = pd.read_csv(TARGETS_CSV)
    
    print("Inferring logits for each day...")
    text_feats = ['text_distress', 'fear_signal', 'threat_context', 'negative_affect', 'urgency']
    beh_feats = ['anomaly_score', 'engagement_deviation', 'inactivity_score']
    
    text_logits = get_logits_from_csv(text_df, text_feats, text_model, selected_patients)
    beh_logits = get_logits_from_csv(beh_df, beh_feats, beh_model, selected_patients)
    voice_logits, voice_masks = get_logits_from_npz(VOICE_NPZ, voice_model, selected_patients)
    
    print("Synchronizing dataset...")
    rows = []
    
    struct_cols = ['threat_event', 'upcoming_hearing', 'hearing_completed', 'investigation_delay', 'compensation_delay', 'relocation_stress', 'rehabilitation_issue', 'protection_event', 'family_support', 'social_support', 'therapist_engagement', 'access_to_services', 'stable_housing', 'other_protective_factors', 'recent_episode', 'episode_severity', 'family_reported_episode', 'intervention', 'follow_up']
    
    for pid in selected_patients:
        p_targ = targ_df[targ_df['patient_id'] == pid].sort_values(by='day_index')
        p_struct = struct_df[struct_df['patient_id'] == pid].sort_values(by='day_index')
        
        for t in range(len(p_targ)):
            day = t + 1
            
            z_text = text_logits[pid][t] if pid in text_logits and len(text_logits[pid]) > t else 0.0
            z_voice = voice_logits[pid][t] if pid in voice_logits and len(voice_logits[pid]) > t else 0.0
            z_beh = beh_logits[pid][t] if pid in beh_logits and len(beh_logits[pid]) > t else 0.0
            
            v_avail = voice_masks[pid][t] if pid in voice_masks and len(voice_masks[pid]) > t else 1
            
            row = {
                'patient_id': pid,
                'day_index': day,
                'z_text': z_text,
                'z_voice': z_voice,
                'z_behaviour': z_beh,
                'text_available': 1,
                'voice_available': int(v_avail),
                'behaviour_available': 1,
                'current_distress_label': p_targ.iloc[t]['current_distress_label'],
                'future_escalation_label': p_targ.iloc[t]['future_escalation_label']
            }
            
            for sc in struct_cols:
                row[f'struct_{sc}'] = p_struct.iloc[t][sc] if len(p_struct) > t and sc in p_struct.columns else 0.0
                
            rows.append(row)
            
    out_df = pd.DataFrame(rows)
    out_df = out_df.fillna(0.0)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"Saved synchronized dataset to {OUT_CSV}")

if __name__ == "__main__":
    main()
