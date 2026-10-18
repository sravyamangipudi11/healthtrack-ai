"""Deterministic safety net: never rely on the LLM alone to flag emergencies."""
RED_FLAGS = {
    "chest pain": "Possible acute coronary syndrome",
    "shortness of breath": "Possible respiratory/cardiac compromise",
    "difficulty breathing": "Possible respiratory compromise",
    "slurred speech": "Possible stroke",
    "facial droop": "Possible stroke",
    "loss of consciousness": "Syncope/neurological emergency",
    "severe bleeding": "Haemorrhage",
    "suicidal": "Psychiatric emergency",
    "seizure": "Neurological emergency",
}
ORDER = {"routine": 0, "urgent": 1, "emergency": 2}


def detect_red_flags(symptoms: list[str]) -> list[str]:
    return [f"{why} (reported: {k})" for k, why in RED_FLAGS.items() if any(k in s for s in symptoms)]


def escalate(urgency: str, flags: list[str]) -> str:
    """Rules can only raise urgency, never lower what the model said."""
    return "emergency" if flags and ORDER[urgency] < 2 else urgency
