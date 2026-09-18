import uuid
from datetime import datetime
from fastapi import APIRouter, Depends

from backend.database.db import conversations_collection
from backend.schemas.health import ChatMessage
from backend.services.security import get_current_user_id
from backend.services.assistant_service import process_turn

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat")
async def chat(payload: ChatMessage, user_id: str = Depends(get_current_user_id)):
    session_id = payload.session_id or str(uuid.uuid4())

    convo = await conversations_collection.find_one({"user_id": user_id, "session_id": session_id})
    state = (convo or {}).get("state", {"answers": {}, "awaiting_key": None, "started": False})
    messages = (convo or {}).get("messages", [])

    reply, new_state, is_complete = process_turn(state, payload.message)

    messages.append({"role": "user", "text": payload.message, "at": datetime.utcnow()})
    messages.append({"role": "assistant", "text": reply, "at": datetime.utcnow()})

    await conversations_collection.update_one(
        {"user_id": user_id, "session_id": session_id},
        {"$set": {
            "user_id": user_id,
            "session_id": session_id,
            "state": new_state,
            "messages": messages,
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )

    return {
        "session_id": session_id,
        "reply": reply,
        "is_complete": is_complete,
        "collected_answers": new_state.get("answers", {}) if is_complete else None,
    }
