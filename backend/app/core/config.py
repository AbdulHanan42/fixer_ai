import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

APP_NAME = os.getenv("APP_NAME", "Fixer AI")
CORS_ORIGINS = [
	origin.strip()
	for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
	if origin.strip()
]
