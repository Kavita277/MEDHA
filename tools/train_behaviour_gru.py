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
BEHAVIOUR_OUT_CSV = os.path.join(DATASET_DIR, "behaviour_engine_outputs_500x30.csv")
TARGETS_CSV = os.path.join(DATASET_DIR, "targets_1000x30.csv")
SPLITS_JSON = os.path.join(DATASET_DIR, "patient_splits.json")
MODEL_DIR = os.path.join("Models", "behaviour_gru")

os.makedirs(MODEL_DIR, exist_ok=True)

class BehaviourGRU(nn.Module):
    def __init__(self, input_size=3, hidden_size=32, num_layers=1):
        super(BehaviourGRU, self).__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        # x is [batch, seq_len, input_size]
        out, _ = self.gru(x)
        # Take the output of the last time step
        last_out = out[:, -1, :]
        logit = self.fc(last_out)
        return logit.squeeze(-1)

def prepare_data():
    with open(SPLITS_JSON, "r") as f:
        splits = json.load(f)
        
    feat_df = pd.read_csv(BEHAVIOUR_OUT_CSV)
    targ_df = pd.read_csv(TARGETS_CSV)
    
    # Sort both
    feat_df = feat_df.sort_values(by=['patient_id', 'day_index'])
    targ_df = targ_df.sort_values(by=['patient_id', 'day_index'])
    
    # Check if we have 30 days per patient
    features = ['anomaly_score', 'engagement_deviation', 'inactivity_score']
    
    def build_tensors(patient_ids):
        X = []
        y = []
        for pid in patient_ids:
            p_feat = feat_df[feat_df['patient_id'] == pid]
            p_targ = targ_df[targ_df['patient_id'] == pid]
            
            if len(p_feat) != 30 or len(p_targ) != 30:
                print(f"Skipping patient {pid} due to missing days")
                continue
                
            x_seq = p_feat[features].values
            # target at day 30
            y_val = p_targ[p_targ['day_index'] == 30]['current_distress_label'].values[0]
            
            X.append(x_seq)
            y.append(y_val)
            
        return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

    X_train, y_train = build_tensors(splits['train'])
    X_val, y_val = build_tensors(splits['val'])
    X_test, y_test = build_tensors(splits['test'])
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def main():
    if not os.path.exists(BEHAVIOUR_OUT_CSV):
        print(f"File {BEHAVIOUR_OUT_CSV} not found! Wait for extraction to finish.")
        return
        
    print("Preparing data...")
    X_train, y_train, X_val, y_val, X_test, y_test = prepare_data()
    
    print(f"Train shapes: X={X_train.shape}, y={y_train.shape}")
    print(f"Val shapes: X={X_val.shape}, y={y_val.shape}")
    print(f"Test shapes: X={X_test.shape}, y={y_test.shape}")
    
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_val, y_val), batch_size=32, shuffle=False)
    
    model = BehaviourGRU()
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
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, "behaviour_gru.pt"))
            
    print(f"Training complete. Best Val Loss: {best_val_loss:.4f}")
    
if __name__ == "__main__":
    main()
