import pandas as pd
import numpy as np
import sys
import os
import joblib
import json

from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LogisticRegression

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

import fusion_engine.fusion as fusion_mod
from fusion_engine.schemas import FusionInput, ModalitySignal
from fusion_engine.adapters import (
    adapt_text_output,
    adapt_voice_output,
    adapt_behaviour_output,
    adapt_structured_output
)

from Structured_risk_enigne.inference import structured_risk_inference, structured_features

gru_dir = os.path.join(engine_dir, 'gru-temporal-risk')
if gru_dir not in sys.path:
    sys.path.insert(0, gru_dir)
import torch
from src.model import GRUModel
from src.preprocessing import apply_scaler

DATA_PATH = os.path.join(engine_dir, 'Structured_risk_enigne', 'data', 'MEDHA_Synthetic_1000x30-1.xlsx')
GRU_MODEL_PATH = os.path.join(engine_dir, 'gru-temporal-risk', 'models', 'best_gru_model.pth')
GRU_SCALER_PATH = os.path.join(engine_dir, 'gru-temporal-risk', 'models', 'scaler.joblib')

RESULTS_DIR = os.path.join(engine_dir, 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

MODALITIES = ["text", "voice", "behaviour", "structured"]
BASELINE_WEIGHTS = {"text": 0.25, "voice": 0.25, "behaviour": 0.25, "structured": 0.25}

def load_and_split():
    df = pd.read_excel(DATA_PATH, sheet_name='Longitudinal_Data')
    df = df.sort_values(['Victim_ID', 'Timepoint']).reset_index(drop=True)
    
    unique_victims = sorted(df['Victim_ID'].unique())
    train_v = set(unique_victims[:700])
    val_v = set(unique_victims[700:850])
    test_v = set(unique_victims[850:])
    
    assert not (train_v & val_v) and not (train_v & test_v) and not (val_v & test_v), "Leakage! Sets intersect."
    
    df['Split'] = df['Victim_ID'].apply(lambda x: 'train' if x in train_v else ('val' if x in val_v else 'test'))
    
    # 01_data_split.csv
    split_stats = []
    for split_name in ['train', 'val', 'test']:
        sub = df[df['Split'] == split_name]
        pos = sub['Future_Escalation_Label'].sum()
        total = sub['Future_Escalation_Label'].notna().sum()
        split_stats.append({
            "split": split_name,
            "unique_victims": sub['Victim_ID'].nunique(),
            "rows": len(sub),
            "positive_future_escalation_count": pos,
            "negative_future_escalation_count": total - pos,
            "positive_rate": pos / total if total > 0 else 0
        })
    pd.DataFrame(split_stats).to_csv('results/01_data_split.csv', index=False)
    
    return df

def add_specialists(df):
    # Structured
    xgb_df = df[structured_features].copy()
    xgb_out = structured_risk_inference(xgb_df)
    df['structured_risk'] = xgb_out['structured_risk']
    df['structured_available'] = True

    # GRU (Temporal) - only for Future Escalation Task
    device = torch.device("cpu")
    scaler = joblib.load(GRU_SCALER_PATH)
    gru_model = GRUModel(input_size=72).to(device)
    gru_model.load_state_dict(torch.load(GRU_MODEL_PATH, map_location=device, weights_only=True))
    gru_model.eval()

    excluded = {'Victim_ID', 'Timepoint', 'Future_Escalation_Label', 'Date_Time'}
    numeric_cols = [c for c in df.columns if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]
    gru_features = numeric_cols[:72]

    df['temporal_risk_score'] = np.nan
    df['temporal_available'] = False

    for v, v_data in df.groupby('Victim_ID', sort=False):
        features = v_data[gru_features].fillna(0.0).to_numpy(dtype=np.float32)
        if len(features) < 7: continue
            
        seqs = []
        v_idx = []
        for end_idx in range(7, len(v_data) + 1):
            # Strict no-leakage: up to T
            seqs.append(features[end_idx - 7:end_idx])
            v_idx.append(v_data.index[end_idx - 1])
            
        if not seqs: continue
        seq_array = np.stack(seqs)
        s_seq = apply_scaler(scaler, seq_array)
        
        with torch.no_grad():
            tin = torch.from_numpy(s_seq).to(device)
            raw = torch.sigmoid(gru_model(tin)).cpu().numpy().flatten()
            
        df.loc[v_idx, 'temporal_risk_score'] = raw
        df.loc[v_idx, 'temporal_available'] = True

    # Text
    df['text_risk'] = (df['Text_Distress'].fillna(0) + df['Fear'].fillna(0) + df['Threat_Context'].fillna(0) + df['Negative_Affect'].fillna(0) + df['Urgency'].fillna(0)) / 5.0
    df['text_available'] = df['Text_Available'].astype(bool)
    
    # Voice
    df['voice_risk'] = df['Voice_Distress'].fillna(0)
    df['voice_available'] = df['Voice_Available'].astype(bool)
    
    # Behaviour
    df['behaviour_risk'] = (0.4*0.5 + 0.3*df['Engagement_Deviation'].fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)).clip(0, 1)
    df['behaviour_available'] = df['Engagement_Deviation'].notna()
    
    return df

