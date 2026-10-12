from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, CORS_ORIGINS
from app.api.v1 import auth

app = FastAPI(title=APP_NAME, description="An AI-powered tool for fixing daily routine car problems.", version="1.0.0")
app.add_middleware(
	CORSMiddleware,
	allow_origins=CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
