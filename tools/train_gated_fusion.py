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
SYNC_CSV = os.path.join(DATASET_DIR, "synchronized_multimodal_150x30.csv")
SPLITS_JSON = os.path.join(DATASET_DIR, "patient_splits_150.json")
MODEL_DIR = os.path.join("Models", "fusion_model")

os.makedirs(MODEL_DIR, exist_ok=True)

class GatedFusionModel(nn.Module):
    def __init__(self, struct_dim=19):
        super(GatedFusionModel, self).__init__()
        # Gate network to predict weights
        self.gate_net = nn.Sequential(
            nn.Linear(struct_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 3) # text, voice, behaviour
        )
        
        # Future escalation head
        self.future_head = nn.Sequential(
            nn.Linear(3 + 3, 16), # w_i and z_i
            nn.ReLU(),
            nn.Linear(16, 1)
        )
        
    def forward(self, z, masks, struct_ctx):
        # z: (batch, 3)
        # masks: (batch, 3)
        # struct_ctx: (batch, struct_dim)
        
        gate_logits = self.gate_net(struct_ctx)
        
        # Mask unavailable modalities
        gate_logits = gate_logits.masked_fill(masks == 0, -1e9)
        
        w = torch.softmax(gate_logits, dim=-1)
        
        # Final z is weighted sum
        z_final = torch.sum(w * z, dim=-1)
        
        # Future head
        future_in = torch.cat([w, z], dim=-1)
        future_logit = self.future_head(future_in).squeeze(-1)
        
        return z_final, future_logit, w

def prepare_data():
    with open(SPLITS_JSON, "r") as f:
        splits = json.load(f)
        
    df = pd.read_csv(SYNC_CSV)
    
    struct_cols = [c for c in df.columns if c.startswith('struct_')]
    
    def build_tensors(patient_ids):
        Z, M, S, y_curr, y_fut, valid_mask = [], [], [], [], [], []
        
        for pid in patient_ids:
            p_df = df[df['patient_id'] == pid].sort_values(by='day_index')
            for _, row in p_df.iterrows():
                Z.append([row['z_text'], row['z_voice'], row['z_behaviour']])
                M.append([row['text_available'], row['voice_available'], row['behaviour_available']])
                S.append(row[struct_cols].values.astype(float))
                y_curr.append(row['current_distress_label'])
                
                # Check future escalation validity (might be NaN at the end of trajectory)
                fut_val = row['future_escalation_label']
                if pd.isna(fut_val) or fut_val == -1:
                    y_fut.append(0.0)
                    valid_mask.append(0.0) # mask out loss for future
                else:
                    y_fut.append(float(fut_val))
                    valid_mask.append(1.0)
                    
        return (torch.tensor(np.array(Z), dtype=torch.float32), 
                torch.tensor(np.array(M), dtype=torch.float32),
                torch.tensor(np.array(S), dtype=torch.float32),
                torch.tensor(np.array(y_curr), dtype=torch.float32),
                torch.tensor(np.array(y_fut), dtype=torch.float32),
                torch.tensor(np.array(valid_mask), dtype=torch.float32))

    tensors_train = build_tensors(splits['train'])
    tensors_val = build_tensors(splits['val'])
    tensors_test = build_tensors(splits['test'])
    
    return tensors_train, tensors_val, tensors_test

def main():
    if not os.path.exists(SYNC_CSV):
        print(f"File {SYNC_CSV} not found! Wait for synchronization to finish.")
        return
        
    print("Preparing data...")
    t_train, t_val, t_test = prepare_data()
    
    train_loader = DataLoader(TensorDataset(*t_train), batch_size=64, shuffle=True)
    val_loader = DataLoader(TensorDataset(*t_val), batch_size=64, shuffle=False)
    
    model = GatedFusionModel(struct_dim=19)
    criterion = nn.BCEWithLogitsLoss(reduction='none')
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    epochs = 30
    best_val_loss = float('inf')
    
    print("Training Gated Late Fusion Model...")
    for epoch in range(epochs):
        model.train()
        train_loss, train_curr_loss, train_fut_loss = 0.0, 0.0, 0.0
        
        for Z, M, S, y_c, y_f, v_mask in train_loader:
            optimizer.zero_grad()
            z_final, f_logit, _ = model(Z, M, S)
            
            loss_c = criterion(z_final, y_c).mean()
            loss_f = (criterion(f_logit, y_f) * v_mask).sum() / (v_mask.sum() + 1e-8)
            
            loss = loss_c + loss_f
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            train_curr_loss += loss_c.item()
            train_fut_loss += loss_f.item()
            
        # Validation
        model.eval()
        val_loss, val_curr_loss, val_fut_loss = 0.0, 0.0, 0.0
        with torch.no_grad():
            for Z, M, S, y_c, y_f, v_mask in val_loader:
                z_final, f_logit, _ = model(Z, M, S)
                loss_c = criterion(z_final, y_c).mean()
                loss_f = (criterion(f_logit, y_f) * v_mask).sum() / (v_mask.sum() + 1e-8)
                
                loss = loss_c + loss_f
                val_loss += loss.item()
                val_curr_loss += loss_c.item()
                val_fut_loss += loss_f.item()
                
        n_train = len(train_loader)
        n_val = len(val_loader)
        
        print(f"Ep {epoch+1:02d} | Train: {train_loss/n_train:.3f} (Curr: {train_curr_loss/n_train:.3f}, Fut: {train_fut_loss/n_train:.3f}) | Val: {val_loss/n_val:.3f} (Curr: {val_curr_loss/n_val:.3f}, Fut: {val_fut_loss/n_val:.3f})")
        
        if (val_loss/n_val) < best_val_loss:
            best_val_loss = (val_loss/n_val)
            torch.save(model.state_dict(), os.path.join(MODEL_DIR, "fusion_model.pt"))
            
    print(f"Training complete. Best Val Loss: {best_val_loss:.4f}")
    
if __name__ == "__main__":
    main()
