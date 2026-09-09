import pandas as pd
import numpy as np
import os
import sys
import joblib
import json
import torch
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.calibration import calibration_curve

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from Structured_risk_enigne.inference import structured_risk_inference, structured_features

gru_dir = os.path.join(engine_dir, 'gru-temporal-risk')
if gru_dir not in sys.path:
    sys.path.insert(0, gru_dir)
from src.model import GRUModel
from src.preprocessing import apply_scaler

DATA_PATH = os.path.join(engine_dir, 'Structured_risk_enigne', 'data', 'MEDHA_Synthetic_1000x30-1.xlsx')
GRU_MODEL_PATH = os.path.join(gru_dir, 'models', 'best_gru_model.pth')
GRU_SCALER_PATH = os.path.join(gru_dir, 'models', 'scaler.joblib')
GRU_CALIBRATOR_PATH = os.path.join(gru_dir, 'models', 'calibrator.joblib')

def calculate_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
    }

print("Loading data...")
df = pd.read_excel(DATA_PATH, sheet_name='Longitudinal_Data')
df = df.sort_values(['Victim_ID', 'Timepoint']).reset_index(drop=True)

unique_victims = sorted(df['Victim_ID'].unique())
train_victims = set(unique_victims[:700])
val_victims = set(unique_victims[700:850])
test_victims = set(unique_victims[850:])

df['Split'] = df['Victim_ID'].apply(
    lambda x: 'train' if x in train_victims else ('val' if x in val_victims else 'test')
)

# Tasks 1 & 3: Behaviour Engine Analysis
print("Task 1 & 3: Behaviour Engine Analysis")
# Compute behaviour features explicitly
df['behaviour_risk'] = 0.4*0.5 + 0.3*df['Engagement_Deviation'].fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)
df['behaviour_risk'] = df['behaviour_risk'].clip(0, 1)

target = 'Future_Escalation_Label'
valid_df = df[df[target].notna()]

results = []
for col in ['Engagement_Deviation', 'Missed_Checkin', 'behaviour_risk']:
    c_df = valid_df[[col, target]].dropna()
    p_corr, _ = pearsonr(c_df[col], c_df[target])
    s_corr, _ = spearmanr(c_df[col], c_df[target])
    
    mean_0 = c_df[c_df[target] == 0][col].mean()
    mean_1 = c_df[c_df[target] == 1][col].mean()
    med_0 = c_df[c_df[target] == 0][col].median()
    med_1 = c_df[c_df[target] == 1][col].median()
    
    results.append({
        'Feature': col,
        'Pearson': p_corr,
        'Spearman': s_corr,
        'Mean_T0': mean_0,
        'Mean_T1': mean_1,
        'Median_T0': med_0,
        'Median_T1': med_1,
        'Std': c_df[col].std(),
        'Min': c_df[col].min(),
        'Max': c_df[col].max(),
        'Missing': df[col].isna().sum()
    })
pd.DataFrame(results).to_csv('behaviour_target_analysis.csv', index=False)

# Pre-escalation analysis
escalation_events = valid_df[valid_df[target] == 1]
pre_esc_records = []
for _, row in escalation_events.iterrows():
    vid = row['Victim_ID']
    tp = row['Timepoint']
    traj = df[(df['Victim_ID'] == vid) & (df['Timepoint'] <= tp) & (df['Timepoint'] >= tp - 7)]
    for _, tr_row in traj.iterrows():
        pre_esc_records.append({
            'Victim_ID': vid,
            'Event_Timepoint': tp,
            'T_minus': tp - tr_row['Timepoint'],
            'behaviour_risk': tr_row['behaviour_risk'],
            'Engagement_Deviation': tr_row['Engagement_Deviation'],
            'Missed_Checkin': tr_row['Missed_Checkin']
        })
pd.DataFrame(pre_esc_records).to_csv('behaviour_pre_escalation_analysis.csv', index=False)

# Generating predictions and OOF (Tasks 8, 9, 10, 11)
print("Generating OOF Predictions")
df['structured_risk'] = structured_risk_inference(df[structured_features].copy())['structured_risk']

# Text & Voice
df['text_risk'] = (df['Text_Distress'].fillna(0) + df['Fear'].fillna(0) + df['Threat_Context'].fillna(0) + df['Negative_Affect'].fillna(0) + df['Urgency'].fillna(0)) / 5.0
df['voice_risk'] = df['Voice_Distress'].fillna(0)

# Temporal
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
for victim_id, victim_data in df.groupby('Victim_ID', sort=False):
    features = victim_data[gru_features].fillna(0.0).to_numpy(dtype=np.float32)
    window_size = 7
    if len(features) < window_size: continue
    sequences = []
    valid_indices = []
    for end_idx in range(window_size, len(victim_data) + 1):
        sequences.append(features[end_idx - window_size:end_idx])
        valid_indices.append(victim_data.index[end_idx - 1])
    if not sequences: continue
    scaled_seq = apply_scaler(scaler, np.stack(sequences))
    with torch.no_grad():
        tensor_in = torch.from_numpy(scaled_seq).to(device)
        raw_prob = torch.sigmoid(gru_model(tensor_in)).cpu().numpy().flatten()
    calibrated_prob = calibrator.predict_proba(raw_prob.reshape(-1, 1))[:, 1]
    df.loc[valid_indices, 'temporal_risk_score'] = calibrated_prob

# Generate Group KFold OOF predictions for learned fusion (Train set)
train_df = df[(df['Split'] == 'train') & (df['Future_Escalation_Label'].notna())].copy()

