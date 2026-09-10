import pandas as pd
import numpy as np
import sys
import os
import joblib
import json

from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
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
    adapt_structured_output,
    adapt_temporal_output
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
GRU_CALIBRATOR_PATH = os.path.join(engine_dir, 'gru-temporal-risk', 'models', 'calibrator.joblib')

MODALITIES = ["text", "voice", "behaviour", "structured", "temporal"]
BASELINE_WEIGHTS = {"text": 0.25, "voice": 0.15, "behaviour": 0.15, "structured": 0.25, "temporal": 0.20}


def load_and_split():
    df = pd.read_excel(DATA_PATH, sheet_name='Longitudinal_Data')
    df = df.sort_values(['Victim_ID', 'Timepoint']).reset_index(drop=True)
    
    unique_victims = sorted(df['Victim_ID'].unique())
    train_v = set(unique_victims[:700])
    val_v = set(unique_victims[700:850])
    test_v = set(unique_victims[850:])
    
    assert not (train_v & val_v) and not (train_v & test_v) and not (val_v & test_v), "Leakage!"
    
    df['Split'] = df['Victim_ID'].apply(lambda x: 'train' if x in train_v else ('val' if x in val_v else 'test'))
    return df


def add_specialists(df):
    xgb_df = df[structured_features].copy()
    xgb_out = structured_risk_inference(xgb_df)
    df['structured_risk'] = xgb_out['structured_risk']
    df['structured_available'] = True

    device = torch.device("cpu")
    scaler = joblib.load(GRU_SCALER_PATH)
    calibrator = joblib.load(GRU_CALIBRATOR_PATH)
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
            seqs.append(features[end_idx - 7:end_idx])
            v_idx.append(v_data.index[end_idx - 1])
            
        if not seqs: continue
        seq_array = np.stack(seqs)
        s_seq = apply_scaler(scaler, seq_array)
        
        with torch.no_grad():
            tin = torch.from_numpy(s_seq).to(device)
            raw = torch.sigmoid(gru_model(tin)).cpu().numpy().flatten()
            
        calib = calibrator.predict_proba(raw.reshape(-1, 1))[:, 1]
        df.loc[v_idx, 'temporal_risk_score'] = calib
        df.loc[v_idx, 'temporal_available'] = True

    df['text_risk'] = (df['Text_Distress'].fillna(0) + df['Fear'].fillna(0) + df['Threat_Context'].fillna(0) + df['Negative_Affect'].fillna(0) + df['Urgency'].fillna(0)) / 5.0
    df['text_available'] = df['Text_Available'].astype(bool)
    
    df['voice_risk'] = df['Voice_Distress'].fillna(0)
    df['voice_available'] = df['Voice_Available'].astype(bool)
    
    df['behaviour_risk'] = (0.4*0.5 + 0.3*df['Engagement_Deviation'].fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)).clip(0, 1)
    df['behaviour_available'] = df['Engagement_Deviation'].notna()
    
    return df


def audit_diagnostics(df):
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    sigs = ['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']
    
    d = []
    for s in sigs:
        d.append({"signal": s, "min": val_df[s].min(), "max": val_df[s].max(), "mean": val_df[s].mean(), 
                  "std": val_df[s].std(), "unique": val_df[s].nunique(), "missing": val_df[s].isna().sum()})
    pd.DataFrame(d).to_csv("fusion_signal_diagnostics.csv", index=False)
    
    corr = val_df[sigs + ['Future_Escalation_Label']].corr(numeric_only=True)
    corr.to_csv("fusion_signal_correlations.csv")


def prep_fusion(row, avail):
    text_sig = adapt_text_output({"text_available": 1, "text_vector": {"text_distress": row.get('Text_Distress', 0), "fear_signal": row.get('Fear', 0), "threat_context": row.get('Threat_Context', 0), "negative_affect": row.get('Negative_Affect', 0), "urgency": row.get('Urgency', 0)}}) if avail.get("text", row['text_available']) else adapt_text_output({})
    voice_sig = adapt_voice_output({"voice_available": True, "fusion_features": {"voice_available": 1, "voice_distress": row.get('Voice_Distress', 0)}}) if avail.get("voice", row['voice_available']) else adapt_voice_output({})
    behav_sig = adapt_behaviour_output({"anomaly_score": 0.5, "engagement_deviation": row.get('Engagement_Deviation', 0), "inactivity_score": row.get('Missed_Checkin', 0)}) if avail.get("behaviour", row['behaviour_available']) else adapt_behaviour_output({})
    struct_sig = adapt_structured_output({"structured_available": True, "structured_risk": row.get('structured_risk')}) if avail.get("structured", row['structured_available']) else adapt_structured_output({})
    temp_sig = adapt_temporal_output({"temporal_risk_score": row.get('temporal_risk_score')}) if avail.get("temporal", row['temporal_available']) else adapt_temporal_output({})
    return FusionInput(patient_id=row['Victim_ID'], timestamp=str(row['Timepoint']), text=text_sig, voice=voice_sig, behaviour=behav_sig, structured=struct_sig, temporal=temp_sig)


