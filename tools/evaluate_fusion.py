import os
import json
import torch
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Reuse the model definition
from train_gated_fusion import GatedFusionModel, prepare_data

MODEL_PATH = os.path.join("Models", "fusion_model", "fusion_model.pt")

def evaluate_model():
    print("Loading test data...")
    t_train, t_val, t_test = prepare_data()
    Z_test, M_test, S_test, y_c_test, y_f_test, v_mask_test = t_test
    
    model = GatedFusionModel(struct_dim=19)
    model.load_state_dict(torch.load(MODEL_PATH))
    model.eval()
    
    with torch.no_grad():
        z_final, f_logit, weights = model(Z_test, M_test, S_test)
        
        # Apply sigmoid because BCEWithLogitsLoss was used
        preds_c = torch.sigmoid(z_final).numpy()
        preds_f = torch.sigmoid(f_logit).numpy()
        
        y_c = y_c_test.numpy()
        y_f = y_f_test.numpy()
        v_mask = v_mask_test.numpy()
        
        # Metrics for Current Distress
        mae_c = mean_absolute_error(y_c, preds_c)
        rmse_c = np.sqrt(mean_squared_error(y_c, preds_c))
        r2_c = r2_score(y_c, preds_c)
        
        print("\n--- CURRENT DISTRESS (TEST SET) ---")
        print(f"MAE:  {mae_c:.4f}")
        print(f"RMSE: {rmse_c:.4f}")
        print(f"R2:   {r2_c:.4f}")
        
        # Metrics for Future Escalation (only where mask == 1)
        valid_idx = np.where(v_mask == 1)[0]
        if len(valid_idx) > 0:
            mae_f = mean_absolute_error(y_f[valid_idx], preds_f[valid_idx])
            rmse_f = np.sqrt(mean_squared_error(y_f[valid_idx], preds_f[valid_idx]))
            r2_f = r2_score(y_f[valid_idx], preds_f[valid_idx])
            
            print("\n--- 7-DAY FUTURE ESCALATION (TEST SET) ---")
            print(f"MAE:  {mae_f:.4f}")
            print(f"RMSE: {rmse_f:.4f}")
            print(f"R2:   {r2_f:.4f}")
        
        # Gate Weight Analysis
        w_text = weights[:, 0].numpy()
        w_voice = weights[:, 1].numpy()
        w_beh = weights[:, 2].numpy()
        
        print("\n--- GATE WEIGHT DISTRIBUTION ---")
        print(f"Average Text Weight:      {np.mean(w_text):.4f}")
        print(f"Average Voice Weight:     {np.mean(w_voice):.4f}")
        print(f"Average Behaviour Weight: {np.mean(w_beh):.4f}")

if __name__ == "__main__":
    evaluate_model()
