from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=120)
    gender: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    medical_history: Optional[list] = None
    family_history: Optional[list] = None
    lifestyle: Optional[dict] = None
    smoking_status: Optional[str] = None
    physical_activity_hours: Optional[float] = None
    sleep_hours: Optional[float] = None
    dietary_habits: Optional[str] = None
    stress_level: Optional[int] = Field(None, ge=1, le=10)


class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    age: int
    gender: str
    created_at: datetime
    profile: Optional[dict] = None
