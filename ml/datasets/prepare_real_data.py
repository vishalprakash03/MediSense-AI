"""
Cleans the raw downloaded datasets and produces the three training CSVs
consumed by ml/training/train_models.py:

  diabetes.csv        - real Pima Indians Diabetes data
  cardiovascular.csv  - real UCI Cleveland heart disease data
  hypertension.csv    - derived from the official CDC/NCHS NHANES
                         August 2021–August 2023
                         survey, using repeated measured blood-pressure values
                         to assign a hypertension label

Run after download_real_data.py:

    python3 ml/datasets/prepare_real_data.py

--- Notes on the hypertension dataset ---
The old 303-row Cleveland-derived dataset is replaced with the much larger
NHANES August 2021–August 2023 adult survey. A positive label is derived from the mean of
at least two measured blood-pressure readings (systolic >=130 mmHg or
diastolic >=80 mmHg). Those readings are excluded from the features, so the
model learns only from the consumer-facing inputs the application collects:
age, sex, BMI, and smoking history.
"""
import os
import pandas as pd
import numpy as np

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")
OUT_DIR = os.path.dirname(__file__)

HYPERTENSION_SYSTOLIC_THRESHOLD = 130  # ACC/AHA Stage 1 hypertension, mmHg
HYPERTENSION_DIASTOLIC_THRESHOLD = 80  # ACC/AHA Stage 1 hypertension, mmHg

NHANES_FILES = {
    "demographics": "nhanes_demographics_2021_2023.xpt",
    "body_measures": "nhanes_body_measures_2021_2023.xpt",
    "smoking": "nhanes_smoking_2021_2023.xpt",
    "blood_pressure": "nhanes_blood_pressure_2021_2023.xpt",
}


def prepare_diabetes():
    path = os.path.join(RAW_DIR, "diabetes_raw.csv")
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Pregnancies": "pregnancies",
        "Glucose": "glucose",
        "BloodPressure": "blood_pressure",
        "SkinThickness": "skin_thickness",
        "Insulin": "insulin",
        "BMI": "bmi",
        "DiabetesPedigreeFunction": "diabetes_pedigree",
        "Age": "age",
        "Outcome": "label",
    })

    # In this dataset, 0 is used as a placeholder for "missing" in several
    # clinically-implausible columns (nobody has 0 blood pressure or BMI).
    # Replace those zeros with NaN, then impute with the column median.
    zero_as_missing = ["glucose", "blood_pressure", "skin_thickness", "insulin", "bmi"]
    for col in zero_as_missing:
        df[col] = df[col].replace(0, np.nan)
        df[col] = df[col].fillna(df[col].median())

    out_path = os.path.join(OUT_DIR, "diabetes.csv")
    df.to_csv(out_path, index=False)
    print(f"diabetes.csv: {df.shape[0]} rows, positive rate {df.label.mean():.3f} -> {out_path}")
    return df


def _load_clean_heart():
    path = os.path.join(RAW_DIR, "heart_raw.csv")
    df = pd.read_csv(path)
    df = df.rename(columns={
        "age": "age",
        "sex": "sex",
        "cp": "chest_pain_type",
        "trestbps": "resting_bp",
        "chol": "cholesterol",
        "fbs": "fasting_blood_sugar_high",
        "restecg": "resting_ecg",
        "thalach": "max_heart_rate",
        "exang": "exercise_angina",
        "oldpeak": "st_depression",
        "slope": "st_slope",
        "ca": "major_vessels",
        "thal": "thalassemia",
        "target": "label",
    })
    # This mirror's `target` is already binary (0 = no disease, 1 = disease
    # present) for the 303-row Cleveland subset used here.
    return df


def prepare_cardiovascular():
    df = _load_clean_heart()
    out_path = os.path.join(OUT_DIR, "cardiovascular.csv")
    df.to_csv(out_path, index=False)
    print(f"cardiovascular.csv: {df.shape[0]} rows, positive rate {df.label.mean():.3f} -> {out_path}")
    return df


