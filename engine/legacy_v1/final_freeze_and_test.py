import pandas as pd
import numpy as np
import sys
import os
import joblib
import json

from evaluate_medha_pipeline import load_and_split, add_specialists, get_fused, dds_metrics

from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def main():
    with open('results/frozen_config.json', 'r') as f:
        config = json.load(f)
        
    best_th = config['best_gru_threshold']
    dds_weights = config['dds_weights']
    
    df = load_and_split()
    df = add_specialists(df)
    
    test_df = df[df['Split'] == 'test']
    
    # DDS Test Evaluation
    yt = test_df['DDS'].values
    yp = get_fused(test_df, dds_weights)
    m = dds_metrics(yt, yp)
    
    res_dds = [{
        "metric_type": "DDS_Test",
        "mae": m["mae"], "rmse": m["rmse"], "r2": m["r2"], "pearson": m["pearson"], "spearman": m["spearman"],
        "pred_mean": np.nanmean(yp), "pred_std": np.nanstd(yp), "pred_min": np.nanmin(yp), "pred_max": np.nanmax(yp),
        "ref_mean": np.nanmean(yt), "ref_std": np.nanstd(yt), "ref_min": np.nanmin(yt), "ref_max": np.nanmax(yt)
    }]
    pd.DataFrame(res_dds).to_csv("results/03_dds_test.csv", index=False)
    
    # GRU Test Evaluation
    test_sub = test_df[test_df['Future_Escalation_Label'].notna()]
    yt_gru = test_sub['Future_Escalation_Label'].values
    yp_gru = test_sub['temporal_risk_score'].fillna(0).values
    
    pr = average_precision_score(yt_gru, yp_gru)
    roc = roc_auc_score(yt_gru, yp_gru)
    
    ypd = (yp_gru >= best_th).astype(int)
    tn, fp, fn, tp = confusion_matrix(yt_gru, ypd, labels=[0,1]).ravel()
    spec = tn / (tn+fp) if (tn+fp)>0 else 0
    brier = np.mean((yp_gru - yt_gru)**2)
    
    res_gru = [{
        "pr_auc": pr, "roc_auc": roc, "precision": precision_score(yt_gru, ypd, zero_division=0),
        "recall": recall_score(yt_gru, ypd, zero_division=0), "f1": f1_score(yt_gru, ypd, zero_division=0),
        "brier": brier, "specificity": spec, "tn": tn, "fp": fp, "fn": fn, "tp": tp, "threshold": best_th
    }]
    pd.DataFrame(res_gru).to_csv("results/08_gru_test.csv", index=False)
    
    # Generate Baseline Comparison (10_baseline_comparison.csv)
    # Using Validation performance for the comparison table as requested (or both)
    # We will compute the final TEST baselines here.
    maj_pred = np.zeros(len(yt_gru))
    pr_maj = average_precision_score(yt_gru, maj_pred)
    yp_struct_gru = test_sub['structured_risk'].fillna(0).values
    pr_struct = average_precision_score(yt_gru, yp_struct_gru)
    
    yp_struct_dds = get_fused(test_df, {"text":0, "voice":0, "behaviour":0, "structured":1})
    dds_struct_m = dds_metrics(yt, yp_struct_dds)
    
    comp = [
        {"Task": "DDS", "Model": "Mean Reference Baseline", "Metric": "MAE", "Value": dds_metrics(yt, np.full(len(yt), np.nanmean(yt)))['mae']},
        {"Task": "DDS", "Model": "Structured Only", "Metric": "MAE", "Value": dds_struct_m['mae']},
        {"Task": "DDS", "Model": "Final Fusion", "Metric": "MAE", "Value": m['mae']},
        {"Task": "Future Escalation", "Model": "Majority Class", "Metric": "PR-AUC", "Value": pr_maj},
        {"Task": "Future Escalation", "Model": "Structured Current Only (Non-temporal)", "Metric": "PR-AUC", "Value": pr_struct},
        {"Task": "Future Escalation", "Model": "Final GRU", "Metric": "PR-AUC", "Value": pr}
    ]
    pd.DataFrame(comp).to_csv("results/10_baseline_comparison.csv", index=False)

if __name__ == "__main__":
    main()
