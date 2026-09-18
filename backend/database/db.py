from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.db_name]

users_collection = db["users"]
health_profiles_collection = db["health_profiles"]
measurements_collection = db["health_measurements"]
predictions_collection = db["predictions"]
conversations_collection = db["conversations"]
symptom_checkins_collection = db["symptom_checkins"]


async def ensure_indexes():
    await users_collection.create_index("email", unique=True)
    await measurements_collection.create_index("user_id")
    await predictions_collection.create_index("user_id")
    await conversations_collection.create_index("user_id")
    await symptom_checkins_collection.create_index("user_id")