def prepare_hypertension():
    """Create an adult hypertension dataset from the CDC/NCHS NHANES files.

    The NHANES XPT components share the participant identifier, ``SEQN``.
    Smoking means the participant reported having smoked at least 100
    cigarettes in their lifetime (SMQ020: yes/no). Participants with missing
    answers, BMI, or fewer than two BP readings are excluded rather than
    imputed, preserving a traceable real-data training set.
    """
    paths = {name: os.path.join(RAW_DIR, filename) for name, filename in NHANES_FILES.items()}
    missing = [path for path in paths.values() if not os.path.exists(path)]
    if missing:
        raise FileNotFoundError(
            "Missing NHANES raw file(s): " + ", ".join(os.path.basename(path) for path in missing)
        )

    demographics = pd.read_sas(paths["demographics"], format="xport", encoding="utf-8")
    body_measures = pd.read_sas(paths["body_measures"], format="xport", encoding="utf-8")
    smoking = pd.read_sas(paths["smoking"], format="xport", encoding="utf-8")
    blood_pressure = pd.read_sas(paths["blood_pressure"], format="xport", encoding="utf-8")

    demographics = demographics[["SEQN", "RIDAGEYR", "RIAGENDR"]]
    body_measures = body_measures[["SEQN", "BMXBMI"]]
    smoking = smoking[["SEQN", "SMQ020"]]
    # Starting with this NHANES cycle, the official component uses
    # oscillometric readings (BPXOSY/BPXODI) rather than the older BPXSY/BPXDI
    # names. These are repeated measured values, not inputs to the model.
    systolic_columns = ["BPXOSY1", "BPXOSY2", "BPXOSY3"]
    diastolic_columns = ["BPXODI1", "BPXODI2", "BPXODI3"]
    bp_columns = [*systolic_columns, *diastolic_columns]
    blood_pressure = blood_pressure[["SEQN", *bp_columns]]

    df = demographics.merge(body_measures, on="SEQN").merge(smoking, on="SEQN").merge(
        blood_pressure, on="SEQN"
    )
    df["systolic_mean"] = df[systolic_columns].mean(axis=1)
    df["diastolic_mean"] = df[diastolic_columns].mean(axis=1)

    # The study population is adult and requires repeated measured values.
    df = df[
        (df["RIDAGEYR"] >= 18)
        & (df["BMXBMI"].between(10, 100))
        & (df["SMQ020"].isin([1, 2]))
        & (df[systolic_columns].notna().sum(axis=1) >= 2)
        & (df[diastolic_columns].notna().sum(axis=1) >= 2)
    ].copy()

    df["label"] = (
        (df["systolic_mean"] >= HYPERTENSION_SYSTOLIC_THRESHOLD)
        | (df["diastolic_mean"] >= HYPERTENSION_DIASTOLIC_THRESHOLD)
    ).astype(int)
    # RIAGENDR is 1=male / 2=female; normalize to the application's 1/0 form.
    df["sex"] = (df["RIAGENDR"] == 1).astype(int)
    df["smoking"] = (df["SMQ020"] == 1).astype(int)
    df = df.rename(columns={"RIDAGEYR": "age", "BMXBMI": "bmi"})
    df = df[["age", "sex", "bmi", "smoking", "label"]]

    out_path = os.path.join(OUT_DIR, "hypertension.csv")
    df.to_csv(out_path, index=False)
    print(f"hypertension.csv: {df.shape[0]} rows, positive rate {df.label.mean():.3f} -> {out_path}")
    print(
        "  (NHANES adults; label = mean BP >= "
        f"{HYPERTENSION_SYSTOLIC_THRESHOLD}/{HYPERTENSION_DIASTOLIC_THRESHOLD} mmHg; "
        "measured BP excluded from features)"
    )
    return df


if __name__ == "__main__":
    missing = [f for f in ("diabetes_raw.csv", "heart_raw.csv", *NHANES_FILES.values())
               if not os.path.exists(os.path.join(RAW_DIR, f))]
    if missing:
        raise SystemExit(
            f"Missing raw file(s): {missing}. Run download_real_data.py first, "
            f"or place them manually in {RAW_DIR}"
        )

    prepare_diabetes()
    prepare_cardiovascular()
    prepare_hypertension()
    print("\nDone. Next, run: python3 ml/training/train_models.py")