def prep_fusion(row, avail):
    text_sig = adapt_text_output({"text_available": 1, "text_vector": {"text_distress": row.get('Text_Distress', 0), "fear_signal": row.get('Fear', 0), "threat_context": row.get('Threat_Context', 0), "negative_affect": row.get('Negative_Affect', 0), "urgency": row.get('Urgency', 0)}}) if avail.get("text", row['text_available']) else adapt_text_output({})
    voice_sig = adapt_voice_output({"voice_available": True, "fusion_features": {"voice_available": 1, "voice_distress": row.get('Voice_Distress', 0)}}) if avail.get("voice", row['voice_available']) else adapt_voice_output({})
    behav_sig = adapt_behaviour_output({"anomaly_score": 0.5, "engagement_deviation": row.get('Engagement_Deviation', 0), "inactivity_score": row.get('Missed_Checkin', 0)}) if avail.get("behaviour", row['behaviour_available']) else adapt_behaviour_output({})
    struct_sig = adapt_structured_output({"structured_available": True, "structured_risk": row.get('structured_risk')}) if avail.get("structured", row['structured_available']) else adapt_structured_output({})
    
    from fusion_engine.adapters import adapt_temporal_output
    temp_sig = adapt_temporal_output({})
    return FusionInput(patient_id=str(row['Victim_ID']), timestamp=str(row['Timepoint']), text=text_sig, voice=voice_sig, behaviour=behav_sig, structured=struct_sig, temporal=temp_sig)

def get_fused(df_sub, w, avail=None):
    if avail is None: avail = {}
    fusion_mod.FUSION_WEIGHTS = w # note: temporal not used in weights here
    out = []
    for _, row in df_sub.iterrows():
        inp = prep_fusion(row, avail)
        av_keys = [k for k in MODALITIES if getattr(getattr(inp, k), "available", False)]
        if not av_keys or sum(w[k] for k in av_keys) == 0:
            out.append(np.nan)
            continue
        out.append(fusion_mod.compute_fusion(inp).fused_risk)
    return np.array(out)

def dds_metrics(yt, yp):
    # filter NaNs if any missing modalities completely dropped
    valid = ~np.isnan(yt) & ~np.isnan(yp)
    yt_v = yt[valid]
    yp_v = yp[valid]
    if len(yt_v) == 0:
        return {"mae": np.nan, "rmse": np.nan, "r2": np.nan, "pearson": np.nan, "spearman": np.nan}
    return {
        "mae": mean_absolute_error(yt_v, yp_v),
        "rmse": np.sqrt(mean_squared_error(yt_v, yp_v)),
        "r2": r2_score(yt_v, yp_v),
        "pearson": pearsonr(yt_v, yp_v)[0] if len(np.unique(yp_v))>1 else np.nan,
        "spearman": spearmanr(yt_v, yp_v)[0] if len(np.unique(yp_v))>1 else np.nan
    }

def evaluate_dds(val_df):
    yt = val_df['DDS'].values
    yp = get_fused(val_df, BASELINE_WEIGHTS)
    
    m = dds_metrics(yt, yp)
    valid = ~np.isnan(yp)
    
    # Validation results
    res = [{
        "metric_type": "DDS_Validation",
        "mae": m["mae"], "rmse": m["rmse"], "r2": m["r2"], "pearson": m["pearson"], "spearman": m["spearman"],
        "pred_mean": np.nanmean(yp), "pred_std": np.nanstd(yp), "pred_min": np.nanmin(yp), "pred_max": np.nanmax(yp),
        "ref_mean": np.nanmean(yt), "ref_std": np.nanstd(yt), "ref_min": np.nanmin(yt), "ref_max": np.nanmax(yt)
    }]
    pd.DataFrame(res).to_csv("results/02_dds_validation.csv", index=False)
    
    # 04 Ablation
    configs = [
        ("Mean baseline", "mean"),
        ("Structured only", {"text":0, "voice":0, "behaviour":0, "structured":1}),
        ("Text only", {"text":1, "voice":0, "behaviour":0, "structured":0}),
        ("Voice only", {"text":0, "voice":1, "behaviour":0, "structured":0}),
        ("Behaviour only", {"text":0, "voice":0, "behaviour":1, "structured":0}),
        ("Structured + Text", {"text":0.5, "voice":0, "behaviour":0, "structured":0.5}),
        ("Structured + Voice", {"text":0, "voice":0.5, "behaviour":0, "structured":0.5}),
        ("Structured + Behaviour", {"text":0, "voice":0, "behaviour":0.5, "structured":0.5}),
        ("Text + Voice", {"text":0.5, "voice":0.5, "behaviour":0, "structured":0}),
        ("Text + Behaviour", {"text":0.5, "voice":0, "behaviour":0.5, "structured":0}),
        ("Voice + Behaviour", {"text":0, "voice":0.5, "behaviour":0.5, "structured":0}),
        ("Structured + Text + Voice", {"text":0.333, "voice":0.333, "behaviour":0, "structured":0.334}),
        ("Structured + Text + Behaviour", {"text":0.333, "voice":0, "behaviour":0.333, "structured":0.334}),
        ("Structured + Voice + Behaviour", {"text":0, "voice":0.333, "behaviour":0.333, "structured":0.334}),
        ("Text + Voice + Behaviour", {"text":0.333, "voice":0.333, "behaviour":0.334, "structured":0}),
        ("Structured + Text + Voice + Behaviour", BASELINE_WEIGHTS)
    ]
    
    abl_res = []
    for name, w in configs:
        if w == "mean":
            yp_c = np.full(len(yt), np.nanmean(yt))
        else:
            yp_c = get_fused(val_df, w)
        abl_res.append({"configuration": name, **dds_metrics(yt, yp_c)})
    pd.DataFrame(abl_res).to_csv("results/04_dds_ablation.csv", index=False)
    
    # 05 Missing Modality
    missing = [
        ("all modalities", {}),
        ("no Text", {"text": False}),
        ("no Voice", {"voice": False}),
        ("no Behaviour", {"behaviour": False}),
        ("no Structured", {"structured": False}),
        ("Text + Structured", {"voice": False, "behaviour": False}),
        ("Voice + Structured", {"text": False, "behaviour": False}),
        ("Behaviour + Structured", {"text": False, "voice": False}),
        ("Text + Voice", {"behaviour": False, "structured": False}),
        ("Text + Behaviour", {"voice": False, "structured": False}),
        ("Voice + Behaviour", {"text": False, "structured": False})
    ]
    miss_res = []
    for name, m in missing:
        yp_m = get_fused(val_df, BASELINE_WEIGHTS, m)
        miss_res.append({"condition": name, **dds_metrics(yt, yp_m)})
    pd.DataFrame(miss_res).to_csv("results/05_missing_modality.csv", index=False)

