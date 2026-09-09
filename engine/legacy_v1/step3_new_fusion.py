import pandas as pd
import numpy as np
import xgboost as xgb
import os
import sys

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
legacy_dir = os.path.abspath(os.path.dirname(__file__))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)
if legacy_dir not in sys.path:
    sys.path.insert(0, legacy_dir)

from evaluate_medha_pipeline import load_and_split, add_specialists, get_fused, dds_metrics, BASELINE_WEIGHTS
from Structured_risk_enigne.inference import preprocess_structured_input

def main():
    print("Loading and preparing data...")
    df = load_and_split()
    df = add_specialists(df)
    
    # Load the new regressor
    model_path = os.path.join(engine_dir, 'results', 'structured_dds_regressor.json')
    regressor = xgb.XGBRegressor()
    regressor.load_model(model_path)
    
    # Get predictions (DDS scale)
    X_processed = preprocess_structured_input(df)
    new_dds_preds = regressor.predict(X_processed)
    
    # Replace the escalation classifier's output with the new regressor's output.
    # The existing Fusion engine multiplies fused_risk by 100 to get DDS.
    # Therefore, we must pass the regressor's output / 100 so the scales align.
    df['structured_risk'] = new_dds_preds / 100.0
    
    val_df = df[df['Split'] == 'val']
    test_df = df[df['Split'] == 'test']
    
    # Run existing fusion pipeline unchanged
    val_yt = val_df['DDS'].values
    val_yp = get_fused(val_df, BASELINE_WEIGHTS)
    val_metrics = dds_metrics(val_yt, val_yp)
    
    test_yt = test_df['DDS'].values
    test_yp = get_fused(test_df, BASELINE_WEIGHTS)
    test_metrics = dds_metrics(test_yt, test_yp)
    
    print("\n--- NEW FUSION PIPELINE METRICS ---")
    print("\nVALIDATION:")
    for k, v in val_metrics.items():
        print(f"{k}: {v:.4f}")
        
    print("\nTEST:")
    for k, v in test_metrics.items():
        print(f"{k}: {v:.4f}")

if __name__ == "__main__":
    main()
