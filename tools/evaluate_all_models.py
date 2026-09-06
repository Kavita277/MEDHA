import os
import json
import torch
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Reuse the fusion model definition and data prep
from train_gated_fusion import GatedFusionModel, prepare_data

MODEL_PATH = os.path.join("Models", "fusion_model", "fusion_model.pt")

def print_metrics(name, y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    print(f"\n--- {name} ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")

def evaluate_models():
    print("Loading test data...")
    t_train, t_val, t_test = prepare_data()
    Z_test, M_test, S_test, y_c_test, y_f_test, v_mask_test = t_test
    
    model = GatedFusionModel(struct_dim=19)
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()
    
    with torch.no_grad():
        # Fusion forward pass
        z_final, f_logit, weights = model(Z_test, M_test, S_test)
        
        # Ground truths
        y_c = y_c_test.numpy()
        y_f = y_f_test.numpy()
        v_mask = v_mask_test.numpy()
        
        # 1. Independent GRU evaluation
        z_text = Z_test[:, 0].numpy()
        z_voice = Z_test[:, 1].numpy()
        z_beh = Z_test[:, 2].numpy()
        
        pred_text = (1 / (1 + np.exp(-z_text))) >= 0.5
        pred_voice = (1 / (1 + np.exp(-z_voice))) >= 0.5
        pred_beh = (1 / (1 + np.exp(-z_beh))) >= 0.5
        
        # M_test[:, i] == 1 means available. We evaluate only on available samples for fair individual metrics
        mask_text = M_test[:, 0].numpy() == 1
        mask_voice = M_test[:, 1].numpy() == 1
        mask_beh = M_test[:, 2].numpy() == 1
        
        print_metrics("Text GRU (Current Distress)", y_c[mask_text], pred_text[mask_text])
        print_metrics("Voice GRU (Current Distress)", y_c[mask_voice], pred_voice[mask_voice])
        print_metrics("Behaviour GRU (Current Distress)", y_c[mask_beh], pred_beh[mask_beh])
        
        # 2. Fusion evaluation
        pred_fusion_c = torch.sigmoid(z_final).numpy() >= 0.5
        print_metrics("Gated Late Fusion (Current Distress)", y_c, pred_fusion_c)
        
        # 3. Future Escalation evaluation
        valid_idx = np.where(v_mask == 1)[0]
        if len(valid_idx) > 0:
            pred_fusion_f = torch.sigmoid(f_logit).numpy()[valid_idx] >= 0.5
            y_f_valid = y_f[valid_idx]
            print_metrics("Fusion Future Escalation Head", y_f_valid, pred_fusion_f)

if __name__ == "__main__":
    evaluate_models()