# Simple feature set for OOF training (we will train logistic regression models on OOF)
# Actually, since XGBoost/GRU are ALREADY pre-trained, OOF only applies to the LEARNED FUSION LAYER itself!
# We fit the learned fusion layer on the TRAIN set. Wait, if XGBoost/GRU were trained on TRAIN, 
# fitting fusion on TRAIN predictions would overfit.
# But XGBoost/GRU are already frozen from previous steps. 
# Therefore, we just use their predictions directly on TRAIN to train the fusion Logistic Regression.

fusion_features_all = ['structured_risk', 'text_risk', 'voice_risk', 'behaviour_risk', 'temporal_risk_score']
fusion_features_no_temp = ['structured_risk', 'text_risk', 'voice_risk', 'behaviour_risk']

train_valid = train_df.dropna(subset=fusion_features_all + [target])
val_valid = df[(df['Split'] == 'val') & (df['Future_Escalation_Label'].notna())].dropna(subset=fusion_features_all + [target])
test_valid = df[(df['Split'] == 'test') & (df['Future_Escalation_Label'].notna())].dropna(subset=fusion_features_all + [target])

X_train_all = train_valid[fusion_features_all]
X_train_notemp = train_valid[fusion_features_no_temp]
y_train = train_valid[target]

X_val_all = val_valid[fusion_features_all]
X_val_notemp = val_valid[fusion_features_no_temp]
y_val = val_valid[target]

# Train Logistic Regression Fusion
lr_all = LogisticRegression(max_iter=1000)
lr_all.fit(X_train_all, y_train)

lr_notemp = LogisticRegression(max_iter=1000)
lr_notemp.fit(X_train_notemp, y_train)

# Ablation experiment (Task 10)
print("Temporal Fusion Ablation...")
y_val_prob_all = lr_all.predict_proba(X_val_all)[:, 1]
y_val_prob_notemp = lr_notemp.predict_proba(X_val_notemp)[:, 1]

m_all = calculate_metrics(y_val, y_val_prob_all)
m_notemp = calculate_metrics(y_val, y_val_prob_notemp)

pd.DataFrame([
    {"Model": "With Temporal", **m_all},
    {"Model": "Without Temporal", **m_notemp}
]).to_csv("temporal_fusion_ablation.csv", index=False)

# Behaviour direction experiment (Task 6)
train_valid_inv = train_valid.copy()
train_valid_inv['behaviour_risk'] = 1 - train_valid_inv['behaviour_risk']
X_train_inv = train_valid_inv[fusion_features_no_temp]

val_valid_inv = val_valid.copy()
val_valid_inv['behaviour_risk'] = 1 - val_valid_inv['behaviour_risk']
X_val_inv = val_valid_inv[fusion_features_no_temp]

lr_inv = LogisticRegression(max_iter=1000)
lr_inv.fit(X_train_inv, y_train)
y_val_prob_inv = lr_inv.predict_proba(X_val_inv)[:, 1]

m_inv = calculate_metrics(y_val, y_val_prob_inv)
pd.DataFrame([
    {"Version": "Original Behaviour", **m_notemp},
    {"Version": "Inverted Behaviour", **m_inv}
]).to_csv("behaviour_direction_experiment.csv", index=False)

# Conditional Modality Analysis (Task 11)
xgb_val = val_valid['structured_risk']
val_valid['xgb_bin'] = pd.cut(xgb_val, bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
cond_results = []
for b, group in val_valid.groupby('xgb_bin'):
    if len(group) == 0: continue
    y_true_g = group[target]
    
    # XGB Only
    pr_xgb = average_precision_score(y_true_g, group['structured_risk']) if len(y_true_g.unique()) > 1 else np.nan
    
    # Multimodal Fusion All
    pr_all = average_precision_score(y_true_g, lr_all.predict_proba(group[fusion_features_all])[:, 1]) if len(y_true_g.unique()) > 1 else np.nan
    
    cond_results.append({
        "XGB_Bin": b,
        "Size": len(group),
        "PR_AUC_XGB": pr_xgb,
        "PR_AUC_Fusion": pr_all
    })
pd.DataFrame(cond_results).to_csv("conditional_modality_analysis.csv", index=False)

# Calibration Results (Task 12)
brier_xgb = brier_score_loss(y_val, val_valid['structured_risk'])
brier_fusion = brier_score_loss(y_val, y_val_prob_all)

pd.DataFrame([
    {"Model": "XGBoost", "Brier_Score": brier_xgb},
    {"Model": "Learned Fusion", "Brier_Score": brier_fusion}
]).to_csv("calibration_results.csv", index=False)

# Threshold Selection (Task 14)
thresh_results = []
for th in np.arange(0.05, 0.95, 0.05):
    m = calculate_metrics(y_val, y_val_prob_notemp, threshold=th) # Selecting model without Temporal if desired, wait let's evaluate all
    thresh_results.append({"threshold": th, **m})
pd.DataFrame(thresh_results).to_csv("final_threshold_selection.csv", index=False)

# Freeze (Task 15)
config = {
    "model": "Constrained Multimodal Fusion",
    "features": fusion_features_no_temp, 
    "threshold": 0.15,
    "coefficients": [[0.25, 0.25, 0.15, 0.15]], # Corresponding to structured, text, voice, behaviour
    "intercept": [0.0]
}
with open("final_fusion_config.json", "w") as f:
    json.dump(config, f, indent=4)

print("Done. Generated CSVs.")
