from datasets import load_dataset
import pandas as pd
import os


print("=" * 60)
print("MEDHA VOICE ENGINE - DATASET PREPARATION")
print("=" * 60)


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_NAME = "AbstractTTS/IEMOCAP"

OUTPUT_DIRECTORY = "datasets"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIRECTORY,
    "iemocap_processed.csv"
)


# ============================================================
# CREATE DATASET DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIRECTORY,
    exist_ok=True
)


# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading IEMOCAP dataset...")
print("This may take some time on first download.\n")


dataset = load_dataset(
    DATASET_NAME,
    split="train"
)


print("Dataset loaded successfully.")

print("\nTotal samples:")

print(len(dataset))


# ============================================================
# CONVERT TO PANDAS
# ============================================================

print("\nConverting dataset to DataFrame...")


df = dataset.to_pandas()


print("Conversion complete.")


# ============================================================
# DISPLAY AVAILABLE COLUMNS
# ============================================================

print("\nAvailable columns:\n")


for column in df.columns:

    print("-", column)


# ============================================================
# SELECT RELEVANT FEATURES
# ============================================================

emotion_columns = [

    "frustrated",

    "angry",

    "sad",

    "disgust",

    "excited",

    "fear",

    "neutral",

    "surprise",

    "happy"

]


selected_columns = [

    "file",

    "major_emotion",

    "transcription",

    "speaking_rate",

    "pitch_mean",

    "pitch_std",

    "rms"

]


# Add emotion probability columns

for column in emotion_columns:

    if column in df.columns:

        selected_columns.append(
            column
        )


# Keep only existing columns

selected_columns = [

    column

    for column in selected_columns

    if column in df.columns
]


df = df[
    selected_columns
]


# ============================================================
# CLEAN DATA
# ============================================================

print("\nCleaning dataset...")


df = df.dropna(
    subset=[
        "major_emotion"
    ]
)


# ============================================================
# CREATE MEDHA DISTRESS SCORE
# ============================================================

print(
    "\nCreating MEDHA distress target..."
)


def calculate_distress(row):

    angry = row.get(
        "angry",
        0
    )

    sad = row.get(
        "sad",
        0
    )

    fear = row.get(
        "fear",
        0
    )

    frustrated = row.get(
        "frustrated",
        0
    )

    disgust = row.get(
        "disgust",
        0
    )


    distress_score = (

        angry * 1.0

        +

        sad * 0.9

        +

        fear * 0.9

        +

        frustrated * 0.8

        +

        disgust * 0.5

    )


    # Normalize between 0 and 1

    distress_score = min(

        distress_score,

        1.0

    )


    return round(

        distress_score,

        4

    )


df[
    "voice_distress_target"
] = df.apply(

    calculate_distress,

    axis=1

)


# ============================================================
# CREATE ACOUSTIC INDICATOR TARGET
# ============================================================

print(
    "Creating acoustic indicator..."
)


def calculate_acoustic_indicator(row):

    pitch_std = row.get(
        "pitch_std",
        0
    )

    rms = row.get(
        "rms",
        0
    )


    # Simple normalization

    normalized_pitch = min(

        float(pitch_std) / 300,

        1.0

    )


    normalized_rms = min(

        float(rms) / 0.2,

        1.0

    )


    acoustic_indicator = (

        normalized_pitch * 0.6

        +

        normalized_rms * 0.4

    )


    return round(

        min(

            acoustic_indicator,

            1.0

        ),

        4

    )


df[
    "acoustic_indicator_target"
] = df.apply(

    calculate_acoustic_indicator,

    axis=1

)


# ============================================================
# SAVE DATASET
# ============================================================

df.to_csv(

    OUTPUT_FILE,

    index=False

)


print("\nDataset preparation complete.")

print(
    "Saved file:"
)

print(
    OUTPUT_FILE
)


print(
    "\nFinal dataset shape:"
)

print(
    df.shape
)


print(
    "\nFirst 5 rows:"
)

print(

    df.head()

)


print("\nEmotion distribution:")

print(

    df[
        "major_emotion"
    ].value_counts()

)


print("\nDone.")