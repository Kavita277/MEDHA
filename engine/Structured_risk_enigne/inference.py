import os
import joblib
import pandas as pd
import numpy as np
import shap

# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


MODEL_PATH = os.path.join(
    BASE_DIR,
    "Models/structured_engine/xgboost_model.pkl"
)

ENCODER_PATH = os.path.join(
    BASE_DIR,
    "Models/structured_engine/case_encoder.pkl"
)

EPISODE_MAPPING_PATH = os.path.join(
    BASE_DIR,
    "Models/structured_engine/episode_mapping.pkl"
)

FEATURES_PATH = os.path.join(
    BASE_DIR,
    "Models/structured_engine/structured_features.pkl"
)

COLUMNS_PATH = os.path.join(
    BASE_DIR,
    "Models/structured_engine/model_columns.pkl"
)

THRESHOLD_PATH = os.path.join(
    BASE_DIR,
    "Models/structured_engine/threshold.pkl"
)


# ============================================================
# LOAD TRAINED ARTIFACTS
# ============================================================
model = joblib.load(MODEL_PATH)

# ============================================================
# SHAP EXPLAINER
# ============================================================
explainer = shap.TreeExplainer(model)

encoder = joblib.load(ENCODER_PATH)

episode_mapping = joblib.load(
    EPISODE_MAPPING_PATH
)

structured_features = joblib.load(
    FEATURES_PATH
)

model_columns = joblib.load(
    COLUMNS_PATH
)

threshold = joblib.load(
    THRESHOLD_PATH
)

# ============================================================
# STRUCTURED RISK + SHAP EXPLANATION
# ============================================================

def structured_risk_with_explanation(df, top_n=5):

    X_processed = preprocess_structured_input(df)

    # --------------------------------------------------------
    # Model probability
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        X_processed
    )[:, 1]

    # --------------------------------------------------------
    # Risk flag
    # --------------------------------------------------------

    predictions = (
        probabilities >= threshold
    ).astype(int)

    # --------------------------------------------------------
    # SHAP
    # --------------------------------------------------------

    shap_values = explainer.shap_values(
        X_processed
    )

    results = []

    for i in range(len(df)):

        contributions = pd.DataFrame({
            "feature": model_columns,
            "shap_value": shap_values[i]
        })

        contributions["abs_shap"] = (
            contributions["shap_value"].abs()
        )

        contributions = contributions.sort_values(
            "abs_shap",
            ascending=False
        )

        # ----------------------------------------------------
        # Top contributors
        # ----------------------------------------------------

        top_features = []

        for _, row in contributions.head(top_n).iterrows():

            feature_name = row["feature"]

            # Remove one-hot prefix if necessary
            display_name = FEATURE_DISPLAY_NAMES.get(
                feature_name,
                feature_name
            )

            top_features.append({
                "feature": feature_name,
                "display_name": display_name,
                "contribution": float(
                    row["shap_value"]
                )
            })

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        results.append({

            "structured_available": True,

            "structured_risk": float(
                probabilities[i]
            ),

            "structured_flag": int(
                predictions[i]
            ),

            "threshold": float(
                threshold
            ),

            "top_contributors": top_features
        })

    return results
# ============================================================
# CATEGORICAL FEATURES
# ============================================================

categorical_features = [
    "Case_Type",
    "Case_Stage"
]

