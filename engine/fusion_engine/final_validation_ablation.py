import pandas as pd
import numpy as np
import os
import sys

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from fusion_engine.evaluate_fusion import load_dataset_and_verify_split, generate_specialist_predictions, calculate_metrics
from sklearn.metrics import brier_score_loss, average_precision_score

def calculate_fusion_score(row, config_weights):
    score = 0.0
    total_w = 0.0
    for mod, w in config_weights.items():
        if w > 0:
            score += row[mod] * w
            total_w += w
    return score / total_w if total_w > 0 else 0.0

def run_ablation():
    print("Loading Validation dataset...")
    df = load_dataset_and_verify_split()
    df = generate_specialist_predictions(df)
    
    df['behaviour_risk'] = 0.4*0.5 + 0.3*df['Engagement_Deviation'].abs().fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)
    df['behaviour_risk'] = df['behaviour_risk'].clip(0, 1)

    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())].copy()
    # Fill any NaNs in the risk scores (e.g. temporal_risk_score is NaN for early timepoints)
    risk_cols = ['temporal_risk_score', 'structured_risk', 'text_risk', 'voice_risk', 'behaviour_risk']
    val_df[risk_cols] = val_df[risk_cols].fillna(0)
    y_true = val_df['Future_Escalation_Label'].astype(int).values

    # Phase 11: Ablation
    print("Running Ablation...")
    configs = {
        "Structured_only": {"structured_risk": 1.0},
        "Text_only": {"text_risk": 1.0},
        "Voice_only": {"voice_risk": 1.0},
        "Behaviour_only": {"behaviour_risk": 1.0},
        "Temporal_only": {"temporal_risk_score": 1.0},
        "Struct+Text": {"structured_risk": 0.5, "text_risk": 0.5},
        "Struct+Voice": {"structured_risk": 0.5, "voice_risk": 0.5},
        "Struct+Behaviour": {"structured_risk": 0.5, "behaviour_risk": 0.5},
        "Struct+Temporal": {"structured_risk": 0.5, "temporal_risk_score": 0.5},
        "Text+Voice+Struct": {"structured_risk": 0.34, "text_risk": 0.33, "voice_risk": 0.33},
        "Text+Behav+Struct": {"structured_risk": 0.34, "text_risk": 0.33, "behaviour_risk": 0.33},
        "Struct+Temp+Behav": {"structured_risk": 0.34, "temporal_risk_score": 0.33, "behaviour_risk": 0.33},
        "All_5_Manual": {"text_risk": 0.25, "voice_risk": 0.15, "behaviour_risk": 0.15, "structured_risk": 0.25, "temporal_risk_score": 0.20}
    }
    
    ablation_res = []
    for cname, weights in configs.items():
        y_prob = val_df.apply(lambda r: calculate_fusion_score(r, weights), axis=1).values
        metrics = calculate_metrics(y_true, y_prob, 0.15)
        metrics['brier'] = brier_score_loss(y_true, y_prob)
        ablation_res.append({"config": cname, **metrics})
        
    ablation_df = pd.DataFrame(ablation_res)
    ablation_df.to_csv("final_ablation_results.csv", index=False)
    
    # Phase 12: Conditional Multimodal Value
    print("Running Conditional Multimodal Analysis...")
    val_df['xgb_bin'] = pd.cut(val_df['structured_risk'], bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    y_prob_all5 = val_df.apply(lambda r: calculate_fusion_score(r, configs["All_5_Manual"]), axis=1).values
    val_df['all5_prob'] = y_prob_all5
    
    cond_res = []
    for b, group in val_df.groupby('xgb_bin'):
        if len(group) == 0: continue
        yt = group['Future_Escalation_Label'].astype(int).values
        if len(np.unique(yt)) < 2: continue # need both classes for auc
        
        pr_xgb = average_precision_score(yt, group['structured_risk'].values)
        pr_all5 = average_precision_score(yt, group['all5_prob'].values)
        cond_res.append({"bin": str(b), "xgb_pr_auc": pr_xgb, "all5_pr_auc": pr_all5, "n_samples": len(group)})
        
    cond_df = pd.DataFrame(cond_res)
    cond_df.to_csv("conditional_multimodal_analysis.csv", index=False)

    # Phase 13: Missing Modalities
    print("Running Missing Modalities...")
    missing_configs = [
        {"name": "All_Available", "missing": []},
        {"name": "No_Text", "missing": ["text_risk"]},
        {"name": "No_Voice", "missing": ["voice_risk"]},
        {"name": "No_Behaviour", "missing": ["behaviour_risk"]},
        {"name": "No_Temporal", "missing": ["temporal_risk_score"]},
        {"name": "No_Text_No_Voice", "missing": ["text_risk", "voice_risk"]},
        {"name": "No_Voice_No_Behav", "missing": ["voice_risk", "behaviour_risk"]},
        {"name": "No_Text_No_Behav", "missing": ["text_risk", "behaviour_risk"]}
    ]
    
    missing_res = []
    base_w = configs["All_5_Manual"]
    for mc in missing_configs:
        current_w = {k: (0 if k in mc["missing"] else v) for k, v in base_w.items()}
        y_prob = val_df.apply(lambda r: calculate_fusion_score(r, current_w), axis=1).values
        metrics = calculate_metrics(y_true, y_prob, 0.15)
        missing_res.append({"condition": mc["name"], **metrics})
        
    missing_df = pd.DataFrame(missing_res)
    missing_df.to_csv("final_missing_modality_results.csv", index=False)

    # Phase 14: GRU Contribution
    gru_contrib_df = pd.DataFrame([
        {"config": "Without GRU", "pr_auc": missing_df[missing_df["condition"] == "No_Temporal"]["pr_auc"].values[0]},
        {"config": "With GRU", "pr_auc": missing_df[missing_df["condition"] == "All_Available"]["pr_auc"].values[0]}
    ])
    gru_contrib_df.to_csv("gru_fusion_contribution.csv", index=False)

if __name__ == "__main__":
    run_ablation()