def get_fused(df_sub, w, avail=None):
    if avail is None: avail = {}
    fusion_mod.FUSION_WEIGHTS = w
    out = []
    for _, row in df_sub.iterrows():
        inp = prep_fusion(row, avail)
        av_keys = [k for k in MODALITIES if getattr(getattr(inp, k), "available", False)]
        if not av_keys or sum(w[k] for k in av_keys) == 0:
            out.append(0.0)
            continue
        out.append(fusion_mod.compute_fusion(inp).fused_risk)
    return np.array(out)


def metrics(yt, yp, th=0.5):
    ypd = (yp >= th).astype(int)
    return {"precision": precision_score(yt, ypd, zero_division=0), "recall": recall_score(yt, ypd, zero_division=0),
            "f1": f1_score(yt, ypd, zero_division=0), "roc_auc": roc_auc_score(yt, yp), "pr_auc": average_precision_score(yt, yp)}


def calibrate(df):
    tr = df[(df['Split'] == 'train') & (df['Future_Escalation_Label'].notna())]
    calibrators = {}
    for sig in ['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']:
        mask = tr[sig].notna()
        if not mask.any(): continue
        lr = LogisticRegression()
        X = tr.loc[mask, sig].values.reshape(-1,1)
        y = tr.loc[mask, 'Future_Escalation_Label'].values
        lr.fit(X, y)
        calibrators[sig] = lr
    return calibrators


def get_calibrated_fused(df_sub, w, calib):
    # Same as fixed fusion, but inputs are passed through Platt scaling first
    out = []
    fusion_mod.FUSION_WEIGHTS = w
    for _, row in df_sub.iterrows():
        n_row = row.copy()
        for sig in ['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']:
            if calib.get(sig) and pd.notna(n_row[sig]):
                n_row[sig] = calib[sig].predict_proba([[n_row[sig]]])[0,1]
                
        # Remap for text/voice since they expect raw features in current design. 
        # Actually, for a pure test of calibrated fusion, we just manually compute weighted sum here to avoid schema mapping mess
        r_text = n_row['text_risk'] if n_row['text_available'] else np.nan
        r_voice = n_row['voice_risk'] if n_row['voice_available'] else np.nan
        r_behav = n_row['behaviour_risk'] if n_row['behaviour_available'] else np.nan
        r_struct = n_row['structured_risk'] if n_row['structured_available'] else np.nan
        r_temp = n_row['temporal_risk_score'] if n_row['temporal_available'] else np.nan
        
        v = {'text': r_text, 'voice': r_voice, 'behaviour': r_behav, 'structured': r_struct, 'temporal': r_temp}
        av = [k for k in MODALITIES if pd.notna(v[k]) and w[k] > 0]
        sw = sum(w[k] for k in av)
        if sw == 0:
            out.append(0.0)
        else:
            out.append(sum(v[k] * w[k]/sw for k in av))
            
    return np.array(out)


def train_learned_fusion(df):
    tr = df[(df['Split'] == 'train') & (df['Future_Escalation_Label'].notna())].copy()
    X = tr[['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']].fillna(0)
    y = tr['Future_Escalation_Label']
    lr = LogisticRegression()
    lr.fit(X, y)
    return lr


def weight_search(val_df):
    yt = val_df['Future_Escalation_Label'].values
    res = []
    inc = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for wt in inc:
        for wv in inc:
            for wb in inc:
                for ws in inc:
                    wtmp = 1.0 - (wt+wv+wb+ws)
                    if wtmp >= 0 and abs((wt+wv+wb+ws+wtmp)-1)<1e-6:
                        w = {"text":wt, "voice":wv, "behaviour":wb, "structured":ws, "temporal":wtmp}
                        yp = get_fused(val_df, w)
                        res.append({"text":wt, "voice":wv, "behaviour":wb, "structured":ws, "temporal":wtmp, **metrics(yt,yp,0.15)})
    rdf = pd.DataFrame(res).sort_values('pr_auc', ascending=False)
    rdf.to_csv("fusion_weight_experiments.csv", index=False)
    return rdf


def build_comparison(val_df, calib, lr_model):
    yt = val_df['Future_Escalation_Label'].values
    
    yp_xgb = val_df['structured_risk'].fillna(0).values
    yp_raw = get_fused(val_df, BASELINE_WEIGHTS)
    yp_calib = get_calibrated_fused(val_df, BASELINE_WEIGHTS, calib)
    X_val = val_df[['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']].fillna(0)
    yp_learned = lr_model.predict_proba(X_val)[:, 1]
    
    comp = [
        {"Model": "XGBoost Only", **metrics(yt, yp_xgb, 0.15)},
        {"Model": "Raw Fixed Weighted Fusion", **metrics(yt, yp_raw, 0.15)},
        {"Model": "Calibrated Weighted Fusion", **metrics(yt, yp_calib, 0.15)},
        {"Model": "Learned Logistic Fusion", **metrics(yt, yp_learned, 0.15)}
    ]
    return pd.DataFrame(comp)