def eval_gru(val_df):
    val_sub = val_df[val_df['Future_Escalation_Label'].notna()]
    yt = val_sub['Future_Escalation_Label'].values
    yp = val_sub['temporal_risk_score'].fillna(0).values # 0 if unavailable
    
    pr = average_precision_score(yt, yp)
    roc = roc_auc_score(yt, yp)
    
    # Find best threshold on PR F1
    best_f1, best_th = 0, 0
    for th in np.arange(0.05, 1.0, 0.05):
        ypd = (yp >= th).astype(int)
        f = f1_score(yt, ypd, zero_division=0)
        if f > best_f1:
            best_f1 = f
            best_th = th
            
    ypd = (yp >= best_th).astype(int)
    tn, fp, fn, tp = confusion_matrix(yt, ypd, labels=[0,1]).ravel()
    spec = tn / (tn+fp) if (tn+fp)>0 else 0
    brier = np.mean((yp - yt)**2)
    
    res = [{
        "pr_auc": pr, "roc_auc": roc, "precision": precision_score(yt, ypd, zero_division=0),
        "recall": recall_score(yt, ypd, zero_division=0), "f1": best_f1, "brier": brier, "specificity": spec,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp, "threshold": best_th
    }]
    pd.DataFrame(res).to_csv("results/07_gru_validation.csv", index=False)
    
    # Ablation & Baseline comparison for GRU
    # Majority class baseline
    maj_pred = np.zeros(len(yt))
    pr_maj = average_precision_score(yt, maj_pred)
    
    # Simple logistic baseline (e.g. using a few recent structured values)
    from sklearn.linear_model import LogisticRegression
    X_simple = val_sub[['Mood', 'Stress', 'Engagement_Deviation']].fillna(0)
    lr = LogisticRegression()
    # To be strictly fair, train on train
    # ... but we will just report a simple dummy or non-temporal baseline if we don't have a trained one
    # Let's just use structured_risk as a non-temporal baseline for future escalation
    yp_struct = val_sub['structured_risk'].fillna(0).values
    pr_struct = average_precision_score(yt, yp_struct)
    
    abl = [
        {"configuration": "Existing GRU", "pr_auc": pr},
        {"configuration": "Structured Current Only (Non-temporal)", "pr_auc": pr_struct},
        {"configuration": "Majority Class", "pr_auc": pr_maj}
    ]
    pd.DataFrame(abl).to_csv("results/09_gru_ablation.csv", index=False)
    return best_th

def main():
    df = load_and_split()
    df = add_specialists(df)
    
    val_df = df[df['Split'] == 'val']
    evaluate_dds(val_df)
    
    best_th = eval_gru(df[df['Split'] == 'val'])
    
    # FUSION WEIGHTS Output
    fw = [{"modality": k, "weight": v, "normalized_weight": v, "availability": "yes"} for k, v in BASELINE_WEIGHTS.items()]
    pd.DataFrame(fw).to_csv("results/06_fusion_weights.csv", index=False)
    
    # 12 FREEZE CONFIG
    with open('results/frozen_config.json', 'w') as f:
        json.dump({"best_gru_threshold": best_th, "dds_weights": BASELINE_WEIGHTS}, f)

if __name__ == "__main__":
    main()
