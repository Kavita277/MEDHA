import os
import json
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

DATASET_DIR = os.path.join("datasets", "MEDHA_Longitudinal_Synthetic_1000x30")
TEXT_OUT_CSV = os.path.join(DATASET_DIR, "text_engine_outputs_500x30.csv")
BEHAVIOUR_OUT_CSV = os.path.join(DATASET_DIR, "behaviour_engine_outputs_500x30.csv")
TARGETS_CSV = os.path.join(DATASET_DIR, "targets_1000x30.csv")
SPLITS_JSON = os.path.join(DATASET_DIR, "patient_splits.json")

class TextGRU(nn.Module):
    def __init__(self, input_size=5, hidden_size=64, num_layers=1):
        super(TextGRU, self).__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        out, _ = self.gru(x)
        last_out = out[:, -1, :]
        return self.fc(last_out).squeeze(-1)

class BehaviourGRU(nn.Module):
    def __init__(self, input_size=3, hidden_size=32, num_layers=1):
        super(BehaviourGRU, self).__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        out, _ = self.gru(x)
        last_out = out[:, -1, :]
        return self.fc(last_out).squeeze(-1)

def build_test_tensors(feat_df, targ_df, test_ids, features):
    X, y = [], []
    for pid in test_ids:
        p_feat = feat_df[feat_df['patient_id'] == pid]
        p_targ = targ_df[targ_df['patient_id'] == pid]
        
        if len(p_feat) != 30 or len(p_targ) != 30:
            continue
            
        X.append(p_feat[features].values)
        y.append(p_targ[p_targ['day_index'] == 30]['current_distress_label'].values[0])
        
    return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

def evaluate_model(model, X, y, model_name):
    model.eval()
    with torch.no_grad():
        logits = model(X)
        probs = torch.sigmoid(logits).numpy()
        preds = (probs >= 0.5).astype(int)
        
    y_true = y.numpy()
    
    acc = accuracy_score(y_true, preds)
    prec = precision_score(y_true, preds, zero_division=0)
    rec = recall_score(y_true, preds, zero_division=0)
    f1 = f1_score(y_true, preds, zero_division=0)
    auc = roc_auc_score(y_true, probs)
    
    print(f"=== {model_name} Evaluation on Test Set ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC AUC:   {auc:.4f}")
    print("=" * 40 + "\n")

def main():
    with open(SPLITS_JSON, "r") as f:
        splits = json.load(f)
    test_ids = splits['test']
    
    targ_df = pd.read_csv(TARGETS_CSV).sort_values(by=['patient_id', 'day_index'])
    
    # 1. Text GRU
    text_feat_df = pd.read_csv(TEXT_OUT_CSV).sort_values(by=['patient_id', 'day_index'])
    text_features = ['text_distress', 'fear_signal', 'threat_context', 'negative_affect', 'urgency']
    X_test_text, y_test_text = build_test_tensors(text_feat_df, targ_df, test_ids, text_features)
    
    text_model = TextGRU()
    text_model.load_state_dict(torch.load("Models/text_gru/text_gru.pt"))
    evaluate_model(text_model, X_test_text, y_test_text, "Text GRU")
    
    # 2. Behaviour GRU
    beh_feat_df = pd.read_csv(BEHAVIOUR_OUT_CSV).sort_values(by=['patient_id', 'day_index'])
    beh_features = ['anomaly_score', 'engagement_deviation', 'inactivity_score']
    X_test_beh, y_test_beh = build_test_tensors(beh_feat_df, targ_df, test_ids, beh_features)
    
    beh_model = BehaviourGRU()
    beh_model.load_state_dict(torch.load("Models/behaviour_gru/behaviour_gru.pt"))
    evaluate_model(beh_model, X_test_beh, y_test_beh, "Behaviour GRU")

if __name__ == "__main__":
    main()
