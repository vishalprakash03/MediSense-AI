import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from backend.database.db import (
    health_profiles_collection,
    measurements_collection,
    predictions_collection,
    symptom_checkins_collection,
    users_collection,
)
from backend.schemas.health import (
    AssessmentRequest,
    PredictRequest,
    MeasurementCreate,
    SymptomCheckInCreate,
)
from backend.services.security import get_current_user_id
from backend.services.ml_service import run_predictions
from backend.services.recommendation_service import build_recommendations
from backend.services.symptom_service import build_symptom_alerts

router = APIRouter(prefix="/api/health", tags=["health"])


def _strip_id(doc):
    if not doc:
        return doc
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc


@router.post("/assessment")
async def submit_assessment(payload: AssessmentRequest, user_id: str = Depends(get_current_user_id)):
    """Stores a raw set of assessment answers without running prediction yet
    (used if the frontend wants to save-then-predict as separate steps)."""
    assessment_id = str(uuid.uuid4())
    doc = {
        "assessment_id": assessment_id,
        "user_id": user_id,
        "answers": payload.answers.dict(exclude_none=True),
        "created_at": datetime.utcnow(),
    }
    await predictions_collection.insert_one({**doc, "predicted_conditions": [], "overall_risk": "Unassessed"})
    return {"assessment_id": assessment_id, "message": "Assessment saved."}


@router.post("/predict")
async def predict(payload: PredictRequest, user_id: str = Depends(get_current_user_id)):
    profile_doc = await health_profiles_collection.find_one({"user_id": user_id}) or {}
    profile_doc.pop("_id", None)
    account_doc = await users_collection.find_one({"_id": ObjectId(user_id)}) or {}
    # Account age and gender are captured during registration, while the health
    # profile stores optional measurements and lifestyle details. Supply both
    # to the feature mapper so a prediction does not default sex or age when
    # the assessment itself omits them.
    profile = {
        "age": account_doc.get("age"),
        "gender": account_doc.get("gender"),
        **profile_doc,
    }

    try:
        prediction = run_predictions(
            answers=payload.answers.dict(exclude_none=True),
            profile=profile,
            diseases=payload.diseases,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not prediction["predicted_conditions"] and not prediction["unavailable_predictions"]:
        raise HTTPException(
            status_code=503,
            detail="No trained models are available yet. Run ml/training/train_models.py.",
        )

    assessment_id = str(uuid.uuid4())
    record = {
        "assessment_id": assessment_id,
        "user_id": user_id,
        "answers": payload.answers.dict(exclude_none=True),
        "predicted_conditions": prediction["predicted_conditions"],
        "unavailable_predictions": prediction["unavailable_predictions"],
        "overall_risk": prediction["overall_risk"],
        "recommendations": build_recommendations(
            payload.answers.dict(exclude_none=True),
            prediction["overall_risk"],
            prediction["predicted_conditions"],
        ),
        "created_at": datetime.utcnow(),
    }
    await predictions_collection.insert_one(record)

    return {
        "assessment_id": assessment_id,
        "overall_risk": prediction["overall_risk"],
        "predicted_conditions": prediction["predicted_conditions"],
        "unavailable_predictions": prediction["unavailable_predictions"],
        "recommendations": record["recommendations"],
        "disclaimer": (
            "MediSense AI provides preliminary health-risk information based on the "
            "data provided by the user. It is not a medical diagnosis and does not "
            "replace professional medical advice. Please consult a qualified "
            "healthcare professional for diagnosis and treatment."
        ),
    }


@router.get("/history")
async def get_history(user_id: str = Depends(get_current_user_id)):
    cursor = predictions_collection.find({"user_id": user_id}).sort("created_at", -1)
    results = [_strip_id(doc) async for doc in cursor]
    return {"history": results}


@router.get("/latest")
async def get_latest(user_id: str = Depends(get_current_user_id)):
    doc = await predictions_collection.find_one(
        {"user_id": user_id}, sort=[("created_at", -1)]
    )
    if not doc:
        return {"latest": None}
    return {"latest": _strip_id(doc)}


@router.post("/measurements")
async def add_measurement(payload: MeasurementCreate, user_id: str = Depends(get_current_user_id)):
    doc = payload.dict(exclude_none=True)
    doc["user_id"] = user_id
    doc["recorded_at"] = doc.get("recorded_at") or datetime.utcnow()
    result = await measurements_collection.insert_one(doc)
    return {"message": "Measurement recorded.", "id": str(result.inserted_id)}


@router.get("/measurements")
async def list_measurements(user_id: str = Depends(get_current_user_id)):
    cursor = measurements_collection.find({"user_id": user_id}).sort("recorded_at", 1)
    results = [_strip_id(doc) async for doc in cursor]
    return {"measurements": results}


@router.post("/symptoms")
async def add_symptom_checkin(
    payload: SymptomCheckInCreate,
    user_id: str = Depends(get_current_user_id),
):
    doc = payload.dict(exclude_none=True)
    doc["user_id"] = user_id
    doc["recorded_at"] = doc.get("recorded_at") or datetime.utcnow()
    result = await symptom_checkins_collection.insert_one(doc)
    return {"message": "Symptom check-in saved.", "id": str(result.inserted_id)}


@router.get("/symptoms")
async def list_symptom_checkins(user_id: str = Depends(get_current_user_id)):
    """Return the latest 90 check-ins and non-diagnostic pattern notices."""
    cursor = symptom_checkins_collection.find({"user_id": user_id}).sort("recorded_at", -1).limit(90)
    checkins = [_strip_id(doc) async for doc in cursor]
    checkins.reverse()
    return {"checkins": checkins, "alerts": build_symptom_alerts(checkins)}


@router.get("/symptoms/latest")
async def get_latest_symptom_checkin(user_id: str = Depends(get_current_user_id)):
    doc = await symptom_checkins_collection.find_one(
        {"user_id": user_id}, sort=[("recorded_at", -1)]
    )
    return {"latest": _strip_id(doc) if doc else None}
