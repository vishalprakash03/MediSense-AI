"""
A lightweight, deterministic conversational flow for the AI Health Assistant.

Design note: the spec calls for a natural, one-question-at-a-time conversation
rather than a big form. This module implements that with a scripted question
sequence plus simple free-text parsing, so it runs with zero external LLM
dependency. To upgrade this later to a full LLM-driven conversation, swap
`extract_value()` and `next_question()` for calls to your LLM of choice while
keeping the same state-machine shape (state stored per-conversation in Mongo).
"""
import re

QUESTION_FLOW = [
    {"key": "age", "question": "To begin, how old are you?", "type": "int"},
    {"key": "gender", "question": "How do you describe your gender? (male / female / other)", "type": "str"},
    {
        "key": "pregnancy_context",
        "question": (
            "If pregnancy-related health information applies to you, which best fits: "
            "currently pregnant / previous gestational diabetes / neither / skip?"
        ),
        "type": "pregnancy_context",
        "when_gender": {"female"},
    },
    {"key": "height_cm", "question": "What is your height in centimetres?", "type": "float"},
    {"key": "weight_kg", "question": "What is your current weight in kilograms?", "type": "float"},
    {"key": "family_history", "question": "Does anyone in your immediate family have diabetes, high blood pressure, or heart disease? Please answer yes or no.", "type": "bool"},
    {"key": "smoking", "question": "Do you currently smoke or use tobacco? Please answer yes or no.", "type": "bool"},
    {"key": "physical_activity_hours", "question": "In a typical week, about how many hours are you physically active or exercising?", "type": "float"},
    {"key": "sleep_hours", "question": "On average, how many hours do you sleep each night?", "type": "float"},
    {"key": "stress_level", "question": "On a scale of 1 to 10, how would you rate your usual stress level?", "type": "int"},
    {"key": "systolic_bp", "question": "If you have a recent blood-pressure result, what was the top (systolic) number? For example, 120. Say 'skip' if you do not know.", "type": "float_optional"},
    {"key": "heart_rate", "question": "If you know it, what is your usual resting heart rate in beats per minute? Say 'skip' if unknown.", "type": "float_optional"},
    {"key": "fasting_glucose_proxy", "question": "If you have a recent fasting blood-glucose result, what was it in mg/dL? Say 'skip' if unknown.", "type": "float_optional"},
    {"key": "cholesterol_proxy", "question": "If you have a recent total cholesterol result, what was it in mg/dL? Say 'skip' if unknown.", "type": "float_optional"},
    {"key": "symptoms", "question": "Now, please tell me what symptoms or health changes brought you here today. Include all that apply, or say 'none'.", "type": "text"},
    {"key": "symptom_duration", "question": "When did these symptoms or changes begin? For example: today, three days ago, or several months ago. Say 'skip' if not applicable.", "type": "str_optional"},
    {"key": "symptom_trend", "question": "Since they began, are they improving, staying about the same, or getting worse? Say 'skip' if not applicable.", "type": "str_optional"},
    {"key": "notes", "question": "Finally, please write any additional note you would want a doctor to read. You can mention diagnoses, medicines, allergies, recent test results, or anything that concerns you. Say 'skip' if there is nothing else.", "type": "str_optional"},
]

GREETING = (
    "Hello! I'm MediSense AI. I can help you understand possible health risks "
    "based on the information you share with me. This is not a medical diagnosis — "
    "just a preliminary risk assessment. Let's start with a few quick questions."
)

DONE_MESSAGE = (
    "Thank you — I have recorded your intake and clinical note. I’ll now show a "
    "preliminary screening summary. This is not a medical diagnosis. Please seek "
    "professional care for concerning, new, or worsening symptoms."
)

YES_WORDS = {"yes", "y", "yeah", "yep", "true", "sure"}
NO_WORDS = {"no", "n", "nope", "false", "none", "nah"}
SKIP_WORDS = {"skip", "unknown", "don't know", "dont know", "not sure", "na", "n/a"}

NUMERIC_RANGES = {
    "age": (1, 120),
    "height_cm": (50, 250),
    "weight_kg": (2, 500),
    "physical_activity_hours": (0, 168),
    "sleep_hours": (0, 24),
    "stress_level": (1, 10),
    "systolic_bp": (50, 300),
    "heart_rate": (20, 300),
    "fasting_glucose_proxy": (20, 800),
    "cholesterol_proxy": (50, 1000),
}

