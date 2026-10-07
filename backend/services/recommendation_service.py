"""Conservative, non-diagnostic wellbeing guidance shown after assessments."""


# These are educational prompts, not treatment plans. They are intentionally
# condition-specific so a user can see what part of the general plan relates to
# each screening result. Kidney food restrictions, in particular, must be
# individualized from laboratory results by a qualified professional.
CONDITION_GUIDANCE = {
    "diabetes": {
        "condition": "Diabetes",
        "lifestyle": [
            "If it is safe for you, build regular movement into your week and start gradually if you are inactive.",
            "Keep any glucose readings, symptoms, and medicines organised for your next clinical review.",
        ],
        "food": [
            "Choose higher-fibre foods such as vegetables, pulses, and whole grains more often.",
            "Choose water or unsweetened drinks instead of sugary drinks when possible.",
        ],
    },
    "hypertension": {
        "condition": "Hypertension",
        "lifestyle": [
            "If you monitor blood pressure at home, record readings and share the pattern with your clinician.",
            "Avoid tobacco and use stress-management and regular activity habits that are realistic for you.",
        ],
        "food": [
            "Compare packaged-food labels and choose lower-sodium options where possible.",
            "Use herbs, spices, lemon, or other flavourings instead of adding extra salt.",
        ],
    },
    "cardiovascular": {
        "condition": "Cardiovascular Risk",
        "lifestyle": [
            "Do not ignore new chest discomfort, breathlessness, fainting, or symptoms that occur with activity—seek urgent care when severe or sudden.",
            "If you smoke, ask a clinician or quit-support service about a plan to stop.",
        ],
        "food": [
            "Prefer unsaturated fats such as nuts, seeds, and plant oils in suitable portions over foods high in saturated or trans fat.",
            "Base more meals on vegetables, fruit, beans, and whole grains.",
        ],
    },
    "chronic_kidney_disease": {
        "condition": "Chronic Kidney Disease Risk",
        "lifestyle": [
            "Arrange a clinician review of new or abnormal kidney laboratory results; creatinine alone cannot confirm kidney disease.",
            "Review medicines, supplements, and over-the-counter pain medicines with a pharmacist or clinician rather than changing them on your own.",
        ],
        "food": [
            "Reduce highly processed, salty foods to support both kidney and blood-pressure health.",
            "Do not start strict potassium, protein, or fluid restrictions without individual advice from a kidney clinician or dietitian.",
        ],
    },
    "stroke": {
        "condition": "Stroke Risk Screening",
        "lifestyle": [
            "Prioritise blood-pressure follow-up, regular activity appropriate for your health, and avoiding tobacco.",
            "Call emergency services immediately for sudden face drooping, arm weakness, speech trouble, severe imbalance, or a sudden severe headache.",
        ],
        "food": [
            "Choose meals lower in sodium, added sugar, and saturated fat more often.",
            "Use vegetables, fruit, legumes, whole grains, and minimally processed protein sources as the base of meals.",
        ],
    },
}


def build_recommendations(
    answers: dict, overall_risk: str, predicted_conditions: list[dict] | None = None,
) -> dict:
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
    if answers.get("hypertension_diagnosis"):
        today.insert(0, "If you have been diagnosed with high blood pressure, follow your clinician's plan and bring home readings to your next review.")
    if answers.get("serum_creatinine") is not None or answers.get("blood_urea") is not None:
        today.insert(0, "Discuss kidney-related laboratory results with a qualified clinician, especially if they are new, abnormal, or changing.")
    if answers.get("pregnancy_context") in {"currently_pregnant", "previous_gestational_diabetes"}:
        today.insert(0, "Pregnancy-related health needs are individual; use this screening only as a prompt to discuss care with your obstetric or primary-care team.")
    if overall_risk in {"Moderate", "High"}:
        watchouts.append("Arrange a non-urgent appointment with a qualified healthcare professional to review this screening and your measurements.")

    symptoms = " ".join(answers.get("symptoms") or []).lower()
    urgent_words = ("chest pain", "trouble breathing", "shortness of breath", "faint", "weakness", "stroke")
    if any(word in symptoms for word in urgent_words):
        watchouts.insert(0, "New or severe chest pain, trouble breathing, fainting, or stroke-like symptoms need urgent medical care—do not wait for an app assessment.")

    condition_keys = {
        item.get("condition_key")
        for item in (predicted_conditions or [])
        if item.get("condition_key") in CONDITION_GUIDANCE
    }
    # Preserve the registered-model order instead of the arbitrary order of a set.
    condition_guidance = [
        CONDITION_GUIDANCE[key] for key in CONDITION_GUIDANCE if key in condition_keys
    ]

    return {
        "today": today[:4],
        "food": food[:4],
        "watchouts": watchouts,
        "condition_guidance": condition_guidance,
    }
