import pandas as pd
import numpy as np
import os
import sys
import json
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss

def calculate_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
        "pr_auc": average_precision_score(y_true, y_prob),
        "brier_score": brier_score_loss(y_true, y_prob),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
    }

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from Structured_risk_enigne.inference import structured_risk_inference, structured_features

DATA_PATH = os.path.join(engine_dir, 'Structured_risk_enigne', 'data', 'MEDHA_Synthetic_1000x30-1.xlsx')

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

test_df = df[(df['Split'] == 'test') & (df['Future_Escalation_Label'].notna())].copy()

# Structured risk
test_df['structured_risk'] = structured_risk_inference(test_df[structured_features].copy())['structured_risk']

# Text, Voice, Behaviour
test_df['text_risk'] = (test_df['Text_Distress'].fillna(0) + test_df['Fear'].fillna(0) + test_df['Threat_Context'].fillna(0) + test_df['Negative_Affect'].fillna(0) + test_df['Urgency'].fillna(0)) / 5.0
test_df['voice_risk'] = test_df['Voice_Distress'].fillna(0)
test_df['behaviour_risk'] = 0.4*0.5 + 0.3*test_df['Engagement_Deviation'].fillna(0) + 0.3*test_df['Missed_Checkin'].fillna(0)
test_df['behaviour_risk'] = test_df['behaviour_risk'].clip(0, 1)

# Load frozen config
with open("final_fusion_config.json", "r") as f:
    config = json.load(f)

features = config['features']
coefs = np.array(config['coefficients'])
intercept = np.array(config['intercept'])
threshold = config['threshold']

X_test = test_df[features].fillna(0)
y_test = test_df['Future_Escalation_Label']

logits = np.dot(X_test.values, coefs.T) + intercept
fusion_prob = 1 / (1 + np.exp(-logits)).flatten()

m_fusion = calculate_metrics(y_test, fusion_prob, threshold=threshold)

# XGBoost threshold 0.15 for fair comparison, or whatever its optimal was. 
# We'll just use the same threshold.
m_xgb = calculate_metrics(y_test, test_df['structured_risk'], threshold=threshold)

with open("final_test_results.json", "w") as f:
    json.dump({"XGBoost": m_xgb, "Learned_Fusion": m_fusion}, f, indent=4)
print("Finished test evaluation.")
