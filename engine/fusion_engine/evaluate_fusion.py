import pandas as pd
import numpy as np
import sys
import os
import joblib

from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

# Add engine directory to path to allow absolute imports for engines
engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

# Import Fusion Engine
from fusion_engine.schemas import FusionInput, ModalitySignal
import fusion_engine.fusion as fusion_mod
from fusion_engine.adapters import (
    adapt_text_output,
    adapt_voice_output,
    adapt_behaviour_output,
    adapt_structured_output,
    adapt_temporal_output
)

# Import XGBoost engine
from Structured_risk_enigne.inference import structured_risk_inference, structured_features

# Import GRU engine components
gru_dir = os.path.join(engine_dir, 'gru-temporal-risk')
if gru_dir not in sys.path:
    sys.path.insert(0, gru_dir)
import torch
from src.model import GRUModel
from src.preprocessing import apply_scaler
from src.sequence_builder import build_sliding_windows


# ============================================================
# CONFIGURATION
# ============================================================
DATA_PATH = os.path.join(engine_dir, 'Structured_risk_enigne', 'data', 'MEDHA_Synthetic_1000x30-1.xlsx')

GRU_MODEL_PATH = os.path.join(engine_dir, 'gru-temporal-risk', 'models', 'best_gru_model.pth')
GRU_SCALER_PATH = os.path.join(engine_dir, 'gru-temporal-risk', 'models', 'scaler.joblib')
GRU_CALIBRATOR_PATH = os.path.join(engine_dir, 'gru-temporal-risk', 'models', 'calibrator.joblib')

MODALITIES = ["text", "voice", "behaviour", "structured", "temporal"]
BASELINE_WEIGHTS = {"text": 0.25, "voice": 0.15, "behaviour": 0.15, "structured": 0.25, "temporal": 0.20}


def load_dataset_and_verify_split():
    """Load dataset, split by victim, and strictly verify intersections."""
    print("Loading dataset and verifying split...")
    df = pd.read_excel(DATA_PATH, sheet_name='Longitudinal_Data')
    
    # Store rows before sorting
    rows_before = len(df)
    df = df.sort_values(['Victim_ID', 'Timepoint']).reset_index(drop=True)
    rows_after = len(df)
    
    unique_victims = sorted(df['Victim_ID'].unique())
    
    # Deterministic split as original: 700 Train, 150 Val, 150 Test
    train_victims = set(unique_victims[:700])
    val_victims = set(unique_victims[700:850])
    test_victims = set(unique_victims[850:])
    
    print("\n--- SPLIT VERIFICATION ---")
    print(f"Total Rows Before Sort: {rows_before}")
    print(f"Total Rows After Sort: {rows_after}")
    print(f"Train victims: {len(train_victims)}")
    print(f"Val victims: {len(val_victims)}")
    print(f"Test victims: {len(test_victims)}")
    
    assert len(train_victims.intersection(val_victims)) == 0, "Leakage: Train intersects Val"
    assert len(train_victims.intersection(test_victims)) == 0, "Leakage: Train intersects Test"
    assert len(val_victims.intersection(test_victims)) == 0, "Leakage: Val intersects Test"
    print("Zero intersection verified across all splits. No victim-level leakage.")
    print("--------------------------\n")
    
    df['Split'] = df['Victim_ID'].apply(
        lambda x: 'train' if x in train_victims else ('val' if x in val_victims else 'test')
    )
    return df


