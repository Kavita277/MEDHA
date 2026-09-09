import pandas as pd
import numpy as np
import os
import sys
import json
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from fusion_engine.evaluate_fusion import load_dataset_and_verify_split, generate_specialist_predictions, calculate_metrics

def calculate_fusion_score(row, config_weights):
    score = 0.0
    total_w = 0.0
    for mod, w in config_weights.items():
        if w > 0:
            score += row[mod] * w
            total_w += w
    return score / total_w if total_w > 0 else 0.0

def run_freeze_and_test():
    print("Loading datasets...")
    df = load_dataset_and_verify_split()
    df = generate_specialist_predictions(df)
    
    # Correct Behaviour Engine Simulation
    df['behaviour_risk'] = 0.4*0.5 + 0.3*df['Engagement_Deviation'].abs().fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)
    df['behaviour_risk'] = df['behaviour_risk'].clip(0, 1)

    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())].copy()
    test_df = df[(df['Split'] == 'test') & (df['Future_Escalation_Label'].notna())].copy()
    
    risk_cols = ['temporal_risk_score', 'structured_risk', 'text_risk', 'voice_risk', 'behaviour_risk']
    val_df[risk_cols] = val_df[risk_cols].fillna(0)
    test_df[risk_cols] = test_df[risk_cols].fillna(0)
    
    y_val = val_df['Future_Escalation_Label'].astype(int).values
    y_test = test_df['Future_Escalation_Label'].astype(int).values
    
    # Selected Architecture: Manual All_5
    selected_weights = {"text_risk": 0.25, "voice_risk": 0.15, "behaviour_risk": 0.15, "structured_risk": 0.25, "temporal_risk_score": 0.20}
    
    y_prob_val = val_df.apply(lambda r: calculate_fusion_score(r, selected_weights), axis=1).values
    y_prob_test = test_df.apply(lambda r: calculate_fusion_score(r, selected_weights), axis=1).values
    
    print("Selecting Threshold on Validation Set...")
    thresholds = np.linspace(0.01, 0.99, 99)
    best_th = 0.5
    best_f1 = 0
    
    th_res = []
    for th in thresholds:
        ypred = (y_prob_val >= th).astype(int)
        f1 = f1_score(y_val, ypred, zero_division=0)
        rec = recall_score(y_val, ypred, zero_division=0)
        prec = precision_score(y_val, ypred, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_val, ypred, labels=[0, 1]).ravel()
        th_res.append({"threshold": float(th), "f1": f1, "recall": rec, "precision": prec, "tp": int(tp), "tn": int(tn), "fp": int(fp), "fn": int(fn)})
        
        # Optimize for best F1 where recall is > 0.8
        if f1 > best_f1 and rec >= 0.80:
            best_f1 = f1
            best_th = th
            
    # Fallback to absolute best F1 if none hit recall target
    if best_f1 == 0:
        for r in th_res:
            if r["f1"] > best_f1:
                best_f1 = r["f1"]
                best_th = r["threshold"]
    
    pd.DataFrame(th_res).to_csv("final_threshold_analysis.csv", index=False)
    
    # -----------------------
    # TEST EVALUATION
    # -----------------------
    print(f"Applying Selected Threshold ({best_th}) to Test Set EXACTLY ONCE...")
    y_pred_test = (y_prob_test >= best_th).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_test, labels=[0, 1]).ravel()
    
    test_metrics = {
        "precision": float(precision_score(y_test, y_pred_test, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred_test, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred_test, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob_test)),
        "pr_auc": float(average_precision_score(y_test, y_prob_test)),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn)
    }
    
    with open("final_test_results.json", "w") as f:
        json.dump(test_metrics, f, indent=4)
        
    config = {
        "architecture": "Manual Normalized Weights",
        "weights": selected_weights,
        "selected_threshold": float(best_th)
    }
    with open("final_fusion_config.json", "w") as f:
        json.dump(config, f, indent=4)
        
    print("Testing Complete.")
    
if __name__ == "__main__":
    run_freeze_and_test()
