import base64
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError
from sqlalchemy.orm import Session, joinedload

from app.core.config import OPENAI_API_KEY, OPENAI_VISION_MODEL
from app.db.models import MechanicProfile, MechanicService, Service, User
from app.db.session import get_db
from app.dependencies.auth import get_current_customer
from app.schemas.ai_diagnosis import (
    AIDiagnosisResult,
    DiagnosisAnalysis,
    DiagnosisAnalyzeResponse,
)

router = APIRouter(prefix="/diagnosis", tags=["AI Diagnosis"])
logger = logging.getLogger(__name__)
MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


async def _analyze_image(
    image_bytes: bytes,
    media_type: str,
    description: str,
    service_categories: list[str],
) -> DiagnosisAnalysis:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI diagnosis is not configured. Set OPENAI_API_KEY.",
        )

    prompt = (
        "Analyze the vehicle image and customer description for possible automotive issues. "
        "Return only a JSON object with possible_issues (a list of concise strings), urgency "
        "(exactly High, Medium, or Low), and target_service_category (exactly one category "
        "from the supplied list, preserving its spelling and capitalization). Do not invent a "
        "service category. Treat this as a preliminary assessment, not a definitive diagnosis.\n\n"
        f"Available service categories: {json.dumps(service_categories)}\n"
        f"Customer description: {description}"
    )
    image_data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        response = await client.chat.completions.create(
            model=OPENAI_VISION_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You provide cautious automotive triage and follow the requested JSON format exactly.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url, "detail": "high"},
                        },
                    ],
                },
            ],
        )
    finally:
        await client.close()

    content = response.choices[0].message.content
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider returned an empty diagnosis.",
        )

    try:
        analysis = DiagnosisAnalysis.model_validate_json(content)
    except (ValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider returned an invalid diagnosis format.",
        ) from exc

    if analysis.target_service_category not in service_categories:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider returned a service category outside the service catalog.",
        )
    return analysis


@router.post("/analyze", response_model=DiagnosisAnalyzeResponse)
async def analyze_repair_issue(
    image: Annotated[UploadFile, File()],
    description: Annotated[str, Form(min_length=10, max_length=2000)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_customer)],
) -> DiagnosisAnalyzeResponse:
    media_type = (image.content_type or "").lower()
    if media_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a JPEG, PNG, WebP, or GIF image.",
        )

    image_bytes = await image.read(MAX_IMAGE_SIZE + 1)
    if not image_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image must be 10 MB or smaller.")

    service_categories = [
        category
        for (category,) in db.query(Service.category).distinct().order_by(Service.category).all()
        if category
    ]
    if not service_categories:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The service catalog is empty, so AI recommendations are unavailable.",
        )

    try:
        analysis = await _analyze_image(image_bytes, media_type, description, service_categories)
    except OpenAIError as exc:
        logger.error(
            "OpenAI diagnosis request failed (status=%s): %s",
            getattr(exc, "status_code", "unknown"),
            getattr(exc, "message", str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI diagnosis provider is temporarily unavailable.",
        ) from exc

    mechanics = (
        db.query(MechanicProfile)
        .join(MechanicProfile.mechanic_services)
        .join(MechanicService.service)
        .options(joinedload(MechanicProfile.user))
        .filter(
            MechanicProfile.is_verified.is_(True),
            Service.category == analysis.target_service_category,
        )
        .order_by(MechanicProfile.average_rating.desc(), MechanicProfile.shop_name.asc())
        .distinct()
        .all()
    )

    return DiagnosisAnalyzeResponse(
        ai_diagnosis_results=AIDiagnosisResult(
            user_description=description,
            possible_issues=analysis.possible_issues,
            urgency=analysis.urgency,
            target_service_category=analysis.target_service_category,
        ),
        recommended_mechanics=[
            {
                "id": str(mechanic.id),
                "name": mechanic.user.full_name,
                "shop_name": mechanic.shop_name,
                "address": mechanic.address,
                "city": mechanic.city,
                "rating": mechanic.average_rating,
                "distance_km": None,
            }
            for mechanic in mechanics
        ],
    )
