from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, CORS_ORIGINS

app = FastAPI(title=APP_NAME, description="An AI-powered tool for fixing daily routine car problems.", version="1.0.0")
app.add_middleware(
	CORSMiddleware,
	allow_origins=CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)
