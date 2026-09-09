import pandas as pd
import numpy as np
import joblib
import os
import sys
from scipy import stats
from sklearn.metrics import mean_absolute_error

# Add engine to path
engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
legacy_dir = os.path.abspath(os.path.dirname(__file__))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)
if legacy_dir not in sys.path:
    sys.path.insert(0, legacy_dir)

# Load data and structured engine
from evaluate_medha_pipeline import load_and_split
from Structured_risk_enigne.inference import structured_features, preprocess_structured_input, model_columns, model, encoder

def run_diagnostics():
    df = load_and_split()

    # Check 1: Feature overlap
    print("--- (1) FEATURE OVERLAP CHECK ---")
    print("Model features count:", len(model_columns))
    lag_features = ['Rolling_DDS_Mean', 'DDS_Slope', 'Recent_Change_Rate', 'Previous_DDS', 'DDS_Deviation_From_Baseline', 'Baseline_DDS']
    overlap = [f for f in lag_features if f in model_columns or f in structured_features]
    print("Overlap with DDS lag features:", overlap)

    df['structured_risk'] = model.predict_proba(preprocess_structured_input(df))[:, 1]
    df['predicted_dds'] = df['structured_risk'] * 100
    df_clean = df.dropna(subset=['DDS', 'predicted_dds'])

    train_df = df_clean[df_clean['Split'] == 'train']
    val_df = df_clean[df_clean['Split'] == 'val']

    # Check 2: Scale/units
    print("\n--- (2) SCALE / UNITS CHECK ---")
    print("Train Target DDS -> Min: {:.2f}, Max: {:.2f}, Mean: {:.2f}".format(train_df['DDS'].min(), train_df['DDS'].max(), train_df['DDS'].mean()))
    print("Train Pred DDS   -> Min: {:.2f}, Max: {:.2f}, Mean: {:.2f}".format(train_df['predicted_dds'].min(), train_df['predicted_dds'].max(), train_df['predicted_dds'].mean()))
    print("Val Target DDS   -> Min: {:.2f}, Max: {:.2f}, Mean: {:.2f}".format(val_df['DDS'].min(), val_df['DDS'].max(), val_df['DDS'].mean()))
    print("Val Pred DDS     -> Min: {:.2f}, Max: {:.2f}, Mean: {:.2f}".format(val_df['predicted_dds'].min(), val_df['predicted_dds'].max(), val_df['predicted_dds'].mean()))

    # Check 3: Train vs Val MAE
    print("\n--- (3) TRAIN VS VAL MAE ---")
    train_mae = mean_absolute_error(train_df['DDS'], train_df['predicted_dds'])
    val_mae = mean_absolute_error(val_df['DDS'], val_df['predicted_dds'])
    print("Train MAE: {:.2f}".format(train_mae))
    print("Val MAE:   {:.2f}".format(val_mae))

    # Check 4: Linear regression
    print("\n--- (4) LINEAR REGRESSION (PRED VS TARGET) ---")
    slope_t, intercept_t, r_t, p_t, err_t = stats.linregress(train_df['predicted_dds'], train_df['DDS'])
    print("Train -> Slope: {:.4f}, Intercept: {:.4f}, R2: {:.4f}".format(slope_t, intercept_t, r_t**2))

    slope_v, intercept_v, r_v, p_v, err_v = stats.linregress(val_df['predicted_dds'], val_df['DDS'])
    print("Val   -> Slope: {:.4f}, Intercept: {:.4f}, R2: {:.4f}".format(slope_v, intercept_v, r_v**2))

    # Check 5: Encoder validation
    print("\n--- (5) ENCODER VALIDATION ---")
    print("Encoder object:", encoder)
    print("Encoder classes (Case_Type):", encoder.categories_[0][:3] if hasattr(encoder, 'categories_') else "N/A")
    print("Is the same encoder object used for all rows? Yes, it is a globally loaded singleton in inference.py.")

if __name__ == "__main__":
    run_diagnostics()