def generate_specialist_predictions(df):
    """Generate risk predictions from all engines without leakage."""
    print("Generating XGBoost Structured predictions...")
    
    # 1. Structured Risk (XGBoost)
    xgb_df = df[structured_features].copy()
    xgb_out = structured_risk_inference(xgb_df)
    df['structured_risk'] = xgb_out['structured_risk']
    df['structured_available'] = True

    # 2. Temporal Risk (GRU)
    print("Generating GRU Temporal predictions...")
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

    for victim_id, victim_data in df.groupby('Victim_ID', sort=False):
        features = victim_data[gru_features].fillna(0.0).to_numpy(dtype=np.float32)
        window_size = 7
        if len(features) < window_size:
            continue
            
        sequences = []
        valid_indices = []
        for end_idx in range(window_size, len(victim_data) + 1):
            sequences.append(features[end_idx - window_size:end_idx])
            valid_indices.append(victim_data.index[end_idx - 1])
            
        if not sequences:
            continue
            
        seq_array = np.stack(sequences)
        scaled_seq = apply_scaler(scaler, seq_array)
        
        with torch.no_grad():
            tensor_in = torch.from_numpy(scaled_seq).to(device)
            raw_prob = torch.sigmoid(gru_model(tensor_in)).cpu().numpy().flatten()
            
        calibrated_prob = calibrator.predict_proba(raw_prob.reshape(-1, 1))[:, 1]
        
        df.loc[valid_indices, 'temporal_risk_score'] = calibrated_prob
        df.loc[valid_indices, 'temporal_available'] = True

    print("Computing other modality risks directly into dataframe for diagnostic audit...")
    # Text
    df['text_risk'] = (df['Text_Distress'].fillna(0) + df['Fear'].fillna(0) + 
                       df['Threat_Context'].fillna(0) + df['Negative_Affect'].fillna(0) + 
                       df['Urgency'].fillna(0)) / 5.0
    df['text_available'] = df['Text_Available'].astype(bool)
    
    # Voice
    df['voice_risk'] = df['Voice_Distress'].fillna(0)
    df['voice_available'] = df['Voice_Available'].astype(bool)
    
    # Behaviour (Anomaly score defaults to 0.5 for synthetic data as actual isolation forest is not run here)
    # The actual Behaviour Engine takes the absolute value of deviation. We must replicate that here.
    df['behaviour_risk'] = 0.4*0.5 + 0.3*df['Engagement_Deviation'].abs().fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)
    df['behaviour_risk'] = df['behaviour_risk'].clip(0, 1)
    df['behaviour_available'] = df['Engagement_Deviation'].notna()
    
    return df


def run_diagnostic_audit(df):
    """Generate diagnostic table for Validation set signals."""
    print("Running diagnostic audit on Validation set...")
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    
    signals = ['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']
    
    diag_data = []
    for sig in signals:
        s_data = val_df[sig]
        diag_data.append({
            "signal": sig,
            "min": s_data.min(),
            "max": s_data.max(),
            "mean": s_data.mean(),
            "std": s_data.std(),
            "number_unique": s_data.nunique(),
            "number_missing": s_data.isna().sum()
        })
        
    diag_df = pd.DataFrame(diag_data)
    diag_df.to_csv("fusion_signal_diagnostics.csv", index=False)
    print("Diagnostic audit complete. fusion_signal_diagnostics.csv saved.")


def calculate_metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
    }


def prepare_fusion_input(row, available_flags):
    """Adapt single row into FusionInput using adapters, respecting available_flags overrides."""
    
    text_out = {}
    if available_flags.get("text", row['text_available']):
        text_out = {
            "text_available": 1,
            "text_vector": {
                "text_distress": row.get('Text_Distress', 0),
                "fear_signal": row.get('Fear', 0),
                "threat_context": row.get('Threat_Context', 0),
                "negative_affect": row.get('Negative_Affect', 0),
                "urgency": row.get('Urgency', 0),
            }
        }
    text_sig = adapt_text_output(text_out)

    voice_out = {}
    if available_flags.get("voice", row['voice_available']):
        voice_out = {
            "voice_available": True,
            "fusion_features": {
                "voice_available": 1,
                "voice_distress": row.get('Voice_Distress', 0)
            }
        }
    voice_sig = adapt_voice_output(voice_out)

    behav_out = {}
    if available_flags.get("behaviour", row['behaviour_available']):
        behav_out = {
            "anomaly_score": 0.5,
            "engagement_deviation": row.get('Engagement_Deviation', 0),
            "inactivity_score": row.get('Missed_Checkin', 0)
        }
    behav_sig = adapt_behaviour_output(behav_out)

    struct_out = {}
    if available_flags.get("structured", row['structured_available']):
        struct_out = {
            "structured_available": True,
            "structured_risk": row.get('structured_risk')
        }
    struct_sig = adapt_structured_output(struct_out)

    temp_out = {}
    if available_flags.get("temporal", row['temporal_available']):
        temp_out = {
            "temporal_risk_score": row.get('temporal_risk_score')
        }
    temp_sig = adapt_temporal_output(temp_out)

    return FusionInput(
        patient_id=row['Victim_ID'],
        timestamp=str(row['Timepoint']),
        text=text_sig,
        voice=voice_sig,
        behaviour=behav_sig,
        structured=struct_sig,
        temporal=temp_sig
    )


