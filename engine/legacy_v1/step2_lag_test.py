import pandas as pd
import numpy as np
import os
import sys
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
legacy_dir = os.path.abspath(os.path.dirname(__file__))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)
if legacy_dir not in sys.path:
    sys.path.insert(0, legacy_dir)

from evaluate_medha_pipeline import load_and_split
from Structured_risk_enigne.inference import preprocess_structured_input

def main():
    print("Loading data...")
    df = load_and_split()
    
    # Non-lag features (the 37 from Step 1)
    X_non_lag_all = preprocess_structured_input(df)
    
    # Lag features specifically requested
    lag_cols = ['Rolling_DDS_Mean', 'DDS_Slope', 'Recent_Change_Rate', 'Previous_DDS']
    
    # We want to predict DDS. Filter out rows where DDS is NaN.
    # Additionally, for a fair comparison, we should filter out rows where the lag features are NaN.
    valid_idx = df['DDS'].notna() & df[lag_cols].notna().all(axis=1)
    
    X_non_lag = X_non_lag_all[valid_idx].fillna(0)
    X_lag = df.loc[valid_idx, lag_cols].fillna(0)
    y = df.loc[valid_idx, 'DDS']
    split_info = df.loc[valid_idx, 'Split']
    
    # Split
    X_nl_train, X_nl_val = X_non_lag[split_info == 'train'], X_non_lag[split_info == 'val']
    X_l_train, X_l_val = X_lag[split_info == 'train'], X_lag[split_info == 'val']
    y_train, y_val = y[split_info == 'train'], y[split_info == 'val']
    
    # 1. Non-lag Linear Regression
    lr_nl = LinearRegression()
    lr_nl.fit(X_nl_train, y_train)
    r2_nl_val = r2_score(y_val, lr_nl.predict(X_nl_val))
    
    # 2. Lag Linear Regression
    lr_l = LinearRegression()
    lr_l.fit(X_l_train, y_train)
    r2_l_val = r2_score(y_val, lr_l.predict(X_l_val))
    
    print(f"\n--- VALIDATION R2 COMPARISON ---")
    print(f"Non-lag features (37 variables) Linear Regression R2: {r2_nl_val:.4f}")
    print(f"Lag features (4 variables) Linear Regression R2:      {r2_l_val:.4f}")

if __name__ == "__main__":
    main()
