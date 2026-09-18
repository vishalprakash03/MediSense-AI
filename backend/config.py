import os
from pydantic_settings import BaseSettings

DEFAULT_JWT_SECRET = "dev-only-change-me-in-production"


class Settings(BaseSettings):
    environment: str = os.getenv("APP_ENV", "development")
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name: str = os.getenv("DB_NAME", "medisense")
    jwt_secret: str = os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    cors_origins: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    session_cookie_name: str = "medisense_access_token"
    cookie_secure: bool = (
        os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
        or os.getenv("APP_ENV", "development").lower() == "production"
    )

    class Config:
        env_file = ".env"


settings = Settings()

if settings.environment.lower() == "production" and settings.jwt_secret == DEFAULT_JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be configured when APP_ENV=production.")
