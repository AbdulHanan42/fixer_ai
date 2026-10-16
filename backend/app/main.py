from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import APP_NAME, CORS_ORIGINS
from app.api.v1 import auth, vehicles, mechanics, repairs, messages, notifications, reviews, admin
from app.api.endpoints import ai_diagnosis

app = FastAPI(title=APP_NAME, description="An AI-powered tool for fixing daily routine car problems.", version="1.0.0")
workshop_upload_dir = Path(__file__).resolve().parents[1] / "storage" / "workshops"
workshop_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/workshops", StaticFiles(directory=workshop_upload_dir), name="workshop-uploads")
app.add_middleware(
	CORSMiddleware,
	allow_origins=CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Include routers under /api/v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(vehicles.router, prefix="/api/v1")
app.include_router(mechanics.router, prefix="/api/v1")
app.include_router(repairs.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ai_diagnosis.router, prefix="/api")

# Also mount at root for convenient client access (/reviews, /admin)
app.include_router(reviews.router)
app.include_router(admin.router)

