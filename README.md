# MediSense AI

An intelligent healthcare prediction and personalized health assistant.

**Stack:** Next.js + React + Tailwind (frontend) · FastAPI (backend) · MongoDB (database) ·
scikit-learn / XGBoost (ML: Random Forest, Decision Tree, Logistic Regression, SVM, XGBoost)

> ⚠️ MediSense AI provides preliminary health-risk information based on data the user provides.
> It is **not** a medical diagnosis and does not replace professional medical advice.

---

## 1. Project layout

```
MediSense-AI/
├── frontend/        Next.js app (App Router) + Tailwind CSS
├── backend/         FastAPI REST API (auth, profile, health, assistant)
├── ml/              Data generation, training, and prediction pipeline
└── requirements.txt Backend + ML python dependencies
```

## 2. Running the ML pipeline (downloads real data, trains & saves models)

The models are trained on real, publicly available clinical datasets:

| Disease | Source | Records |
|---|---|---|
| Diabetes | Pima Indians Diabetes Dataset (NIDDK) | 768 real patients |
| Cardiovascular Risk | UCI Cleveland Heart Disease Dataset | 303 real patients |
| Hypertension | CDC/NCHS NHANES August 2021–August 2023 adult survey; label derived from repeated measured blood pressure (mean systolic ≥130 mmHg or diastolic ≥80 mmHg) | Prepared locally from official survey components |

```bash
cd ml
python3 datasets/download_real_data.py   # downloads the source data (needs internet)
python3 datasets/prepare_real_data.py    # cleans + derives the 3 training CSVs into datasets/
python3 training/train_models.py         # trains + compares models, saves best one per disease to ml/models/
```

This produces `ml/models/diabetes_model.joblib`, `hypertension_model.joblib`, and
`cardiovascular_model.joblib`, each bundled with its scaler, feature order,
**data-driven per-feature defaults** (training-data medians), and metadata
(`chosen_algorithm`, cross-validated / held-out AUC) in a single joblib file.

> **Note on features:** The diabetes and cardiovascular models use real *clinical/biometric* datasets (labs, vitals,
> diagnostic test results) — not lifestyle datasets. So the ML models themselves
> predict from things like age, sex, BMI, blood pressure, cholesterol, glucose, and
> heart rate. Fields a consumer app can't reasonably ask a layperson for (ECG results,
> ST-segment slope, major-vessel count, etc.) are filled in with that disease's
> training-data median rather than guessed. The assistant's lifestyle questions
> (smoking, activity, sleep, stress, family history) still drive the personalized
> preventive recommendations shown alongside the prediction — they just aren't fed
> into these specific models, since no simple public dataset combines both cleanly.
>
> The hypertension model instead uses a larger real-world NHANES adult dataset and
> only age, sex, BMI, and smoking history—the inputs the app collects. It is shown
> only after its saved held-out evaluation meets the project's probability-trust
> threshold; otherwise the API returns an unavailable state rather than a risk label.
>
> If either data source mirror ever goes down, search for "pima indians diabetes csv"
> or "UCI heart disease heart.csv" — any mirror with matching column names
> (`Pregnancies,Glucose,BloodPressure,...` / `age,sex,cp,trestbps,chol,...`) works as
> a drop-in replacement; just update the URLs in `download_real_data.py`.

## 3. Running the backend

```bash
python -m venv venv && source venv/bin/activate      # optional
pip install -r requirements.txt

# Environment variables (create backend/.env or export directly):
#   MONGO_URI=mongodb://localhost:27017
#   DB_NAME=medisense
#   JWT_SECRET=change-me-to-a-long-random-string

# run from the project root (backend/ uses absolute `backend.*` imports)
uvicorn backend.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

## 4. Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

Open `http://localhost:3000`.

## 5. API summary

```
POST /api/auth/register
POST /api/auth/login

GET  /api/user/profile
PUT  /api/user/profile

POST /api/assistant/chat          # conversational one-question-at-a-time flow
POST /api/health/assessment       # store a structured assessment answer set
POST /api/health/predict          # run the ML pipeline against an assessment
GET  /api/health/history
GET  /api/health/latest

POST /api/health/measurements
GET  /api/health/measurements

POST /api/health/symptoms
GET  /api/health/symptoms/latest
```

All endpoints except register/login use the authenticated session cookie.

## 6. Adding a new disease model later

1. Add a data-generation function in `ml/datasets/generate_data.py`.
2. Add a training block in `ml/training/train_models.py` (same pattern as the existing three).
3. Register the new model + its feature list in `ml/prediction/predict.py`'s `MODEL_REGISTRY`.

No other code needs to change — the API, dashboard, and history views are disease-agnostic.

## 7. Recent research references (2023–2026)

The application includes a **Research & References** page at `/references`. The
following sources support the project presentation, its health-monitoring
workflow, and its safety-first screening approach. They do not make the app a
diagnostic or treatment service.

1. Cuevas-Chávez, A., et al. (2023). *A Systematic Review of Machine Learning and IoT Applied to the Prediction and Monitoring of Cardiovascular Diseases.* Healthcare, 11(16), 2240. https://doi.org/10.3390/healthcare11162240
2. World Health Organization. (2023). *Global Report on Hypertension: The Race Against a Silent Killer.* https://www.who.int/publications/i/item/9789240081062
3. McEvoy, J. W., et al. (2024). *2024 ESC Guidelines for the Management of Elevated Blood Pressure and Hypertension.* European Heart Journal, 45(38), 3912–4018. https://doi.org/10.1093/eurheartj/ehae178
4. Liu, T., et al. (2025). *Machine Learning Based Prediction Models for Cardiovascular Disease Risk Using Electronic Health Records Data: Systematic Review and Meta-analysis.* European Heart Journal – Digital Health, 6(1), 7–22. https://doi.org/10.1093/ehjdh/ztae080
5. Wan, S., Wan, F., & Dai, X. J. (2025). *Machine Learning Approaches for Cardiovascular Disease Prediction: A Review.* Archives of Cardiovascular Diseases, 118(10), 554–562. https://doi.org/10.1016/j.acvd.2025.04.055
6. Wang, Y., Wang, C., & Wang, J. (2026). *Prediction Models for Progression From Prediabetes to Diabetes: A Systematic Review and Meta-analysis.* Frontiers in Endocrinology, 17, 1888466. https://doi.org/10.3389/fendo.2026.1888466
7. Barada, S., & Selvanambi, R. (2026). *Artificial Intelligence for Early Prediction of Gestational Diabetes Mellitus and Preeclampsia: A Systematic Review of Machine Learning Models and Clinical Decision Support Systems.* Frontiers in Artificial Intelligence, 9, 1890320. https://doi.org/10.3389/frai.2026.1890320
