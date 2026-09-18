from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AssessmentAnswers(BaseModel):
    """Structured health data collected by the assistant / assessment form.
    Only the fields relevant to the requested prediction need to be present;
    the predict endpoint validates per-model requirements at call time."""
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = Field(None, min_length=1, max_length=30)
    bmi: Optional[float] = Field(None, ge=10, le=100)
    height_cm: Optional[float] = Field(None, ge=50, le=250)
    weight_kg: Optional[float] = Field(None, ge=2, le=500)
    family_history: Optional[bool] = None
    physical_activity_hours: Optional[float] = Field(None, ge=0, le=168)
    smoking: Optional[bool] = None
    fasting_glucose_proxy: Optional[float] = Field(None, ge=20, le=800)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    systolic_bp: Optional[float] = Field(None, ge=50, le=300)
    heart_rate: Optional[float] = Field(None, ge=20, le=300)
    resting_heart_rate: Optional[float] = Field(None, ge=20, le=300)
    sodium_diet_level: Optional[int] = Field(None, ge=1, le=10)
    cholesterol_proxy: Optional[float] = Field(None, ge=50, le=1000)
    pregnancy_context: Optional[str] = None
    diabetes_flag: Optional[bool] = None
    symptoms: Optional[List[str]] = None
    symptom_duration: Optional[str] = Field(None, max_length=200)
    symptom_trend: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class AssessmentRequest(BaseModel):
    answers: AssessmentAnswers


class PredictRequest(BaseModel):
    answers: AssessmentAnswers
    diseases: Optional[List[str]] = None  # None = run all registered models


class PredictionResult(BaseModel):
    condition: str
    risk_level: str
    contributing_factors: List[str]
    algorithm_used: str
    probability_percent: Optional[float] = None
    input_coverage_percent: Optional[float] = None
    assumed_features: List[str] = Field(default_factory=list)


class UnavailablePrediction(BaseModel):
    condition: str
    status: str
    reason: str
    missing_inputs: List[str] = Field(default_factory=list)


class PredictionRecord(BaseModel):
    assessment_id: str
    user_id: str
    predicted_conditions: List[PredictionResult]
    unavailable_predictions: List[UnavailablePrediction] = Field(default_factory=list)
    overall_risk: str
    created_at: datetime


class MeasurementCreate(BaseModel):
    blood_pressure_systolic: Optional[float] = Field(None, ge=50, le=300)
    blood_pressure_diastolic: Optional[float] = Field(None, ge=30, le=200)
    heart_rate: Optional[float] = Field(None, ge=20, le=300)
    temperature: Optional[float] = Field(None, ge=30, le=45)
    weight_kg: Optional[float] = Field(None, ge=2, le=500)
    recorded_at: Optional[datetime] = None


class SymptomCheckInCreate(BaseModel):
    symptoms: List[str] = Field(default_factory=list, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)
    recorded_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
