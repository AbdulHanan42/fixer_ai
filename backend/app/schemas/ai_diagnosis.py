from typing import Literal, Optional

from pydantic import BaseModel, Field


class DiagnosisAnalysis(BaseModel):
    possible_issues: list[str] = Field(min_length=1, max_length=8)
    urgency: Literal["High", "Medium", "Low"]
    target_service_category: str = Field(min_length=1, max_length=50)


class AIDiagnosisResult(BaseModel):
    user_description: str
    possible_issues: list[str]
    urgency: Literal["High", "Medium", "Low"]
    target_service_category: str


class RecommendedMechanic(BaseModel):
    id: str
    name: str
    shop_name: str
    address: str
    city: Optional[str] = None
    rating: float
    distance_km: Optional[float] = None


class DiagnosisAnalyzeResponse(BaseModel):
    ai_diagnosis_results: AIDiagnosisResult
    recommended_mechanics: list[RecommendedMechanic]