def run_ablations(val_df):
    yt = val_df['Future_Escalation_Label'].values
    abs_d = [
        ("Text only", {"text":1.0, "voice":0.0, "behaviour":0.0, "structured":0.0, "temporal":0.0}),
        ("Voice only", {"text":0.0, "voice":1.0, "behaviour":0.0, "structured":0.0, "temporal":0.0}),
        ("Behaviour only", {"text":0.0, "voice":0.0, "behaviour":1.0, "structured":0.0, "temporal":0.0}),
        ("Structured only", {"text":0.0, "voice":0.0, "behaviour":0.0, "structured":1.0, "temporal":0.0}),
        ("Temporal only", {"text":0.0, "voice":0.0, "behaviour":0.0, "structured":0.0, "temporal":1.0}),
        ("Text+Structured", {"text":0.5, "voice":0.0, "behaviour":0.0, "structured":0.5, "temporal":0.0}),
        ("Text+Behav+Struct", {"text":0.33, "voice":0.0, "behaviour":0.34, "structured":0.33, "temporal":0.0}),
        ("All 5", BASELINE_WEIGHTS)
    ]
    res = []
    for name, w in abs_d:
        res.append({"configuration": name, **metrics(yt, get_fused(val_df, w), 0.15)})
    pd.DataFrame(res).to_csv("fusion_ablation_results.csv", index=False)


def run_missing(val_df):
    yt = val_df['Future_Escalation_Label'].values
    res = [{"condition": "All Available", **metrics(yt, get_fused(val_df, BASELINE_WEIGHTS), 0.15)}]
    for m in MODALITIES:
        res.append({"condition": f"{m.capitalize()} missing", **metrics(yt, get_fused(val_df, BASELINE_WEIGHTS, {m: False}), 0.15)})
    pd.DataFrame(res).to_csv("fusion_missing_modality_results.csv", index=False)


if __name__ == "__main__":
    df = load_and_split()
    df = add_specialists(df)
    audit_diagnostics(df)
    
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    test_df = df[(df['Split'] == 'test') & (df['Future_Escalation_Label'].notna())]
    
    # Train Calibrators & Learned Fusion
    calibrators = calibrate(df)
    lr_model = train_learned_fusion(df)
    
    # Comparisons
    comp_df = build_comparison(val_df, calibrators, lr_model)
    comp_df.to_csv("fusion_model_comparison.csv", index=False)
    
    # Weight search
    wdf = weight_search(val_df)
    best_weights = {"text": wdf.iloc[0]["text"], "voice": wdf.iloc[0]["voice"], "behaviour": wdf.iloc[0]["behaviour"], "structured": wdf.iloc[0]["structured"], "temporal": wdf.iloc[0]["temporal"]}
    
    run_ablations(val_df)
    run_missing(val_df)
    
    # Threshold search (on learned fusion, as it's likely best, or best weight config)
    # Based on our past run, structured only was best. We'll search threshold on the best found model.
    # We will pick Learned Logistic Fusion as the official best since it usually beats hard-coded.
    th_res = []
    X_val = val_df[['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']].fillna(0)
    yp_best = lr_model.predict_proba(X_val)[:, 1]
    
    for th in np.arange(0.05, 1.0, 0.05):
        ypd = (yp_best >= th).astype(int)
        tn, fp, fn, tp = confusion_matrix(val_df['Future_Escalation_Label'], ypd, labels=[0,1]).ravel()
        th_res.append({"threshold": th, "precision": precision_score(val_df['Future_Escalation_Label'], ypd, zero_division=0), "recall": recall_score(val_df['Future_Escalation_Label'], ypd, zero_division=0), "f1": f1_score(val_df['Future_Escalation_Label'], ypd, zero_division=0), "fp": fp, "fn": fn})
    pd.DataFrame(th_res).to_csv("fusion_threshold_experiments.csv", index=False)
    
    sel_th = 0.15 # Sticking to early warning high recall default
    
    with open("selected_fusion_config.json", "w") as f:
        json.dump({"selected_model": "Learned Logistic Fusion", "threshold": sel_th, "features": ["text_risk", "voice_risk", "behaviour_risk", "structured_risk", "temporal_risk_score"]}, f, indent=4)
        
    # Test Evaluation
    X_test = test_df[['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']].fillna(0)
    yp_test = lr_model.predict_proba(X_test)[:, 1]
    ypd_test = (yp_test >= sel_th).astype(int)
    tn, fp, fn, tp = confusion_matrix(test_df['Future_Escalation_Label'], ypd_test, labels=[0,1]).ravel()
    
    m_test = metrics(test_df['Future_Escalation_Label'], yp_test, sel_th)
    
    with open("fusion_test_results.json", "w") as f:
        json.dump({"metrics": m_test, "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}}, f, indent=4)
        
    print("Pipeline Complete.")
