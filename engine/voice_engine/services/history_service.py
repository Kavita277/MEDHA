import json
import os


HISTORY_FILE = os.path.join(
    "logs",
    "voice_history.jsonl"
)


def save_voice_record(record: dict):
    """
    Saves one voice analysis record as a JSON line.

    Each line represents one patient interaction.

    Example:

    {
        "patient_id": "patient_001",
        "timestamp": "...",
        "fusion_features": {...}
    }
    """

    os.makedirs(
        "logs",
        exist_ok=True
    )

    with open(
        HISTORY_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        json.dump(
            record,
            file
        )

        file.write("\n")


def get_patient_history(
    patient_id: str
):
    """
    Returns all historical voice records
    for one patient.
    """

    if not os.path.exists(
        HISTORY_FILE
    ):

        return []


    history = []


    with open(
        HISTORY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()


            if not line:

                continue


            record = json.loads(
                line
            )


            if record.get(
                "patient_id"
            ) == patient_id:

                history.append(
                    record
                )


    return history