# ============================================================
# HUMAN-READABLE FEATURE NAMES
# ============================================================
FEATURE_DISPLAY_NAMES = {
    "DDS": "Current distress score",
    "Previous_DDS": "Previous distress score",
    "Baseline_DDS": "Baseline distress level",
    "DDS_Deviation_From_Baseline": "Change from baseline distress",

    "Engagement_Score": "Engagement level",
    "Engagement_Deviation": "Change in engagement",

    "Mood": "Mood",
    "Stress": "Stress level",
    "Sleep": "Sleep quality",
    "Functioning": "Daily functioning",
    "Safety": "Sense of safety",
    "Social_Support_Checkin": "Social support",
    "Self_Reported_Wellbeing": "Self-reported wellbeing",

    "Response_Delay_Hours": "Response delay",
    "Response_Delay_Deviation": "Change in response delay",

    "Missed_Checkin": "Missed check-in",
    "Interaction_Frequency_7d": "Recent interaction frequency",
    "Session_Duration_Minutes": "Session duration",

    "Threat_Event": "Recent threat event",
    "Upcoming_Hearing": "Upcoming hearing",
    "Hearing_Completed": "Hearing completed",
    "Investigation_Delay": "Investigation delay",
    "Compensation_Delay": "Compensation delay",
    "Relocation_Stress": "Relocation stress",
    "Rehabilitation_Issue": "Rehabilitation issue",
    "Protection_Event": "Protection event",

    "Family_Support": "Family support",
    "Social_Support": "Social support",
    "Therapist_Engagement": "Therapist engagement",
    "Access_To_Services": "Access to services",
    "Stable_Housing": "Stable housing",
    "Other_Protective_Factors": "Other protective factors",

    "Recent_Episode": "Recent episode",
    "Family_Reported_Episode": "Family-reported episode",

    "Baseline_Response_Delay": "Baseline response delay",
    "Baseline_Engagement": "Baseline engagement",
    "Delta_DDS": "Change in distress score",

    "Episode_Severity": "Episode severity",
}
FEATURE_DISPLAY_NAMES.update({

    "Case_Type_arson_displacement":
        "Case type: arson/displacement",

    "Case_Type_caste_based_violence":
        "Case type: caste-based violence",

    "Case_Type_compensation_rehabilitation":
        "Case type: compensation/rehabilitation",

    "Case_Type_murder_grievous_hurt":
        "Case type: murder/grievous hurt",

    "Case_Type_sexual_violence":
        "Case type: sexual violence",

    "Case_Type_witness_intimidation":
        "Case type: witness intimidation",

    "Case_Stage_Compensation":
        "Case stage: compensation",

    "Case_Stage_Complaint":
        "Case stage: complaint",

    "Case_Stage_Hearing":
        "Case stage: hearing",

    "Case_Stage_Investigation":
        "Case stage: investigation",

    "Case_Stage_Investigation_Delay":
        "Case stage: investigation delay",

    "Case_Stage_Post_Hearing":
        "Case stage: post hearing",

    "Case_Stage_Trial_Preparation":
        "Case stage: trial preparation"
})

# ============================================================
# PREPROCESS STRUCTURED INPUT
# ============================================================

def preprocess_structured_input(df):
    """
    Convert raw structured MEDHA input into
    exactly the same 51-feature representation
    used during XGBoost training.
    """

    # Work on a copy
    X = df.copy()

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    missing_columns = [
        col for col in structured_features
        if col not in X.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required features: {missing_columns}"
        )

    # Keep only training features
    X = X[structured_features].copy()

    # --------------------------------------------------------
    # Episode Severity
    # --------------------------------------------------------

    X["Episode_Severity"] = (
        X["Episode_Severity"]
        .map(episode_mapping)
    )


    # --------------------------------------------------------
    # One-hot encode Case_Type + Case_Stage
    # --------------------------------------------------------

    encoded = encoder.transform(
        X[categorical_features]
    )

    encoded_df = pd.DataFrame(
        encoded,
        columns=encoder.get_feature_names_out(
            categorical_features
        ),
        index=X.index
    )

    # Remove raw categorical columns
    X = X.drop(
        columns=categorical_features
    )

    # Combine numerical features + encoded features
    X_processed = pd.concat(
        [
            X,
            encoded_df
        ],
        axis=1
    )

    # --------------------------------------------------------
    # Force exact training column order
    # --------------------------------------------------------

    X_processed = X_processed.reindex(
        columns=model_columns
    )

    # --------------------------------------------------------
    # Final safety check
    # --------------------------------------------------------

    if list(X_processed.columns) != list(model_columns):

        raise RuntimeError(
            "Processed feature columns do not match "
            "the training feature columns."
        )

    if X_processed.shape[1] != len(model_columns):

        raise RuntimeError(
            f"Expected {len(model_columns)} features, "
            f"got {X_processed.shape[1]}."
        )

    return X_processed

# ============================================================
# API CONTRACT
# ============================================================

def structured_engine_api(df, top_n=5):

    result = structured_risk_with_explanation(
        df,
        top_n=top_n
    )

    return result
# ============================================================
# STRUCTURED RISK INFERENCE
# ============================================================

def structured_risk_inference(df):
    """
    Run the frozen Structured Risk Engine.

    Input:
        pandas DataFrame containing one or more rows
        with the original structured MEDHA features.

    Returns:
        pandas DataFrame containing:
            structured_risk
            structured_flag
            threshold
    """

    X_processed = preprocess_structured_input(df)

    # Probability of Future_Escalation_Label = 1
    probabilities = model.predict_proba(
        X_processed
    )[:, 1]

    # Apply frozen validation threshold
    predictions = (
        probabilities >= threshold
    ).astype(int)

    results = pd.DataFrame({
        "structured_risk": probabilities,
        "structured_flag": predictions,
        "threshold": threshold
    }, index=df.index)

    return results




    # temp test
    # ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("Structured Engine loaded successfully.")
    print()

    print("Model columns:", len(model_columns))
    print("Threshold:", threshold)
    print("Episode mapping:", episode_mapping)
    print()

    print("Expected features:")
    print(len(structured_features))

    print()
    print("Model expects:")
    print(model_columns)