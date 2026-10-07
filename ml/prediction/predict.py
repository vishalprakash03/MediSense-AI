"""
Loads trained model bundles and turns a user's health profile + assessment
answers into risk predictions with plain-language contributing factors.

The models are trained on real, publicly available clinical datasets (see
ml/datasets/download_real_data.py and prepare_real_data.py):
  - diabetes:       Pima Indians Diabetes Dataset (NIDDK)
  - hypertension:   derived from the CDC/NCHS NHANES August 2021–August 2023 survey's
                     repeated blood-pressure measurements (see prepare_real_data.py)
  - cardiovascular: UCI Cleveland Heart Disease Dataset
  - chronic_kidney_disease: UCI Chronic Kidney Disease Dataset
  - stroke: BRFSS 2023 (CDC) self-reported health survey

Adding a new disease later = add one entry to MODEL_REGISTRY (feature list +
a human-readable label per feature) and drop a matching `<name>_model.joblib`
into ml/models/. Nothing else in the app needs to change.
"""
import os
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

# feature_key -> friendly label shown in "contributing factors" explanations
MODEL_REGISTRY = {
    "diabetes": {
        "file": "diabetes_model.joblib",
        "display_name": "Diabetes",
        "features": {
            "pregnancies": "Number of pregnancies",
            "glucose": "Blood glucose level",
            "blood_pressure": "Diastolic blood pressure",
            "skin_thickness": "Skin fold thickness",
            "insulin": "Serum insulin level",
            "bmi": "Body Mass Index (BMI)",
            "diabetes_pedigree": "Family history strength (diabetes pedigree)",
            "age": "Age",
        },
    },
    "hypertension": {
        "file": "hypertension_model.joblib",
        "display_name": "Hypertension",
        "features": {
            "age": "Age",
            "sex": "Recorded biological profile",
            "bmi": "Body Mass Index (BMI)",
            "smoking": "Smoking history",
        },
    },
    "cardiovascular": {
        "file": "cardiovascular_model.joblib",
        "display_name": "Cardiovascular Risk",
        "features": {
            "age": "Age",
            "sex": "Sex",
            "chest_pain_type": "Chest pain history",
            "resting_bp": "Resting blood pressure",
            "cholesterol": "Cholesterol level",
            "fasting_blood_sugar_high": "Elevated fasting blood sugar",
            "resting_ecg": "Resting ECG result",
            "max_heart_rate": "Maximum heart rate",
            "exercise_angina": "Exercise-induced chest pain",
            "st_depression": "ST depression (exercise ECG)",
            "st_slope": "ST segment slope (exercise ECG)",
            "major_vessels": "Major vessels affected",
            "thalassemia": "Thalassemia test result",
        },
    },
    "chronic_kidney_disease": {
        "file": "chronic_kidney_disease_model.joblib",
        "display_name": "Chronic Kidney Disease Risk",
        "features": {
            "age": "Age",
            "kidney_blood_pressure": "Blood pressure result",
            "blood_glucose": "Blood glucose result",
            "blood_urea": "Blood urea result",
            "serum_creatinine": "Serum creatinine result",
            "hemoglobin": "Haemoglobin result",
        },
    },
    "stroke": {
        "file": "stroke_model.joblib",
        "display_name": "Stroke Risk Screening",
        "features": {
            "age": "Age",
            "sex": "Recorded biological profile",
            "bmi": "Body Mass Index (BMI)",
            "smoking": "Current smoking",
            "physically_active": "Physical activity",
            "hypertension_diagnosis": "History of high blood pressure",
            "diabetes_diagnosis": "History of diabetes",
            "high_cholesterol": "History of high cholesterol",
        },
        # BRFSS stroke-history prevalence is much lower than the other target
        # datasets, so its screening bands are calibrated for that source
        # population rather than applying the general 33%/66% cutoffs.
        "risk_thresholds": (0.03, 0.08),
        "result_note": (
            "This survey-based screening estimates association with a reported "
            "history of stroke. It cannot diagnose a stroke or predict a first stroke."
        ),
    },
}

# Features where a LOWER value than the training-data baseline increases risk
# (protective factors). Everything else assumes higher-than-baseline = more risk.
PROTECTIVE = {"max_heart_rate", "physically_active", "hemoglobin"}

_loaded_bundles = {}


