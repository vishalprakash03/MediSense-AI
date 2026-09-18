from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.database.db import ensure_indexes
from backend.routes import auth, user, health, assistant


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    yield


app = FastAPI(
    title="MediSense AI API",
    description="Intelligent healthcare prediction and personalized health assistant backend.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(health.router)
app.include_router(assistant.router)


@app.get("/")
async def root():
    return {
        "service": "MediSense AI API",
        "status": "running",
        "disclaimer": (
            "MediSense AI provides preliminary health-risk information and is "
            "not a substitute for professional medical advice."
        ),
    }


@app.get("/health-check")
async def health_check():
    return {"status": "ok"}
