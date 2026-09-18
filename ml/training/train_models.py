"""
Trains and compares Random Forest, Decision Tree, Logistic Regression, SVM, and
XGBoost for each disease target, calibrates probabilities, picks the best
performer by cross-validated ROC-AUC, and saves a single joblib bundle per
disease containing: the fitted model, the scaler, the feature order, the
chosen algorithm name, and the CV score (used later to decide whether a
probability is trustworthy enough to display).
"""
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, accuracy_score

try:
    from xgboost import XGBClassifier
    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False
    print("[warn] xgboost not installed - skipping it as a candidate model. "
          "Install it (see requirements.txt) to include it in the comparison.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "datasets")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# Minimum CV ROC-AUC we're willing to call "calibrated enough to show a %".
# Below this, the API will show a risk category (Low/Moderate/High) without a
# numeric probability, per the "don't show an uncalibrated probability" rule.
PROBABILITY_TRUST_THRESHOLD = 0.65

CANDIDATES = {
    "random_forest": RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42),
    "decision_tree": DecisionTreeClassifier(max_depth=5, random_state=42),
    "logistic_regression": LogisticRegression(max_iter=2000),
    "svm": SVC(probability=True, kernel="rbf", random_state=42),
}

if _HAS_XGBOOST:
    CANDIDATES["xgboost"] = XGBClassifier(
        n_estimators=250, max_depth=4, learning_rate=0.08,
        eval_metric="logloss", random_state=42,
    )


def train_one(disease_name, csv_file, feature_cols):
    print(f"\n=== Training models for: {disease_name} ===")
    df = pd.read_csv(os.path.join(DATA_DIR, csv_file))
    X = df[feature_cols].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    best_name, best_model, best_score = None, None, -1
    results = {}

    for name, base_model in CANDIDATES.items():
        cv_scores = cross_val_score(base_model, X_train_s, y_train, cv=5, scoring="roc_auc")
        mean_cv = cv_scores.mean()
        results[name] = mean_cv
        print(f"  {name:22s} CV ROC-AUC = {mean_cv:.4f}")
        if mean_cv > best_score:
            best_score, best_name, best_model = mean_cv, name, base_model

    # Fit the winning model on the full training split, calibrated for
    # meaningful probability outputs.
    calibrated = CalibratedClassifierCV(best_model, method="sigmoid", cv=5)
    calibrated.fit(X_train_s, y_train)

    test_pred = calibrated.predict(X_test_s)
    test_proba = calibrated.predict_proba(X_test_s)[:, 1]
    test_auc = roc_auc_score(y_test, test_proba)
    test_acc = accuracy_score(y_test, test_pred)

    print(f"  -> Selected: {best_name} | held-out AUC={test_auc:.4f} acc={test_acc:.4f}")

    # Data-driven per-feature defaults (median across the real training data),
    # used at inference time whenever a user hasn't provided a given field
    # (many of these are clinical/diagnostic-test fields a consumer app can't
    # reasonably ask a layperson for) and also as the comparison baseline when
    # explaining contributing factors.
    feature_defaults = {col: float(df[col].median()) for col in feature_cols}

    bundle = {
        "model": calibrated,
        "scaler": scaler,
        "feature_order": feature_cols,
        "feature_defaults": feature_defaults,
        "chosen_algorithm": best_name,
        "cv_auc": round(best_score, 4),
        "test_auc": round(test_auc, 4),
        "test_accuracy": round(test_acc, 4),
        "probability_trusted": bool(test_auc >= PROBABILITY_TRUST_THRESHOLD),
        "candidate_scores": {k: round(v, 4) for k, v in results.items()},
    }
    out_path = os.path.join(MODEL_DIR, f"{disease_name}_model.joblib")
    joblib.dump(bundle, out_path)
    print(f"  Saved -> {out_path}")
    return bundle


if __name__ == "__main__":
    # Ensure the real, cleaned datasets exist. See ml/datasets/download_real_data.py
    # and ml/datasets/prepare_real_data.py (run those first if this file is missing).
    if not os.path.exists(os.path.join(DATA_DIR, "diabetes.csv")):
        raise SystemExit(
            "No training data found in ml/datasets/. Run these first:\n"
            "  python3 ml/datasets/download_real_data.py\n"
            "  python3 ml/datasets/prepare_real_data.py"
        )

    train_one(
        "diabetes", "diabetes.csv",
        ["pregnancies", "glucose", "blood_pressure", "skin_thickness",
         "insulin", "bmi", "diabetes_pedigree", "age"],
    )
    train_one(
        "hypertension", "hypertension.csv",
        ["age", "sex", "bmi", "smoking"],
    )
    train_one(
        "cardiovascular", "cardiovascular.csv",
        ["age", "sex", "chest_pain_type", "resting_bp", "cholesterol",
         "fasting_blood_sugar_high", "resting_ecg", "max_heart_rate",
         "exercise_angina", "st_depression", "st_slope", "major_vessels", "thalassemia"],
    )
    print("\nAll models trained and saved to ml/models/")