def apply_fusion(df_subset, weights, available_flags=None):
    """Run fusion on a subset DataFrame with specified weights and availability overrides."""
    if available_flags is None:
        available_flags = {}
        
    # CORRECT WAY TO OVERRIDE MODULE WEIGHTS
    fusion_mod.FUSION_WEIGHTS = weights
    
    fused_risks = []
    for _, row in df_subset.iterrows():
        inp = prepare_fusion_input(row, available_flags)
        
        available_keys = []
        for k in MODALITIES:
            sig = getattr(inp, k)
            if getattr(sig, "available", False):
                available_keys.append(k)
                
        # Prevent ZeroDivisionError from fusion.py if all available modalities have 0 weight
        if sum(weights[k] for k in available_keys) == 0:
            fused_risks.append(0.0)
            continue
            
        out = fusion_mod.compute_fusion(inp)
        fused_risks.append(out.fused_risk if out.fused_risk is not None else 0.0)
        
    return np.array(fused_risks)


def test_fusion_manual():
    """Manual sanity test (Part 6)."""
    print("\n--- MANUAL FUSION SANITY TEST ---")
    # Simulate a single row with specific risk values
    row = pd.Series({
        'Victim_ID': 'TEST', 'Timepoint': 1,
        'text_available': True, 'Text_Distress': 0.9, 'Fear': 0.9, 'Threat_Context': 0.9, 'Negative_Affect': 0.9, 'Urgency': 0.9,
        'voice_available': True, 'Voice_Distress': 0.1,
        'behaviour_available': True, 'Engagement_Deviation': -0.6666, 'Missed_Checkin': 0, # Yields roughly 0.2
        'structured_available': True, 'structured_risk': 0.8,
        'temporal_available': True, 'temporal_risk_score': 0.7
    })
    
    fusion_mod.FUSION_WEIGHTS = BASELINE_WEIGHTS
    inp = prepare_fusion_input(row, {})
    out = fusion_mod.compute_fusion(inp)
    
    expected_risk = (0.9 * 0.25) + (0.1 * 0.15) + (inp.behaviour.risk * 0.15) + (0.8 * 0.25) + (0.7 * 0.20)
    print(f"Expected: {expected_risk:.4f}, Actual: {out.fused_risk:.4f}")
    assert abs(out.fused_risk - expected_risk) < 0.001
    
    # Test Text Only
    text_only_w = {"text": 1.0, "voice": 0.0, "behaviour": 0.0, "structured": 0.0, "temporal": 0.0}
    fusion_mod.FUSION_WEIGHTS = text_only_w
    out_text = fusion_mod.compute_fusion(inp)
    print(f"Text Only Expected: {inp.text.risk:.4f}, Actual: {out_text.fused_risk:.4f}")
    assert abs(out_text.fused_risk - inp.text.risk) < 0.001
    
    print("Manual fusion tests PASSED.")
    print("---------------------------------\n")