def _load_bundle(disease_key):
    if disease_key not in _loaded_bundles:
        path = os.path.join(MODEL_DIR, MODEL_REGISTRY[disease_key]["file"])
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model for '{disease_key}' not found at {path}. "
                f"Run ml/training/train_models.py first."
            )
        _loaded_bundles[disease_key] = joblib.load(path)
    return _loaded_bundles[disease_key]


def get_feature_defaults(disease_key):
    """Median values from the real training data for this disease's features.
    Used both to fill in fields the user didn't provide and as the comparison
    baseline for explaining contributing factors."""
    return _load_bundle(disease_key)["feature_defaults"]


def get_model_metadata(disease_key):
    """Return the stored evaluation metadata used to gate user-facing output."""
    bundle = _load_bundle(disease_key)
    return {
        "chosen_algorithm": bundle.get("chosen_algorithm"),
        "cv_auc": bundle.get("cv_auc"),
        "test_auc": bundle.get("test_auc"),
        "test_accuracy": bundle.get("test_accuracy"),
        "probability_trusted": bundle.get("probability_trusted", False),
    }


def _risk_level(disease_key, probability):
    low_threshold, high_threshold = MODEL_REGISTRY[disease_key].get(
        "risk_thresholds", (0.33, 0.66)
    )
    if probability < low_threshold:
        return "Low"
    elif probability < high_threshold:
        return "Moderate"
    return "High"


def _contributing_factors(disease_key, user_values, top_n=4):
    labels = MODEL_REGISTRY[disease_key]["features"]
    defaults = get_feature_defaults(disease_key)
    deviations = []
    for key, label in labels.items():
        # Sex assigned at birth is a non-modifiable model input. It should not
        # be presented as a personal "contributing factor" or lifestyle cause.
        if key == "sex":
            continue
        val = user_values.get(key)
        base = defaults.get(key)
        if val is None or base is None:
            continue
        if key in PROTECTIVE:
            delta = base - val  # lower than baseline => contributes to risk
        else:
            delta = val - base
        if delta > 0:
            scale = max(abs(base), 1)
            deviations.append((label, delta / scale))
    deviations.sort(key=lambda x: x[1], reverse=True)
    return [label for label, _ in deviations[:top_n]] or ["No strongly elevated factors detected"]


def predict_disease(disease_key, user_values: dict):
    """
    user_values: dict of feature_key -> numeric value. Any feature required
    by the model but missing from user_values is filled with that feature's
    training-data median (see get_feature_defaults) by the caller
    (backend/services/ml_service.py) before this is invoked; this function
    also falls back to that median itself as a safety net.
    """
    bundle = _load_bundle(disease_key)
    feature_order = bundle["feature_order"]
    defaults = bundle["feature_defaults"]

    x = np.array([[user_values.get(f, defaults.get(f, 0)) for f in feature_order]])
    x_scaled = bundle["scaler"].transform(x)

    proba = float(bundle["model"].predict_proba(x_scaled)[0][1])
    level = _risk_level(disease_key, proba)
    factors = _contributing_factors(disease_key, user_values)

    result = {
        "condition_key": disease_key,
        "condition": MODEL_REGISTRY[disease_key]["display_name"],
        "risk_level": level,
        "contributing_factors": factors,
        "algorithm_used": bundle["chosen_algorithm"],
    }
    # Only surface a numeric probability if the model's calibration was good
    # enough on held-out data to be meaningfully interpreted.
    if bundle.get("probability_trusted"):
        result["probability_percent"] = round(proba * 100, 1)
    else:
        result["probability_percent"] = None
    if MODEL_REGISTRY[disease_key].get("result_note"):
        result["result_note"] = MODEL_REGISTRY[disease_key]["result_note"]

    return result


def predict_all(user_values: dict):
    """Runs every registered disease model, skipping any whose model file
    hasn't been trained yet."""
    results = []
    for disease_key in MODEL_REGISTRY:
        try:
            results.append(predict_disease(disease_key, user_values))
        except FileNotFoundError:
            continue
    return results


def overall_risk(results):
    order = {"Low": 0, "Moderate": 1, "High": 2}
    if not results:
        return "Unknown"
    worst = max(results, key=lambda r: order.get(r["risk_level"], 0))
    return worst["risk_level"]


if __name__ == "__main__":
    sample = {
        "age": 52, "sex": 1, "bmi": 31.2, "glucose": 145, "blood_pressure": 88,
        "cholesterol": 240, "max_heart_rate": 140, "resting_bp": 138,
        "fasting_blood_sugar_high": 1,
    }
    for r in predict_all(sample):
        print(r)