GENDER_VALUES = {
    "male": "male", "man": "male", "m": "male",
    "female": "female", "woman": "female", "f": "female",
    "other": "other", "nonbinary": "other", "non-binary": "other",
    "prefer not to say": "other",
}

PREGNANCY_CONTEXTS = {
    "pregnant": "currently_pregnant",
    "currently pregnant": "currently_pregnant",
    "previous gestational diabetes": "previous_gestational_diabetes",
    "gestational diabetes": "previous_gestational_diabetes",
    "neither": "neither",
    "no": "neither",
}


def extract_value(raw_text: str, field_type: str):
    text = raw_text.strip().lower()

    if field_type == "bool":
        if any(w in text for w in YES_WORDS):
            return True
        if any(w in text for w in NO_WORDS):
            return False
        return None  # couldn't parse; caller should re-ask

    if field_type in ("float_optional",) and any(w in text for w in SKIP_WORDS):
        return None

    if field_type == "str_optional" and text in SKIP_WORDS:
        return None

    if field_type == "pregnancy_context":
        if text in SKIP_WORDS:
            return "skipped"
        return PREGNANCY_CONTEXTS.get(text)

    if field_type in ("int", "float", "float_optional"):
        match = re.search(r"-?\d+(\.\d+)?", text)
        if not match:
            return None
        num = float(match.group())
        return int(num) if field_type == "int" else num

    if field_type == "text":
        if text in NO_WORDS or text in SKIP_WORDS:
            return []
        # naive symptom split on commas/"and"
        parts = re.split(r",| and ", raw_text.strip())
        return [p.strip() for p in parts if p.strip()]

    return raw_text.strip()


def is_skipped(raw_text: str) -> bool:
    return raw_text.strip().lower() in SKIP_WORDS


def normalize_gender(raw_text: str):
    return GENDER_VALUES.get(raw_text.strip().lower())


def is_valid_value(key: str, value) -> bool:
    if key not in NUMERIC_RANGES:
        return True
    low, high = NUMERIC_RANGES[key]
    return low <= value <= high


def get_next_step(answers: dict):
    for step in QUESTION_FLOW:
        if step["key"] in answers:
            continue
        allowed_genders = step.get("when_gender")
        if allowed_genders and answers.get("gender") not in allowed_genders:
            continue
        if step["key"] not in answers:
            return step
    return None


def process_turn(conversation_state: dict, user_message: str):
    """
    conversation_state: {"answers": {...}, "awaiting_key": "age" | None, "started": bool}
    Returns (reply_text, updated_state, is_complete)
    """
    answers = conversation_state.get("answers", {})
    awaiting_key = conversation_state.get("awaiting_key")

    if not conversation_state.get("started"):
        first_step = QUESTION_FLOW[0]
        new_state = {"answers": {}, "awaiting_key": first_step["key"], "started": True}
        return f"{GREETING}\n\n{first_step['question']}", new_state, False

    # Parse the answer to the question we just asked
    if awaiting_key:
        step = next(s for s in QUESTION_FLOW if s["key"] == awaiting_key)
        value = extract_value(user_message, step["type"])
        if value is None and step["type"] in {"float_optional", "str_optional"} and is_skipped(user_message):
            answers[awaiting_key] = None
        elif value is None:
            return (
                f"Sorry, I didn't quite catch that. {step['question']}",
                conversation_state,
                False,
            )
        elif awaiting_key == "gender":
            normalized_gender = normalize_gender(value)
            if normalized_gender is None:
                return (
                    f"Please answer male, female, or other. {step['question']}",
                    conversation_state,
                    False,
                )
            answers[awaiting_key] = normalized_gender
        elif not is_valid_value(awaiting_key, value):
            low, high = NUMERIC_RANGES[awaiting_key]
            return (
                f"Please enter a value between {low} and {high}. {step['question']}",
                conversation_state,
                False,
            )
        else:
            answers[awaiting_key] = value

    next_step = get_next_step(answers)
    if next_step is None:
        new_state = {"answers": answers, "awaiting_key": None, "started": True}
        return DONE_MESSAGE, new_state, True

    new_state = {"answers": answers, "awaiting_key": next_step["key"], "started": True}
    return next_step["question"], new_state, False
