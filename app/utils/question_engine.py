import json
import os

QUESTIONS = [
    {"id": "q1", "type": "Text", "text": "How are you feeling today?"},
    {"id": "q2", "type": "Rating Scale", "text": "On a scale of 1-10, how stressed are you?"},
    {"id": "q3", "type": "Yes/No", "text": "Have you experienced any panic attacks recently?"},
    {"id": "q4", "type": "MCQ", "text": "How is your sleep quality?", "options": ["Good", "Fair", "Poor"]}
]

def get_next_question(answered_question_ids: list[str]):
    for q in QUESTIONS:
        if q["id"] not in answered_question_ids:
            return q
    return None
