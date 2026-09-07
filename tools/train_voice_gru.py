import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import pandas as pd
import numpy as np

# Reproducibility
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
VOICE_NPZ = os.path.join(DATASET_DIR, "voice_engine_outputs_150x30.npz")
TARGETS_CSV = os.path.join(DATASET_DIR, "targets_1000x30.csv")
SPLITS_JSON = os.path.join(DATASET_DIR, "patient_splits_150.json")
MODEL_DIR = os.path.join("Models", "voice_gru")

os.makedirs(MODEL_DIR, exist_ok=True)

class VoiceGRU(nn.Module):
    # Wav2Vec2 base hidden_dim is 768
    def __init__(self, input_size=768, hidden_size=64, num_layers=1):
        super(VoiceGRU, self).__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        out, _ = self.gru(x)
        last_out = out[:, -1, :]
        logit = self.fc(last_out)
        return logit.squeeze(-1)

def prepare_data():
    with open(SPLITS_JSON, "r") as f:
        splits = json.load(f)
        
    # Load targets
    targ_df = pd.read_csv(TARGETS_CSV)
    
    # Load pre-extracted Wav2Vec2 features
    npz = np.load(VOICE_NPZ)
    X_voice = npz["X_voice"]         # (150, 30, 768)
    patient_ids = npz["patient_ids"] # (150,)
    
    pid_to_idx = {pid: idx for idx, pid in enumerate(patient_ids)}
    
    def build_tensors(split_pids):
        X = []
        y = []
        for pid in split_pids:
            if pid not in pid_to_idx:
                continue
                
            idx = pid_to_idx[pid]
            x_seq = X_voice[idx] # (30, 768)
            
            p_targ = targ_df[targ_df['patient_id'] == pid]
            if len(p_targ) != 30:
                print(f"Skipping patient {pid} due to missing target days")
                continue
                
            y_val = p_targ[p_targ['day_index'] == 30]['current_distress_label'].values[0]
            
            X.append(x_seq)
            y.append(y_val)
            
        return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

    X_train, y_train = build_tensors(splits['train'])
    X_val, y_val = build_tensors(splits['val'])
    X_test, y_test = build_tensors(splits['test'])
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def main():
    if not os.path.exists(VOICE_NPZ):
        print(f"File {VOICE_NPZ} not found! Wait for extraction to finish.")
        return
        
    print("Preparing data...")
    X_train, y_train, X_val, y_val, X_test, y_test = prepare_data()
    
    print(f"Train shapes: X={X_train.shape}, y={y_train.shape}")
    print(f"Val shapes: X={X_val.shape}, y={y_val.shape}")
    print(f"Test shapes: X={X_test.shape}, y={y_test.shape}")
    
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=32, shuffle=False)
    
    model = VoiceGRU()
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    epochs = 20
    best_val_loss = float('inf')
    
    print("Training...")
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                logits = model(X_batch)
                loss = criterion(logits, y_batch)
                val_loss += loss.item()
                
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        
        print(f"Epoch {epoch+1:02d}/{epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, "voice_gru.pt"))
            
    print(f"Training complete. Best Val Loss: {best_val_loss:.4f}")
    
if __name__ == "__main__":
    main()
