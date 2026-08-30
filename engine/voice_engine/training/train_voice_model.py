import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


print("\n")
print("=" * 60)
print("MEDHA VOICE MODEL TRAINING")
print("=" * 60)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "datasets",
    "iemocap_processed.csv"
)

MODELS_DIR = os.path.join(
    BASE_DIR,
    "models"
)

os.makedirs(
    MODELS_DIR,
    exist_ok=True
)


# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(
    DATASET_PATH
)

print(
    f"Dataset shape: {df.shape}"
)


# ============================================================
# VOICE DISTRESS FEATURES
# ============================================================

print("\n")
print("=" * 60)
print("VOICE DISTRESS MODEL FEATURES")
print("=" * 60)


distress_features = [

    # Emotion probabilities
    "angry",
    "sad",
    "neutral",
    "happy",

    # Acoustic features
    "speaking_rate",
    "pitch_mean",
    "pitch_std",
    "rms"
]


print("\nSelected input features:")

for feature in distress_features:

    print(
        f" - {feature}"
    )


X_distress = df[
    distress_features
]

y_distress = df[
    "voice_distress_target"
]


# ============================================================
# ACOUSTIC INDICATOR FEATURES
# ============================================================

print("\n")
print("=" * 60)
print("ACOUSTIC INDICATOR MODEL FEATURES")
print("=" * 60)


acoustic_features = [

    "speaking_rate",
    "pitch_mean",
    "pitch_std",
    "rms"
]


print("\nSelected input features:")

for feature in acoustic_features:

    print(
        f" - {feature}"
    )


X_acoustic = df[
    acoustic_features
]

y_acoustic = df[
    "acoustic_indicator_target"
]


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print("\nSplitting dataset...")


X_train_distress, X_test_distress, y_train_distress, y_test_distress = train_test_split(

    X_distress,
    y_distress,

    test_size=0.20,

    random_state=42
)


X_train_acoustic, X_test_acoustic, y_train_acoustic, y_test_acoustic = train_test_split(

    X_acoustic,
    y_acoustic,

    test_size=0.20,

    random_state=42
)


print(
    f"\nVoice Distress Training samples: {len(X_train_distress)}"
)

print(
    f"Voice Distress Testing samples: {len(X_test_distress)}"
)


# ============================================================
# TRAIN VOICE DISTRESS MODEL
# ============================================================

print("\n")
print("=" * 60)
print("TRAINING VOICE DISTRESS MODEL")
print("=" * 60)


voice_distress_model = RandomForestRegressor(

    n_estimators=300,

    max_depth=20,

    min_samples_split=5,

    min_samples_leaf=2,

    random_state=42,

    n_jobs=-1
)


voice_distress_model.fit(

    X_train_distress,
    y_train_distress
)


# ============================================================
# EVALUATE VOICE DISTRESS MODEL
# ============================================================

distress_predictions = voice_distress_model.predict(

    X_test_distress
)


distress_mae = mean_absolute_error(

    y_test_distress,
    distress_predictions
)


distress_rmse = mean_squared_error(

    y_test_distress,
    distress_predictions
) ** 0.5


distress_r2 = r2_score(

    y_test_distress,
    distress_predictions
)


print("\n")
print("=" * 60)
print("VOICE DISTRESS MODEL EVALUATION")
print("=" * 60)

print(
    f"MAE  : {distress_mae:.4f}"
)

print(
    f"RMSE : {distress_rmse:.4f}"
)

print(
    f"R²   : {distress_r2:.4f}"
)


# ============================================================
# TRAIN ACOUSTIC INDICATOR MODEL
# ============================================================

print("\n")
print("=" * 60)
print("TRAINING ACOUSTIC INDICATOR MODEL")
print("=" * 60)


acoustic_indicator_model = RandomForestRegressor(

    n_estimators=300,

    max_depth=20,

    min_samples_split=5,

    min_samples_leaf=2,

    random_state=42,

    n_jobs=-1
)


