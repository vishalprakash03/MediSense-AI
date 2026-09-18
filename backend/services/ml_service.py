"""
Bridges the FastAPI layer to the ml/ package. Keeps model-loading and
feature-engineering logic out of route handlers.

The trained models expect real clinical/biometric fields (see
ml/prediction/predict.py MODEL_REGISTRY). Our conversational assistant only
collects what a layperson can reasonably self-report (age, gender, height/
weight, blood pressure if known, resting heart rate, smoking, family history,
lifestyle habits, etc.) -- it can't ask someone for their ECG slope or major
vessel count. Fields the app doesn't collect are filled with that specific
model's training-data median (a principled, disclosed default -- see
get_feature_defaults) rather than a guess.

Lifestyle fields the assistant collects (smoking, physical activity, sleep,
stress) aren't part of these particular real datasets, so they aren't fed
into the ML models directly -- they still flow into the personalized
preventive recommendations shown alongside the prediction.
"""
import sys
import os

# Make the sibling `ml/` package importable regardless of where uvicorn is launched from.
ML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml"))
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from prediction.predict import (  # noqa: E402
    predict_all, predict_disease, overall_risk, get_feature_defaults, get_model_metadata, MODEL_REGISTRY,
)

# These are product-quality gates, not clinical diagnostic criteria. They prevent
# the consumer app from presenting a risk category when nearly every model input
# would otherwise be a training-data median.
MINIMUM_USER_FEATURES = {
    "diabetes": ("age", "bmi", "glucose"),
    "cardiovascular": ("age", "sex", "resting_bp", "cholesterol", "max_heart_rate"),
    "hypertension": ("age", "sex", "bmi", "smoking"),
}


def _compute_bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm:
        return None
    h_m = height_cm / 100
    return round(weight_kg / (h_m ** 2), 1)


def _sex_to_numeric(gender):
    if gender is None:
        return None
    g = str(gender).strip().lower()
    if g == "male":
        return 1
    if g == "female":
        return 0
    return None  # "other" / unrecognized -> let the model default (dataset mode) apply


def _smoking_to_numeric(smoking):
    if smoking is None:
        return None
    if isinstance(smoking, bool):
        return int(smoking)
    value = str(smoking).strip().lower()
    if value in {"current", "former", "yes", "true", "1"}:
        return 1
    if value in {"never", "no", "false", "0"}:
        return 0
    return None


def _map_user_inputs(answers: dict, profile: dict) -> dict:
    """Collects everything the app actually knows about the user into a flat
    dict keyed by the *dataset* feature names, doing unit/field translation
    where needed. Returns only keys we have real values for -- callers fill
    in the rest from each model's own training-data defaults."""
    merged = {**profile, **{k: v for k, v in answers.items() if v is not None}}

    bmi = merged.get("bmi") or _compute_bmi(merged.get("weight_kg"), merged.get("height_cm"))
    sex = _sex_to_numeric(merged.get("gender"))
    smoking = _smoking_to_numeric(merged.get("smoking", merged.get("smoking_status")))

    mapped = {
        "age": merged.get("age"),
        "bmi": bmi,
        "sex": sex,
        "resting_bp": merged.get("systolic_bp"),
        "cholesterol": merged.get("cholesterol_proxy"),
        "max_heart_rate": merged.get("heart_rate") or merged.get("resting_heart_rate"),
        "glucose": merged.get("fasting_glucose_proxy"),
        "smoking": smoking,
    }
    # Diastolic BP isn't collected directly; approximate it from systolic
    # (roughly 2/3 of systolic is a commonly used rough clinical rule of
    # thumb) only when we actually have a systolic reading to work from.
    if merged.get("systolic_bp"):
        mapped["blood_pressure"] = round(merged["systolic_bp"] * 0.66, 1)

    # Fasting blood sugar > 120 mg/dl is a yes/no clinical flag; derive it
    # from the glucose reading if the user gave one.
    if merged.get("fasting_glucose_proxy") is not None:
        mapped["fasting_blood_sugar_high"] = int(merged["fasting_glucose_proxy"] > 120)

    return {k: v for k, v in mapped.items() if v is not None}


def build_feature_dict(disease_key: str, answers: dict, profile: dict = None) -> dict:
    """Returns a complete feature dict for one disease model: real user
    values where we have them, training-data medians for everything else
    (chest pain type, ECG results, etc. that a consumer app can't ask)."""
    profile = profile or {}
    user_inputs = _map_user_inputs(answers, profile)
    defaults = get_feature_defaults(disease_key)
    feature_order = MODEL_REGISTRY[disease_key]["features"].keys()

    return {f: user_inputs.get(f, defaults.get(f)) for f in feature_order}


def run_predictions(answers: dict, profile: dict = None, diseases=None):
    disease_keys = diseases or list(MODEL_REGISTRY.keys())
    profile = profile or {}
    user_inputs = _map_user_inputs(answers, profile)

    results = []
    unavailable_predictions = []
    for disease_key in disease_keys:
        if disease_key not in MODEL_REGISTRY:
            continue
        model_features = MODEL_REGISTRY[disease_key]["features"]
        condition = MODEL_REGISTRY[disease_key]["display_name"]

        required_features = MINIMUM_USER_FEATURES.get(disease_key, ())
        missing_features = [feature for feature in required_features if feature not in user_inputs]
        if missing_features:
            unavailable_predictions.append({
                "condition": condition,
                "status": "insufficient_data",
                "reason": "More user-provided clinical information is needed before this assessment can be shown.",
                "missing_inputs": [model_features[feature] for feature in missing_features],
            })
            continue

        try:
            metadata = get_model_metadata(disease_key)
        except FileNotFoundError:
            unavailable_predictions.append({
                "condition": condition,
                "status": "model_unavailable",
                "reason": "The trained model is not available on the server yet.",
                "missing_inputs": [],
            })
            continue

        if not metadata["probability_trusted"]:
            unavailable_predictions.append({
                "condition": condition,
                "status": "model_withheld",
                "reason": "This assessment is temporarily unavailable while its model is being improved.",
                "missing_inputs": [],
            })
            continue

        try:
            feature_dict = build_feature_dict(disease_key, answers, profile)
            result = predict_disease(disease_key, feature_dict)
            assumed_features = [
                label for key, label in model_features.items()
                if key not in user_inputs
            ]
            result["input_coverage_percent"] = round(
                (len(model_features) - len(assumed_features)) / len(model_features) * 100,
                1,
            )
            result["assumed_features"] = assumed_features
            results.append(result)
        except FileNotFoundError:
            unavailable_predictions.append({
                "condition": condition,
                "status": "model_unavailable",
                "reason": "The trained model is not available on the server yet.",
                "missing_inputs": [],
            })

    return {
        "predicted_conditions": results,
        "unavailable_predictions": unavailable_predictions,
        "overall_risk": overall_risk(results) if results else "Insufficient data",
    }
