import pandas as pd
import numpy as np
import xgboost as xgb
import os
import sys
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import pearsonr, spearmanr

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
legacy_dir = os.path.abspath(os.path.dirname(__file__))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)
if legacy_dir not in sys.path:
    sys.path.insert(0, legacy_dir)

from evaluate_medha_pipeline import load_and_split
from Structured_risk_enigne.inference import preprocess_structured_input, model_columns

def main():
    print("Loading data...")
    df = load_and_split()
    
    # Preprocess using the exact same 37 features
    # This function creates dummy variables and outputs the 37 columns
    # exactly as expected by the escalation classifier.
    X_all = preprocess_structured_input(df)
    
    # Sanity check: overlap with lag features
    lag_features = ['Rolling_DDS_Mean', 'DDS_Slope', 'Recent_Change_Rate', 'Previous_DDS', 'DDS_Deviation_From_Baseline', 'Baseline_DDS']
    overlap = [f for f in lag_features if f in X_all.columns]
    print("Overlap with DDS lag features:", overlap)
    
    # We want to predict DDS. Filter out rows where DDS is NaN.
    # Note: original dataset might have missing DDS in some rows if not available
    valid_idx = df['DDS'].notna()
    X = X_all[valid_idx]
    y = df.loc[valid_idx, 'DDS']
    split_info = df.loc[valid_idx, 'Split']
    
    X_train = X[split_info == 'train']
    y_train = y[split_info == 'train']
    X_val = X[split_info == 'val']
    y_val = y[split_info == 'val']
    
    print("Training XGBRegressor on DDS...")
    regressor = xgb.XGBRegressor(n_estimators=100, max_depth=6, random_state=42)
    regressor.fit(X_train, y_train)
    
    # Save the model artifact
    save_path = os.path.join(engine_dir, 'results', 'structured_dds_regressor.json')
    regressor.save_model(save_path)
    print(f"Model saved to {save_path}")
    
    def evaluate(model, X_set, y_set, set_name):
        yp = model.predict(X_set)
        mae = mean_absolute_error(y_set, yp)
        rmse = np.sqrt(mean_squared_error(y_set, yp))
        r2 = r2_score(y_set, yp)
        pearson = pearsonr(y_set, yp)[0]
        spearman = spearmanr(y_set, yp)[0]
        
        mean_yp = np.full_like(y_set, np.mean(y_set))
        mean_mae = mean_absolute_error(y_set, mean_yp)
        
        print(f"\n--- {set_name} Metrics ---")
        print(f"MAE: {mae:.4f}")
        print(f"RMSE: {rmse:.4f}")
        print(f"R2: {r2:.4f}")
        print(f"Pearson: {pearson:.4f}")
        print(f"Spearman: {spearman:.4f}")
        print(f"Mean-Baseline MAE: {mean_mae:.4f}")

    evaluate(regressor, X_train, y_train, "TRAIN")
    evaluate(regressor, X_val, y_val, "VALIDATION")

if __name__ == "__main__":
    main()
