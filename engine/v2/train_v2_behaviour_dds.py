"""
MEDHA V2 — Step 8: Independent Behaviour DDS Specialist
Predicts psychological distress (DDS) exclusively from behavioural interaction data.

Verifies the intended mathematical definition of deviation features (absolute deviation |z|),
preserves the existing Behaviour Engine, and strictly enforces feature policies.
"""

import os
import sys

ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V2_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(ENGINE_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from scipy.stats import pearsonr, spearmanr
import xgboost as xgb

try:
    from engine.v2.v2_feature_policy import (
        validate_behaviour_specialist_features,
        get_all_approved_behaviour_dds_features,
        V2_CORE_BEHAVIOUR_DDS_FEATURES,
        V2_EXTENDED_BEHAVIOUR_DDS_FEATURES,
    )
except ImportError:
    from v2_feature_policy import (
        validate_behaviour_specialist_features,
        get_all_approved_behaviour_dds_features,
        V2_CORE_BEHAVIOUR_DDS_FEATURES,
        V2_EXTENDED_BEHAVIOUR_DDS_FEATURES,
    )

SEED = 42

def calculate_metrics(y_true, y_pred, baseline_mean):
    """Calculates all mandated evaluation metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    
    # Pearson and Spearman
    p_corr, _ = pearsonr(y_true, y_pred)
    s_corr, _ = spearmanr(y_true, y_pred)
    
    # Dummy baseline
    base_preds = np.full_like(y_true, baseline_mean)
    base_mae = float(mean_absolute_error(y_true, base_preds))
    base_rmse = float(root_mean_squared_error(y_true, base_preds))
    mae_improvement = float((base_mae - mae) / base_mae * 100.0)
    
    return {
        "n_samples": int(len(y_true)),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "pearson_r": round(float(p_corr), 4),
        "spearman_rho": round(float(s_corr), 4),
        "baseline_mae": round(base_mae, 4),
        "baseline_rmse": round(base_rmse, 4),
        "mae_improvement_pct": round(mae_improvement, 2),
    }

def prepare_feature_matrix(df_split, feature_list, use_absolute_deviations=True):
    """
    Extracts features and applies the intended mathematical definition for deviation features.
    If use_absolute_deviations is True, computes |Engagement_Deviation| and |Response_Delay_Deviation|.
    """
    X = df_split[feature_list].copy()
    if use_absolute_deviations:
        if "Engagement_Deviation" in X.columns:
            X["Engagement_Deviation"] = X["Engagement_Deviation"].abs()
        if "Response_Delay_Deviation" in X.columns:
            X["Response_Delay_Deviation"] = X["Response_Delay_Deviation"].abs()
    return X

def main():
    print("=" * 80)
    print("MEDHA V2 — STEP 8: BEHAVIOUR DDS REGRESSION SPECIALIST")
    print("=" * 80)

    # 1. Load data
    data_path = "engine/data/processed/v2_longitudinal_split.csv"
    victim_split_path = "engine/data/processed/v2_victim_split.csv"

    if not os.path.exists(data_path) or not os.path.exists(victim_split_path):
        raise FileNotFoundError("Processed split datasets not found in engine/data/processed/")

    df = pd.read_csv(data_path)
    split_df = pd.read_csv(victim_split_path)

    print(f"Loaded longitudinal dataset: {len(df)} rows, {df['Victim_ID'].nunique()} victims.")
    print(f"Victim split counts: {split_df['Split'].value_counts().to_dict()}")

    # 2. Strict Policy and Boundary Validation
    print("\n--- Validating Behaviour Feature Policies & Boundaries ---")
    core_features = list(V2_CORE_BEHAVIOUR_DDS_FEATURES)
    all_features = list(V2_EXTENDED_BEHAVIOUR_DDS_FEATURES)

    validate_behaviour_specialist_features(core_features, allow_extended=False)
    validate_behaviour_specialist_features(all_features, allow_extended=True)
    print(f"Core features ({len(core_features)}): {core_features}")
    print(f"All features ({len(all_features)}): {all_features}")
    print("Feature policy validation PASSED: Zero target lags, future information, text, or voice features.")

    # 3. Partition Data according to Authoritative Split
    train_df = df[df["Split"].str.lower() == "train"].copy().reset_index(drop=True)
    val_df = df[df["Split"].str.lower().isin(["val", "validation"])].copy().reset_index(drop=True)
    test_df = df[df["Split"].str.lower() == "test"].copy().reset_index(drop=True)

    y_train = train_df["DDS"].values
    y_val = val_df["DDS"].values
    y_test = test_df["DDS"].values

    train_mean = float(np.mean(y_train))
    print(f"\nTarget DDS summary (train mean): {train_mean:.4f}")
    print(f"Split sizes: Train={len(train_df)} ({train_df['Victim_ID'].nunique()} victims), "
          f"Val={len(val_df)} ({val_df['Victim_ID'].nunique()} victims), "
          f"Test={len(test_df)} ({test_df['Victim_ID'].nunique()} victims)")

    # 4. Mathematical Verification of Deviation Features
    print("\n--- Mathematical Verification of Deviation Features ---")
    raw_eng_dev = df["Engagement_Deviation"]
    raw_neg_count = int((raw_eng_dev < 0).sum())
    print(f"Raw Engagement_Deviation: range=[{raw_eng_dev.min():.3f}, {raw_eng_dev.max():.3f}], negative rows={raw_neg_count} ({raw_neg_count/len(df):.1%})")
    print(f"Correlation with DDS: signed={raw_eng_dev.corr(df['DDS']):.4f}, absolute={raw_eng_dev.abs().corr(df['DDS']):.4f}")
    print("Verification: Transforming to absolute deviation |Engagement_Deviation| ensures behavioral divergence from baseline produces a positive risk indicator.")

    # 5. Fit Preprocessor (Median Imputer on Train Split)
    X_train_raw = prepare_feature_matrix(train_df, all_features, use_absolute_deviations=True)
    X_val_raw = prepare_feature_matrix(val_df, all_features, use_absolute_deviations=True)
    X_test_raw = prepare_feature_matrix(test_df, all_features, use_absolute_deviations=True)

    imputer = SimpleImputer(strategy="median")
    imputer.fit(X_train_raw)

    X_train_imp = pd.DataFrame(imputer.transform(X_train_raw), columns=all_features)
    X_val_imp = pd.DataFrame(imputer.transform(X_val_raw), columns=all_features)
    X_test_imp = pd.DataFrame(imputer.transform(X_test_raw), columns=all_features)

    # Core 7 matrices
    X_train_core = X_train_imp[core_features]
    X_val_core = X_val_imp[core_features]
    X_test_core = X_test_imp[core_features]

    # Signed matrices for diagnostic ablation
    X_train_signed_raw = prepare_feature_matrix(train_df, all_features, use_absolute_deviations=False)
    X_val_signed_raw = prepare_feature_matrix(val_df, all_features, use_absolute_deviations=False)
    X_test_signed_raw = prepare_feature_matrix(test_df, all_features, use_absolute_deviations=False)
    imputer_signed = SimpleImputer(strategy="median").fit(X_train_signed_raw)
    X_train_signed = pd.DataFrame(imputer_signed.transform(X_train_signed_raw), columns=all_features)
    X_val_signed = pd.DataFrame(imputer_signed.transform(X_val_signed_raw), columns=all_features)
    X_test_signed = pd.DataFrame(imputer_signed.transform(X_test_signed_raw), columns=all_features)

    # 6. Train Models
    print("\n--- Training Behaviour DDS Regression Models ---")

    # 6a. Canonical Specialist: Ridge Regression (All 10 Absolute Deviations)
    ridge_all10 = Ridge(alpha=1.0, random_state=SEED)
    ridge_all10.fit(X_train_imp, y_train)

    # 6b. Nonlinear Baseline: XGBoost (All 10 Absolute Deviations)
    xgb_all10 = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=SEED,
        n_jobs=-1
    )
    xgb_all10.fit(X_train_imp, y_train)

    # 6c. Core-7 Interaction Models
    ridge_core7 = Ridge(alpha=1.0, random_state=SEED)
    ridge_core7.fit(X_train_core, y_train)

    xgb_core7 = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=SEED,
        n_jobs=-1
    )
    xgb_core7.fit(X_train_core, y_train)

    # 6d. Diagnostic Signed Models (Ablation)
    ridge_signed = Ridge(alpha=1.0, random_state=SEED)
    ridge_signed.fit(X_train_signed, y_train)

    xgb_signed = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=SEED,
        n_jobs=-1
    )
    xgb_signed.fit(X_train_signed, y_train)

    print("Model training complete.")

    # 7. Model Evaluation
    print("\n--- Evaluating Models across Splits ---")
    all_metrics = {}

    model_dict = {
        "ridge_all10_canonical": (ridge_all10, X_train_imp, X_val_imp, X_test_imp),
        "xgb_all10": (xgb_all10, X_train_imp, X_val_imp, X_test_imp),
        "ridge_core7": (ridge_core7, X_train_core, X_val_core, X_test_core),
        "xgb_core7": (xgb_core7, X_train_core, X_val_core, X_test_core),
        "diagnostic_ridge_signed": (ridge_signed, X_train_signed, X_val_signed, X_test_signed),
        "diagnostic_xgb_signed": (xgb_signed, X_train_signed, X_val_signed, X_test_signed),
    }

    for model_name, (model, xtr, xva, xte) in model_dict.items():
        p_tr = model.predict(xtr)
        p_va = model.predict(xva)
        p_te = model.predict(xte)

        tr_metrics = calculate_metrics(y_train, p_tr, train_mean)
        va_metrics = calculate_metrics(y_val, p_va, train_mean)
        te_metrics = calculate_metrics(y_test, p_te, train_mean)

        all_metrics[model_name] = {
            "train": tr_metrics,
            "val": va_metrics,
            "test": te_metrics
        }

        print(f"[{model_name}] Test: MAE={te_metrics['mae']} (+{te_metrics['mae_improvement_pct']}%), "
              f"RMSE={te_metrics['rmse']}, R2={te_metrics['r2']}, Pearson={te_metrics['pearson_r']}, Spearman={te_metrics['spearman_rho']}")

    # 8. Feature Importance & Coefficients
    print("\n--- Canonical Ridge Weights (Interpretable Clinical Formulation) ---")
    coef_dict = dict(zip(all_features, ridge_all10.coef_))
    intercept = float(ridge_all10.intercept_)
    print(f"Intercept: {intercept:.4f}")
    for feat, coef in sorted(coef_dict.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"  {feat:28s}: {coef:+.4f}")

    # XGBoost feature importances
    xgb_imp_dict = dict(zip(all_features, [float(x) for x in xgb_all10.feature_importances_]))
    imp_df = pd.DataFrame([
        {
            "feature": f,
            "ridge_coefficient": round(float(coef_dict[f]), 4),
            "xgb_gain_importance": round(float(xgb_imp_dict[f]), 4)
        }
        for f in all_features
    ]).sort_values("xgb_gain_importance", ascending=False)

    # 9. Generate Predictions for Outputs
    test_preds_canonical = ridge_all10.predict(X_test_imp)
    test_preds_xgb = xgb_all10.predict(X_test_imp)

    val_preds_canonical = ridge_all10.predict(X_val_imp)
    val_preds_xgb = xgb_all10.predict(X_val_imp)

    out_test_df = pd.DataFrame({
        "Victim_ID": test_df["Victim_ID"],
        "Timepoint": test_df["Timepoint"],
        "Actual_DDS": test_df["DDS"],
        "Predicted_DDS_Ridge": np.round(test_preds_canonical, 4),
        "Predicted_DDS_XGB": np.round(test_preds_xgb, 4),
        "Engagement_Score": test_df["Engagement_Score"],
        "Engagement_Deviation_Abs": np.round(X_test_imp["Engagement_Deviation"], 4),
        "Response_Delay_Hours": test_df["Response_Delay_Hours"],
        "Response_Delay_Deviation_Abs": np.round(X_test_imp["Response_Delay_Deviation"], 4),
        "Missed_Checkin": test_df["Missed_Checkin"],
    })

    out_val_df = pd.DataFrame({
        "Victim_ID": val_df["Victim_ID"],
        "Timepoint": val_df["Timepoint"],
        "Actual_DDS": val_df["DDS"],
        "Predicted_DDS_Ridge": np.round(val_preds_canonical, 4),
        "Predicted_DDS_XGB": np.round(val_preds_xgb, 4),
        "Engagement_Score": val_df["Engagement_Score"],
        "Engagement_Deviation_Abs": np.round(X_val_imp["Engagement_Deviation"], 4),
        "Response_Delay_Hours": val_df["Response_Delay_Hours"],
        "Response_Delay_Deviation_Abs": np.round(X_val_imp["Response_Delay_Deviation"], 4),
        "Missed_Checkin": val_df["Missed_Checkin"],
    })

    # 10. Persist Artifacts
    target_model_dirs = ["models/behaviour_dds_v2", "engine/models/behaviour_dds_v2"]
    target_output_dirs = ["outputs/dds_v2/behaviour", "engine/outputs/dds_v2/behaviour"]

    feature_metadata = {
        "specialist": "Behaviour DDS Specialist",
        "policy_version": "v2.0",
        "mathematical_definition": "Absolute deviation |z| for Engagement_Deviation and Response_Delay_Deviation",
        "core_features": core_features,
        "extended_features": all_features,
        "canonical_model": "Ridge (All 10 Absolute Deviations)",
        "all_10_features": all_features,
        "core_7_features": core_features,
        "coefficients_ridge_all10": {f: round(float(c), 4) for f, c in coef_dict.items()},
        "intercept_ridge_all10": round(intercept, 4),
    }

    for d in target_model_dirs:
        os.makedirs(d, exist_ok=True)
        joblib.dump(ridge_all10, os.path.join(d, "v2_behaviour_dds_ridge_all10.pkl"))
        joblib.dump(ridge_core7, os.path.join(d, "v2_behaviour_dds_ridge_core7.pkl"))
        joblib.dump(imputer, os.path.join(d, "v2_behaviour_dds_preprocessor.pkl"))
        xgb_all10.save_model(os.path.join(d, "v2_behaviour_dds_xgb_all10.json"))
        xgb_core7.save_model(os.path.join(d, "v2_behaviour_dds_xgb_core7.json"))
        xgb_signed.save_model(os.path.join(d, "v2_behaviour_dds_diagnostic_signed.json"))
        
        with open(os.path.join(d, "v2_behaviour_dds_features.json"), "w") as f:
            json.dump(feature_metadata, f, indent=4)
        with open(os.path.join(d, "v2_behaviour_dds_metrics.json"), "w") as f:
            json.dump(all_metrics, f, indent=4)
        imp_df.to_csv(os.path.join(d, "v2_behaviour_dds_importance.csv"), index=False)

    for d in target_output_dirs:
        os.makedirs(d, exist_ok=True)
        out_test_df.to_csv(os.path.join(d, "test_behaviour_dds_predictions.csv"), index=False)
        out_val_df.to_csv(os.path.join(d, "val_behaviour_dds_predictions.csv"), index=False)

    print("\nAll model artifacts and prediction datasets saved successfully to:")
    for d in target_model_dirs + target_output_dirs:
        print(f"  -> {d}")
    print("=" * 80)

if __name__ == "__main__":
    main()
