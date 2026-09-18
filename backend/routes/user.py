from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from backend.database.db import (
    users_collection,
    health_profiles_collection,
    measurements_collection,
    predictions_collection,
    conversations_collection,
    symptom_checkins_collection,
)
from backend.schemas.user import UserProfileUpdate
from backend.services.security import get_current_user_id

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
async def get_profile(user_id: str = Depends(get_current_user_id)):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    profile = await health_profiles_collection.find_one({"user_id": user_id})

    return {
        "user_id": user_id,
        "name": user["name"],
        "email": user["email"],
        "age": user["age"],
        "gender": user["gender"],
        "created_at": user["created_at"],
        "profile": _strip_id(profile) or {},
    }


@router.put("/profile")
async def update_profile(payload: UserProfileUpdate, user_id: str = Depends(get_current_user_id)):
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    await health_profiles_collection.update_one(
        {"user_id": user_id},
        {"$set": {**updates, "user_id": user_id}},
        upsert=True,
    )
    profile = await health_profiles_collection.find_one({"user_id": user_id})
    return {"message": "Profile updated.", "profile": _strip_id(profile)}


@router.delete("/account")
async def delete_account(user_id: str = Depends(get_current_user_id)):
    """Delete all user-owned account and health data from the application."""
    await health_profiles_collection.delete_many({"user_id": user_id})
    await measurements_collection.delete_many({"user_id": user_id})
    await predictions_collection.delete_many({"user_id": user_id})
    await conversations_collection.delete_many({"user_id": user_id})
    await symptom_checkins_collection.delete_many({"user_id": user_id})
    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "Your account and stored health data were deleted."}


def _strip_id(doc):
    if not doc:
        return doc
    doc = dict(doc)
    doc.pop("_id", None)
    return doc
