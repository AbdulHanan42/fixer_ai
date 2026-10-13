from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, CORS_ORIGINS
from app.api.v1 import auth, vehicles, mechanics, repairs, messages, notifications, reviews, admin
from app.api.endpoints import ai_diagnosis

app = FastAPI(title=APP_NAME, description="An AI-powered tool for fixing daily routine car problems.", version="1.0.0")
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

