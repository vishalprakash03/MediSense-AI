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

def make_candidates(class_weight=None, xgb_scale_pos_weight=1.0, include_svm=True):
    """Return fresh estimators for a fair comparison on each dataset."""
    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=6, random_state=42,
            class_weight=class_weight, n_jobs=-1,
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=5, random_state=42, class_weight=class_weight,
        ),
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight=class_weight,
        ),
    }
    # An RBF SVM has quadratic memory/time behaviour. It is included for the
    # small clinical datasets but deliberately omitted for the large BRFSS
    # survey dataset below.
    if include_svm:
        candidates["svm"] = SVC(
            probability=True, kernel="rbf", random_state=42, class_weight=class_weight,
        )
    if _HAS_XGBOOST:
        candidates["xgboost"] = XGBClassifier(
            n_estimators=250, max_depth=4, learning_rate=0.08,
            eval_metric="logloss", random_state=42, n_jobs=-1,
            scale_pos_weight=xgb_scale_pos_weight,
        )
    return candidates


def train_one(
    disease_name, csv_file, feature_cols, class_weight=None,
    xgb_scale_pos_weight=1.0, max_training_rows=None, include_svm=True,
):
    print(f"\n=== Training models for: {disease_name} ===")
    df = pd.read_csv(os.path.join(DATA_DIR, csv_file))
    if max_training_rows and len(df) > max_training_rows:
        df, _ = train_test_split(
            df, train_size=max_training_rows, random_state=42, stratify=df["label"],
        )
        print(f"  Using a stratified {len(df):,}-row training sample from {csv_file}")
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

    for name, base_model in make_candidates(
        class_weight, xgb_scale_pos_weight, include_svm,
    ).items():
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
        "training_rows": int(len(df)),
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
    train_one(
        "chronic_kidney_disease", "chronic_kidney_disease.csv",
        ["age", "kidney_blood_pressure", "blood_glucose", "blood_urea", "serum_creatinine", "hemoglobin"],
    )
    # Stroke-history reports are uncommon in BRFSS. Weighting makes each
    # candidate consider the minority class during selection; the final
    # CalibratedClassifierCV step restores probability calibration.
    stroke_df = pd.read_csv(os.path.join(DATA_DIR, "stroke.csv"))
    positive_count = int(stroke_df["label"].sum())
    negative_count = int((stroke_df["label"] == 0).sum())
    train_one(
        "stroke", "stroke.csv",
        ["age", "sex", "bmi", "smoking", "physically_active", "hypertension_diagnosis",
         "diabetes_diagnosis", "high_cholesterol"],
        class_weight="balanced",
        xgb_scale_pos_weight=negative_count / max(positive_count, 1),
        max_training_rows=100_000,
        include_svm=False,
    )
    print("\nAll models trained and saved to ml/models/")