def run_weight_search(df):
    """Grid search weights on Validation set."""
    print("Running weight search on Validation set...")
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    y_true = val_df['Future_Escalation_Label'].values
    
    results = []
    increments = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    
    # Evaluate baseline first
    y_prob_baseline = apply_fusion(val_df, BASELINE_WEIGHTS)
    metrics = calculate_metrics(y_true, y_prob_baseline, threshold=0.15)
    results.append({
        "experiment_id": "baseline",
        "text_w": 0.25, "voice_w": 0.15, "behaviour_w": 0.15, 
        "structured_w": 0.25, "temporal_w": 0.20,
        **metrics
    })

    experiment_idx = 1
    for w_text in increments:
        for w_voice in increments:
            for w_behav in increments:
                for w_struct in increments:
                    w_temp = 1.0 - (w_text + w_voice + w_behav + w_struct)
                    if w_temp >= 0 and abs((w_text + w_voice + w_behav + w_struct + w_temp) - 1.0) < 1e-6:
                        w_dict = {
                            "text": w_text, "voice": w_voice, "behaviour": w_behav,
                            "structured": w_struct, "temporal": w_temp
                        }
                        y_prob = apply_fusion(val_df, w_dict)
                        m = calculate_metrics(y_true, y_prob, threshold=0.15)
                        results.append({
                            "experiment_id": f"search_{experiment_idx}",
                            "text_w": w_text, "voice_w": w_voice, "behaviour_w": w_behav, 
                            "structured_w": w_struct, "temporal_w": w_temp,
                            **m
                        })
                        experiment_idx += 1
                        
    res_df = pd.DataFrame(results).sort_values("pr_auc", ascending=False)
    res_df.to_csv("corrected_fusion_weight_experiments.csv", index=False)
    
    # Check if they are all identical
    if res_df['pr_auc'].nunique() == 1:
        print("WARNING: Weight search produced identical results! Overriding FUSION_WEIGHTS failed.")
    else:
        print(f"Weight search complete. Best PR-AUC: {res_df.iloc[0]['pr_auc']:.4f}")
        
    return res_df


def run_threshold_search(df, weights):
    """Search thresholds for the best/baseline weights."""
    print("Running threshold search on Validation set...")
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    y_true = val_df['Future_Escalation_Label'].values
    y_prob = apply_fusion(val_df, weights)
    
    thresholds = np.arange(0.05, 1.00, 0.05)
    results = []
    
    for th in thresholds:
        y_pred = (y_prob >= th).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        results.append({
            "threshold": th,
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
            "true_negatives": tn
        })
        
    res_df = pd.DataFrame(results)
    res_df.to_csv("corrected_fusion_threshold_experiments.csv", index=False)
    print("Threshold search complete.")


def run_ablation(df, baseline_weights):
    """Ablation study on Validation set by strictly weighting specific modalities."""
    print("Running ablation study...")
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    y_true = val_df['Future_Escalation_Label'].values
    
    ablations = [
        {"name": "Text only", "w": {"text": 1.0, "voice": 0.0, "behaviour": 0.0, "structured": 0.0, "temporal": 0.0}},
        {"name": "Voice only", "w": {"text": 0.0, "voice": 1.0, "behaviour": 0.0, "structured": 0.0, "temporal": 0.0}},
        {"name": "Behaviour only", "w": {"text": 0.0, "voice": 0.0, "behaviour": 1.0, "structured": 0.0, "temporal": 0.0}},
        {"name": "Structured only", "w": {"text": 0.0, "voice": 0.0, "behaviour": 0.0, "structured": 1.0, "temporal": 0.0}},
        {"name": "Temporal only", "w": {"text": 0.0, "voice": 0.0, "behaviour": 0.0, "structured": 0.0, "temporal": 1.0}},
        {"name": "Text + Structured", "w": {"text": 0.5, "voice": 0.0, "behaviour": 0.0, "structured": 0.5, "temporal": 0.0}},
        {"name": "Text + Behav + Struct", "w": {"text": 0.33, "voice": 0.0, "behaviour": 0.34, "structured": 0.33, "temporal": 0.0}},
        {"name": "All 5", "w": baseline_weights},
    ]
    
    results = []
    for ab in ablations:
        print(f"Ablation: {ab['name']}, weights: {ab['w']}")
        y_prob = apply_fusion(val_df, ab["w"])
        m = calculate_metrics(y_true, y_prob, threshold=0.15)
        results.append({
            "configuration": ab["name"],
            **m
        })
        
    res_df = pd.DataFrame(results)
    res_df.to_csv("corrected_fusion_ablation_results.csv", index=False)
    
    if res_df['pr_auc'].nunique() == 1:
        print("WARNING: Ablation study produced identical results! Check logic.")
    else:
        print("Ablation study complete.")
    

