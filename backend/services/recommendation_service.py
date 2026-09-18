"""Conservative, non-diagnostic wellbeing guidance shown after assessments."""


def build_recommendations(answers: dict, overall_risk: str) -> dict:
    today = [
        "Keep tracking the measurements you know, and discuss any persistent changes with a qualified clinician.",
        "Use the daily symptom check-in to make changes easier to notice over time.",
    ]
    food = [
        "Build meals mostly from vegetables, fruit, legumes, whole grains, and minimally processed protein sources.",
        "Choose water or unsweetened drinks more often than sugary drinks.",
        "Limit highly processed foods that are often high in salt, added sugar, or saturated fat.",
    ]
    watchouts = []

    if answers.get("smoking"):
        today.insert(0, "If you smoke, consider speaking with a clinician or local quit-support service about a plan that works for you.")
    if (answers.get("physical_activity_hours") or 0) < 2.5:
        today.insert(0, "If it is safe for you, add movement gradually—short walks or similar activity can be a practical starting point.")
    if answers.get("sleep_hours") is not None and answers["sleep_hours"] < 7:
        today.insert(0, "Protect a regular sleep routine and discuss ongoing poor sleep with a clinician.")
    if (answers.get("stress_level") or 0) >= 7:
        today.insert(0, "Make room for a daily stress-reduction practice that feels realistic, such as a brief walk, breathing exercise, or talking with someone you trust.")
    if answers.get("systolic_bp") is not None and answers["systolic_bp"] >= 130:
        food.insert(0, "When choosing packaged foods, compare labels and choose lower-sodium options where possible.")
    if answers.get("fasting_glucose_proxy") is not None and answers["fasting_glucose_proxy"] >= 100:
        food.insert(0, "Pair carbohydrate-rich foods with fiber and protein, and discuss an abnormal glucose result with a clinician.")
    if answers.get("pregnancy_context") in {"currently_pregnant", "previous_gestational_diabetes"}:
        today.insert(0, "Pregnancy-related health needs are individual; use this screening only as a prompt to discuss care with your obstetric or primary-care team.")
    if overall_risk in {"Moderate", "High"}:
        watchouts.append("Arrange a non-urgent appointment with a qualified healthcare professional to review this screening and your measurements.")

    symptoms = " ".join(answers.get("symptoms") or []).lower()
    urgent_words = ("chest pain", "trouble breathing", "shortness of breath", "faint", "weakness", "stroke")
    if any(word in symptoms for word in urgent_words):
        watchouts.insert(0, "New or severe chest pain, trouble breathing, fainting, or stroke-like symptoms need urgent medical care—do not wait for an app assessment.")

    return {"today": today[:4], "food": food[:4], "watchouts": watchouts}
