import pandas as pd
import numpy as np
import os
import sys

# Paths
engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(engine_dir, 'Structured_risk_enigne', 'data', 'MEDHA_Synthetic_1000x30-1.xlsx')

def audit_behaviour():
    print("Loading dataset for behaviour audit...")
    df = pd.read_excel(DATA_PATH, sheet_name='Longitudinal_Data')
    
    target = 'Future_Escalation_Label'
    df = df[df[target].notna()].copy()
    
    features = [
        'Response_Delay_Hours', 
        'Missed_Checkin', 
        'Interaction_Frequency_7d', 
        'Session_Duration_Minutes', 
        'Engagement_Score', 
        'Engagement_Deviation'
    ]
    
    # Add current behaviour risk
    # 0.4 * 0.5 (anomaly baseline) + 0.3 * Engagement_Deviation + 0.3 * Missed_Checkin
    df['behaviour_risk_OLD'] = 0.4*0.5 + 0.3*df['Engagement_Deviation'].fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)
    df['behaviour_risk_OLD'] = df['behaviour_risk_OLD'].clip(0, 1)

    # What if we invert Engagement_Deviation because a drop in engagement (negative deviation) means higher risk?
    # Drop in engagement -> Negative Deviation -> We want HIGHER risk -> Subtract it.
    df['behaviour_risk_CORRECTED'] = 0.4*0.5 - 0.3*df['Engagement_Deviation'].fillna(0) + 0.3*df['Missed_Checkin'].fillna(0)
    df['behaviour_risk_CORRECTED'] = df['behaviour_risk_CORRECTED'].clip(0, 1)

    features.extend(['behaviour_risk_OLD', 'behaviour_risk_CORRECTED'])
    
    audit_data = []
    
    for f in features:
        if f not in df.columns:
            continue
            
        s = df[f]
        
        # Calculate separately for Target=0 and Target=1
        s_0 = df[df[target] == 0][f]
        s_1 = df[df[target] == 1][f]
        
        pearson = df[[f, target]].corr(method='pearson').iloc[0, 1]
        spearman = df[[f, target]].corr(method='spearman').iloc[0, 1]
        
        audit_data.append({
            "feature": f,
            "min": s.min(),
            "max": s.max(),
            "mean": s.mean(),
            "median": s.median(),
            "std": s.std(),
            "missing": s.isna().sum(),
            "mean_Target=0": s_0.mean(),
            "mean_Target=1": s_1.mean(),
            "pearson_corr": pearson,
            "spearman_corr": spearman
        })
        
    audit_df = pd.DataFrame(audit_data)
    audit_df.to_csv("behaviour_audit.csv", index=False)
    print("Saved behaviour_audit.csv")

    # Save behaviour fix comparison
    fix_df = audit_df[audit_df['feature'].isin(['behaviour_risk_OLD', 'behaviour_risk_CORRECTED'])]
    fix_df.to_csv("behaviour_fix_comparison.csv", index=False)
    print("Saved behaviour_fix_comparison.csv")
    
if __name__ == "__main__":
    audit_behaviour()
