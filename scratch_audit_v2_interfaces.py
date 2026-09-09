import os
import json
import joblib

ENGINE_DIR = r"c:\Users\jnark\Documents\MEDHA\MEDHA\engine"

models = {
    "structured": (
        os.path.join(ENGINE_DIR, "models", "structured_dds_v2", "v2_structured_dds_preprocessor.pkl"),
        os.path.join(ENGINE_DIR, "models", "structured_dds_v2", "v2_structured_dds_xgb.json"),
        os.path.join(ENGINE_DIR, "models", "structured_dds_v2", "v2_structured_dds_features.json") # wait, where is features.json? it was in engine/models/v2
    ),
    "text": (
        os.path.join(ENGINE_DIR, "models", "text_dds_v2", "v2_text_dds_preprocessor.pkl"),
        os.path.join(ENGINE_DIR, "models", "text_dds_v2", "v2_text_dds_ridge_core5.pkl"),
        os.path.join(ENGINE_DIR, "models", "text_dds_v2", "v2_text_dds_features.json")
    ),
    "voice": (
        os.path.join(ENGINE_DIR, "models", "voice_dds_v2", "v2_voice_dds_preprocessor.pkl"),
        os.path.join(ENGINE_DIR, "models", "voice_dds_v2", "v2_voice_dds_ridge_core5.pkl"),
        os.path.join(ENGINE_DIR, "models", "voice_dds_v2", "v2_voice_dds_features.json")
    ),
    "behaviour": (
        os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2", "v2_behaviour_dds_preprocessor.pkl"),
        os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2", "v2_behaviour_dds_ridge_core7.pkl"),
        os.path.join(ENGINE_DIR, "models", "behaviour_dds_v2", "v2_behaviour_dds_features.json")
    ),
    "fusion": (
        None,
        os.path.join(ENGINE_DIR, "models", "v2", "fusion_final", "fusion_model.json"),
        os.path.join(ENGINE_DIR, "models", "v2", "fusion_final", "fusion_feature_config.json")
    ),
    "gru": (
        os.path.join(ENGINE_DIR, "models", "v2", "gru_sequences", "scaler.joblib"),
        os.path.join(ENGINE_DIR, "models", "v2", "gru", "best_gru_model.pth"),
        os.path.join(ENGINE_DIR, "models", "v2", "gru_sequences", "feature_config.json")
    )
}

print("=== V2 INTERFACES AUDIT ===")

for mod, (prep, model, feat) in models.items():
    print(f"\n--- {mod.upper()} ---")
    
    if prep and os.path.exists(prep):
        print(f"Preprocessor: Found")
    elif prep:
        print(f"Preprocessor: NOT FOUND -> {prep}")
        
    if model and os.path.exists(model):
        print(f"Model: Found")
    else:
        print(f"Model: NOT FOUND -> {model}")
        
    if feat:
        if os.path.exists(feat):
            with open(feat, 'r') as f:
                features = json.load(f)
                if isinstance(features, list):
                    print(f"Features: {len(features)} items")
                    print(f"First 5: {features[:5]}")
                elif isinstance(features, dict):
                    print("Features keys:", list(features.keys()))
                    if "feature_order" in features:
                        print(f"feature_order len: {len(features['feature_order'])}")
                        print(f"First 5: {features['feature_order'][:5]}")
                    elif "features" in features:
                        print(f"features len: {len(features['features'])}")
                        print(f"First 5: {features['features'][:5]}")
                    elif "feature_whitelist" in features:
                        print(f"feature_whitelist len: {len(features['feature_whitelist'])}")
                        print(f"First 5: {features['feature_whitelist'][:5]}")
        else:
            print(f"Features JSON: NOT FOUND -> {feat}")
