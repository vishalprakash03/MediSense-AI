from fastapi import APIRouter, HTTPException, Request, Response, status
from datetime import datetime
from bson import ObjectId

from backend.database.db import users_collection
from backend.schemas.user import RegisterRequest, LoginRequest, TokenResponse
from backend.services.security import hash_password, verify_password, create_access_token
from backend.services.rate_limit import login_rate_limiter
from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def _login_rate_limit_key(request: Request, email: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{email.lower()}"


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, response: Response):
    existing = await users_collection.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "age": payload.age,
        "gender": payload.gender,
        "created_at": datetime.utcnow(),
    }
    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    token = create_access_token(user_id)
    _set_session_cookie(response, token)

    return TokenResponse(
        access_token=token,
        user={"user_id": user_id, "name": payload.name, "email": payload.email},
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response):
    rate_limit_key = _login_rate_limit_key(request, payload.email)
    await login_rate_limiter.check(rate_limit_key)
    user = await users_collection.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        await login_rate_limiter.record_failure(rate_limit_key)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user_id = str(user["_id"])
    token = create_access_token(user_id)
    await login_rate_limiter.reset(rate_limit_key)
    _set_session_cookie(response, token)

    return TokenResponse(
        access_token=token,
        user={"user_id": user_id, "name": user["name"], "email": user["email"]},
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key=settings.session_cookie_name, path="/")