acoustic_indicator_model.fit(

    X_train_acoustic,
    y_train_acoustic
)


# ============================================================
# EVALUATE ACOUSTIC INDICATOR MODEL
# ============================================================

acoustic_predictions = acoustic_indicator_model.predict(

    X_test_acoustic
)


acoustic_mae = mean_absolute_error(

    y_test_acoustic,
    acoustic_predictions
)


acoustic_rmse = mean_squared_error(

    y_test_acoustic,
    acoustic_predictions
) ** 0.5


acoustic_r2 = r2_score(

    y_test_acoustic,
    acoustic_predictions
)


print("\n")
print("=" * 60)
print("ACOUSTIC INDICATOR MODEL EVALUATION")
print("=" * 60)

print(
    f"MAE  : {acoustic_mae:.4f}"
)

print(
    f"RMSE : {acoustic_rmse:.4f}"
)

print(
    f"R²   : {acoustic_r2:.4f}"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n")
print("=" * 60)
print("VOICE DISTRESS FEATURE IMPORTANCE")
print("=" * 60)


distress_importance = sorted(

    zip(

        distress_features,

        voice_distress_model.feature_importances_
    ),

    key=lambda x: x[1],

    reverse=True
)


for feature, importance in distress_importance:

    print(
        f"{feature}: {importance:.4f}"
    )


print("\n")
print("=" * 60)
print("ACOUSTIC INDICATOR FEATURE IMPORTANCE")
print("=" * 60)


acoustic_importance = sorted(

    zip(

        acoustic_features,

        acoustic_indicator_model.feature_importances_
    ),

    key=lambda x: x[1],

    reverse=True
)


for feature, importance in acoustic_importance:

    print(
        f"{feature}: {importance:.4f}"
    )


# ============================================================
# SAVE MODELS
# ============================================================

print("\nSaving trained models...")


joblib.dump(

    voice_distress_model,

    os.path.join(
        MODELS_DIR,
        "voice_distress_model.joblib"
    )
)


joblib.dump(

    acoustic_indicator_model,

    os.path.join(
        MODELS_DIR,
        "acoustic_indicator_model.joblib"
    )
)


joblib.dump(

    distress_features,

    os.path.join(
        MODELS_DIR,
        "voice_distress_feature_names.joblib"
    )
)


joblib.dump(

    acoustic_features,

    os.path.join(
        MODELS_DIR,
        "acoustic_indicator_feature_names.joblib"
    )
)


# ============================================================
# SAVE TRAINING METRICS
# ============================================================

training_metrics = {

    "voice_distress_model": {

        "features": distress_features,

        "MAE": round(
            float(distress_mae),
            4
        ),

        "RMSE": round(
            float(distress_rmse),
            4
        ),

        "R2": round(
            float(distress_r2),
            4
        )
    },


    "acoustic_indicator_model": {

        "features": acoustic_features,

        "MAE": round(
            float(acoustic_mae),
            4
        ),

        "RMSE": round(
            float(acoustic_rmse),
            4
        ),

        "R2": round(
            float(acoustic_r2),
            4
        )
    }
}


metrics_path = os.path.join(

    MODELS_DIR,

    "training_metrics.json"
)


with open(

    metrics_path,

    "w"

) as file:

    json.dump(

        training_metrics,

        file,

        indent=4
    )


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n")
print("=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)


print("\nModels saved successfully:\n")


print(

    os.path.join(
        MODELS_DIR,
        "voice_distress_model.joblib"
    )
)


print(

    os.path.join(
        MODELS_DIR,
        "acoustic_indicator_model.joblib"
    )
)


print(

    os.path.join(
        MODELS_DIR,
        "voice_distress_feature_names.joblib"
    )
)


print(

    os.path.join(
        MODELS_DIR,
        "acoustic_indicator_feature_names.joblib"
    )
)


print(

    metrics_path
)