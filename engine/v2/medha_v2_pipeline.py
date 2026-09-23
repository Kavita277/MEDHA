import os
import json
import joblib
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
import torch
import torch.nn as nn

# ==============================================================
# V2 GRU MODEL ARCHITECTURE
# ==============================================================
class V2GRUModel(nn.Module):
    """
    MEDHA V2 Temporal Risk GRU Architecture.
    """
    def __init__(self, input_size=57, hidden_size=64, num_layers=1, dropout=0.3):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout_rate = dropout

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        _, hidden_state = self.gru(x)
        last_hidden_state = hidden_state[-1]
        logits = self.fc(self.dropout(last_hidden_state))
        return logits.squeeze(-1)

    def predict_proba(self, x):
        return torch.sigmoid(self(x))

# ==============================================================
# MEDHA V2 INTEGRATION PIPELINE
# ==============================================================
class MedhaV2Pipeline:
    def __init__(self, engine_dir=None):
        if engine_dir is None:
            engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            
        self.engine_dir = engine_dir
        self.device = torch.device("cpu")
        self._load_configs()
        self._load_models()

    def _load_configs(self):
        # Structured Features
        struct_feat_path = os.path.join(self.engine_dir, "models", "v2", "v2_structured_dds_features.json")
        with open(struct_feat_path, "r") as f:
            self.structured_features = json.load(f)["features"]
            
        # Text Features
        text_feat_path = os.path.join(self.engine_dir, "models", "text_dds_v2", "v2_text_dds_features.json")
        with open(text_feat_path, "r") as f:
            self.text_features = json.load(f)["core_features"]
            
        # Voice Features
        voice_feat_path = os.path.join(self.engine_dir, "models", "voice_dds_v2", "v2_voice_dds_features.json")
        with open(voice_feat_path, "r") as f:
            self.voice_features = json.load(f)["core_features"]
            
        # Behaviour Features
        behav_feat_path = os.path.join(self.engine_dir, "models", "behaviour_dds_v2", "v2_behaviour_dds_features.json")
        with open(behav_feat_path, "r") as f:
            b_cfg = json.load(f)
            self.behaviour_features_all = b_cfg["all_10_features"]
            self.behaviour_features_core = b_cfg["core_7_features"]
            
        # Fusion Features
        fusion_feat_path = os.path.join(self.engine_dir, "models", "v2", "fusion_final", "fusion_feature_config.json")
        with open(fusion_feat_path, "r") as f:
            self.fusion_features = json.load(f)["feature_order"]
            
        # GRU Features
        gru_feat_path = os.path.join(self.engine_dir, "models", "v2", "gru_sequences", "feature_config.json")
        with open(gru_feat_path, "r") as f:
            self.gru_features = json.load(f)["feature_whitelist"]
            
        # GRU Threshold
        gru_thresh_path = os.path.join(self.engine_dir, "models", "v2", "gru", "threshold_config.json")
        with open(gru_thresh_path, "r") as f:
            self.gru_threshold = json.load(f)["selected_threshold"]

    def _load_models(self):
        # 1. Structured
        with open(os.path.join(self.engine_dir, "models", "structured_dds_v2", "v2_structured_dds_preprocessor.pkl"), "rb") as f:
            self.struct_preproc = pickle.load(f)
        self.struct_model = xgb.XGBRegressor()
        self.struct_model.load_model(os.path.join(self.engine_dir, "models", "structured_dds_v2", "v2_structured_dds_xgb.json"))
        
        # 2. Text
        with open(os.path.join(self.engine_dir, "models", "text_dds_v2", "v2_text_dds_preprocessor.pkl"), "rb") as f:
            self.text_preproc = pickle.load(f)
        with open(os.path.join(self.engine_dir, "models", "text_dds_v2", "v2_text_dds_ridge_core5.pkl"), "rb") as f:
            self.text_model = pickle.load(f)
            
        # 3. Voice
        with open(os.path.join(self.engine_dir, "models", "voice_dds_v2", "v2_voice_dds_preprocessor.pkl"), "rb") as f:
            self.voice_preproc = pickle.load(f)
        with open(os.path.join(self.engine_dir, "models", "voice_dds_v2", "v2_voice_dds_ridge_core5.pkl"), "rb") as f:
            self.voice_model = pickle.load(f)
            
        # 4. Behaviour (uses joblib for Ridge models and Imputer in V2)
        self.behav_preproc = joblib.load(os.path.join(self.engine_dir, "models", "behaviour_dds_v2", "v2_behaviour_dds_preprocessor.pkl"))
        self.behav_model = joblib.load(os.path.join(self.engine_dir, "models", "behaviour_dds_v2", "v2_behaviour_dds_ridge_all10.pkl"))
            
        # 5. Fusion
        self.fusion_model = xgb.XGBRegressor()
        self.fusion_model.load_model(os.path.join(self.engine_dir, "models", "v2", "fusion_final", "fusion_model.json"))
        
        # 6. GRU
        self.gru_scaler = joblib.load(os.path.join(self.engine_dir, "models", "v2", "gru_sequences", "scaler.joblib"))
        self.gru_model = V2GRUModel(input_size=57, hidden_size=64, num_layers=1, dropout=0.3).to(self.device)
        self.gru_model.load_state_dict(torch.load(os.path.join(self.engine_dir, "models", "v2", "gru", "best_gru_model.pth"), map_location=self.device, weights_only=True))
        self.gru_model.eval()

    def predict_v2(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes the entire V2 pipeline on a longitudinal DataFrame.
        Expected columns: Victim_ID, Timepoint, + features.
        Returns a DataFrame with Fusion_DDS_Prediction and Temporal_Risk_Score appended.
        """
        out_df = df.copy()
        
        # --- 1. Specialists Inference ---
        
        # Structured
        X_struct = self.struct_preproc.transform(out_df[self.structured_features])
        out_df["Struct_Pred"] = np.round(self.struct_model.predict(X_struct), 4)
        out_df["Struct_Available"] = 1.0 # Structured is assumed always available if inferenced
        
        # Text
        out_df["Text_Available"] = out_df.get("Text_Available", 0).fillna(0).astype(float)
        X_text = self.text_preproc.transform(out_df[self.text_features])
        text_preds = self.text_model.predict(X_text)
        out_df["Text_Pred"] = np.where(out_df["Text_Available"] == 1, np.round(text_preds, 4), np.nan)
        
        # Voice
        out_df["Voice_Available"] = out_df.get("Voice_Available", 0).fillna(0).astype(float)
        X_voice = self.voice_preproc.transform(out_df[self.voice_features])
        voice_preds = self.voice_model.predict(X_voice)
        out_df["Voice_Pred"] = np.where(out_df["Voice_Available"] == 1, np.round(voice_preds, 4), np.nan)
        
        # Behaviour
        # Behaviour core features might contain NaNs in raw data.
        # Imputer was fitted on all 10 features.
        # We must also apply absolute deviations as per Step 8 Mathematical Verification.
        behav_df = out_df[self.behaviour_features_all].copy()
        if "Engagement_Deviation" in behav_df.columns:
            behav_df["Engagement_Deviation"] = behav_df["Engagement_Deviation"].abs()
        if "Response_Delay_Deviation" in behav_df.columns:
            behav_df["Response_Delay_Deviation"] = behav_df["Response_Delay_Deviation"].abs()
            
        X_behav_all_imp = pd.DataFrame(self.behav_preproc.transform(behav_df), columns=self.behaviour_features_all)
        
        out_df["Behav_Available"] = out_df.get("Behav_Available", 0).fillna(0).astype(float)
        behav_preds = self.behav_model.predict(X_behav_all_imp)
        out_df["Behav_Pred"] = np.where(out_df["Behav_Available"] == 1, np.round(behav_preds, 4), np.nan)
        
        # --- 2. Fusion Inference ---
        fusion_input = out_df[self.fusion_features].copy()
        # Missing modality predictions set to 0.0 before fusion (Availability flag handles logic)
        for col in self.fusion_features:
            fusion_input[col] = fusion_input[col].fillna(0.0)
            
        X_fusion = fusion_input.values
        fusion_preds = np.clip(self.fusion_model.predict(X_fusion), 0.0, 100.0)
        out_df["Fusion_DDS_Prediction"] = np.round(fusion_preds, 4)
        
        # --- 3. GRU Inference ---
        out_df["Temporal_Risk_Score"] = np.nan
        out_df["Temporal_Available"] = 0
        out_df["Future_Escalation_Flag"] = np.nan
        
        # Pre-fill NaN and infs for GRU features with 0.0 BEFORE sequence grouping
        gru_df = out_df[self.gru_features].replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(np.float32)
        
        for victim_id, victim_indices in out_df.groupby("Victim_ID").groups.items():
            victim_data = out_df.loc[victim_indices].sort_values("Timepoint")
            # Extract features for this victim
            features = gru_df.loc[victim_data.index].to_numpy()
            
            for i, idx in enumerate(victim_data.index):
                # We need sequence length exactly 7
                # Trailing 7 days with progressive baseline padding for early timepoints
                if i >= 7:
                    window = features[i - 7 : i]
                else:
                    earliest = features[0:1]
                    n_pad = 7 - (i + 1)
                    if n_pad > 0:
                        window = np.vstack([np.repeat(earliest, n_pad, axis=0), features[0 : i + 1]])
                    else:
                        window = features[i + 1 - 7 : i + 1]
                
                # Scale window
                window_scaled = self.gru_scaler.transform(window)
                
                # Predict
                with torch.no_grad():
                    tensor_x = torch.from_numpy(window_scaled).unsqueeze(0).to(self.device)
                    prob = self.gru_model.predict_proba(tensor_x).item()
                    
                out_df.at[idx, "Temporal_Risk_Score"] = np.round(prob, 4)
                out_df.at[idx, "Temporal_Available"] = 1
                out_df.at[idx, "Future_Escalation_Flag"] = int(prob >= self.gru_threshold)
                
        return out_df

if __name__ == "__main__":
    # Smoke test on the test set
    print("Testing MedhaV2Pipeline instantiation...")
    pipeline = MedhaV2Pipeline()
    print("Pipeline loaded successfully.")