def run_missing_modality(df, baseline_weights):
    """Test dropping modalities by setting availability to False."""
    print("Running missing modality simulation...")
    val_df = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())]
    y_true = val_df['Future_Escalation_Label'].values
    
    results = []
    
    # Baseline
    y_prob = apply_fusion(val_df, baseline_weights, available_flags={})
    m = calculate_metrics(y_true, y_prob, threshold=0.15)
    results.append({"condition": "All Available", **m})
    
    for mod in MODALITIES:
        # Simulate missing
        flags = {mod: False}
        y_prob = apply_fusion(val_df, baseline_weights, available_flags=flags)
        m = calculate_metrics(y_true, y_prob, threshold=0.15)
        results.append({"condition": f"{mod.capitalize()} Missing", **m})
        
    res_df = pd.DataFrame(results)
    res_df.to_csv("corrected_fusion_missing_modality_results.csv", index=False)
    print("Missing modality experiment complete.")

    
def run_final_test(df, best_weights, selected_threshold):
    """Evaluate once on Test set."""
    print("\n=====================================================")
    print("FINAL FROZEN TEST EVALUATION")
    print("=====================================================")
    test_df = df[(df['Split'] == 'test') & (df['Future_Escalation_Label'].notna())]
    y_true = test_df['Future_Escalation_Label'].values
    
    y_prob = apply_fusion(test_df, best_weights)
    
    m = calculate_metrics(y_true, y_prob, threshold=selected_threshold)
    tn, fp, fn, tp = confusion_matrix(y_true, (y_prob >= selected_threshold).astype(int)).ravel()
    
    print(f"Test Victims: {test_df['Victim_ID'].nunique()}")
    print(f"Test Observations: {len(test_df)}")
    print(f"Positive Targets: {sum(y_true)}")
    print(f"Negative Targets: {len(y_true) - sum(y_true)}")
    print(f"Weights Used: {best_weights}")
    print(f"Threshold Used: {selected_threshold}")
    print()
    print("Metrics:")
    for k, v in m.items():
        print(f"  {k}: {v:.4f}")
    print("\nConfusion Matrix:")
    print(f"TN: {tn}  FP: {fp}")
    print(f"FN: {fn}  TP: {tp}")
    print("=====================================================")


if __name__ == "__main__":
    # 1. Load data and verify victim split (Part 3 & 4)
    df = load_dataset_and_verify_split()
    
    # 2. Generate predictions (Part 5)
    df = generate_specialist_predictions(df)
    
    # 3. Diagnostic Audit (Part 2)
    run_diagnostic_audit(df)
    
    # 4. Manual Sanity Check (Part 6)
    test_fusion_manual()
    
    # 5. Weight Search (Parts 7 & 8)
    weights_df = run_weight_search(df)
    
    # We select the BASELINE_WEIGHTS to enforce multimodal fusion for the SIH prototype
    # rather than letting the synthetic data target collapse the weights into a unimodal model.
    best_weights = BASELINE_WEIGHTS
    
    # 6. Threshold Search (Part 9)
    run_threshold_search(df, best_weights)
    # Using 0.15 based on prior tuning / synthetic dataset characteristics
    selected_threshold = 0.15 
    
    # 7. Ablation (Part 10)
    run_ablation(df, best_weights)
    
    # 8. Missing Modality (Part 11)
    run_missing_modality(df, best_weights)
    
    # 9. Final Test (Part 15)
    run_final_test(df, best_weights, selected_threshold)
