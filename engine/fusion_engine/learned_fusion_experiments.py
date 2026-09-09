import pandas as pd
import numpy as np
import os
import sys
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)
    
from fusion_engine.evaluate_fusion import load_dataset_and_verify_split, generate_specialist_predictions, calculate_metrics

def run_learned_fusion():
    print("Loading OOF predictions...")
    oof_df = pd.read_csv("oof_specialist_predictions.csv")
    
    print("Loading full dataset for Validation set...")
    full_df = load_dataset_and_verify_split()
    full_df = generate_specialist_predictions(full_df)
    
    # Ensure behaviour_risk uses abs() as corrected
    full_df['behaviour_risk'] = 0.4*0.5 + 0.3*full_df['Engagement_Deviation'].abs().fillna(0) + 0.3*full_df['Missed_Checkin'].fillna(0)
    full_df['behaviour_risk'] = full_df['behaviour_risk'].clip(0, 1)

    val_df = full_df[(full_df['Split'] == 'val') & (full_df['Future_Escalation_Label'].notna())].copy()
    
    features = ['text_risk', 'voice_risk', 'behaviour_risk', 'oof_structured_risk', 'oof_temporal_risk']
    val_features = ['text_risk', 'voice_risk', 'behaviour_risk', 'structured_risk', 'temporal_risk_score']
    
    X_train = oof_df[features].fillna(0)
    y_train = oof_df['Future_Escalation_Label'].astype(int)
    
    X_val = val_df[val_features].fillna(0)
    # Rename columns to match X_train
    X_val = X_val.rename(columns={'structured_risk': 'oof_structured_risk', 'temporal_risk_score': 'oof_temporal_risk'})
    y_val = val_df['Future_Escalation_Label'].astype(int)
    
    # 1. Logistic Regression
    lr = LogisticRegression(penalty='l2', C=1.0, class_weight='balanced', random_state=42)
    lr.fit(X_train, y_train)
    
    val_preds_lr = lr.predict_proba(X_val)[:, 1]
    res_lr = calculate_metrics(y_val, val_preds_lr, 0.5) # Dynamic thresholding done later, use 0.5 here
    
    lr_df = pd.DataFrame([{"model": "Logistic_Regression", **res_lr}])
    lr_df.to_csv("oof_logistic_fusion_results.csv", index=False)
    
    # 2. MLP
    mlp = MLPClassifier(hidden_layer_sizes=(16, 8), activation='relu', max_iter=500, random_state=42)
    mlp.fit(X_train, y_train)
    val_preds_mlp = mlp.predict_proba(X_val)[:, 1]
    res_mlp = calculate_metrics(y_val, val_preds_mlp, 0.5)
    
    mlp_df = pd.DataFrame([{"model": "MLP_Fusion", **res_mlp}])
    mlp_df.to_csv("mlp_fusion_results.csv", index=False)
    
    # 3. Interactions
    X_train_int = X_train.copy()
    X_val_int = X_val.copy()
    
    X_train_int['text_x_struct'] = X_train_int['text_risk'] * X_train_int['oof_structured_risk']
    X_train_int['voice_x_struct'] = X_train_int['voice_risk'] * X_train_int['oof_structured_risk']
    X_train_int['behav_x_struct'] = X_train_int['behaviour_risk'] * X_train_int['oof_structured_risk']
    
    X_val_int['text_x_struct'] = X_val_int['text_risk'] * X_val_int['oof_structured_risk']
    X_val_int['voice_x_struct'] = X_val_int['voice_risk'] * X_val_int['oof_structured_risk']
    X_val_int['behav_x_struct'] = X_val_int['behaviour_risk'] * X_val_int['oof_structured_risk']
    
    lr_int = LogisticRegression(penalty='l2', C=1.0, class_weight='balanced', random_state=42)
    lr_int.fit(X_train_int, y_train)
    val_preds_int = lr_int.predict_proba(X_val_int)[:, 1]
    res_int = calculate_metrics(y_val, val_preds_int, 0.5)
    
    int_df = pd.DataFrame([{"model": "Logistic_Interactions", **res_int}])
    int_df.to_csv("fusion_interaction_results.csv", index=False)
    
    print("Learned fusion completed.")
    
if __name__ == "__main__":
    run_learned_fusion()
