from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.models import RequestStatus


class RepairRequestCreate(BaseModel):
    """Schema for creating a repair request."""
    vehicle_id: Optional[str] = None
    mechanic_id: Optional[str] = None
    description: str = Field(..., min_length=10, max_length=2000)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class RepairRequestUpdate(BaseModel):
    """Schema for updating a repair request (mechanic only)."""
    status: RequestStatus


class RepairRequestResponse(BaseModel):
    """Schema for repair request response."""
    id: str
    customer_id: str
    vehicle_id: Optional[str] = None
    mechanic_id: Optional[str] = None
    status: RequestStatus
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AIDiagnosisResponse(BaseModel):
    """Schema for AI diagnosis response."""
    id: str
    request_id: str
    possible_faults: Optional[dict] = None
    urgency: str
    ai_summary: str

    class Config:
        from_attributes = True


class RequestImageResponse(BaseModel):
    """Schema for request image response."""
    id: str
    request_id: str
    image_url: str

    class Config:
        from_attributes = True


class RepairRequestWithDetails(RepairRequestResponse):
    """Schema for repair request with additional details."""
    vehicle_info: Optional[dict] = None
    mechanic_info: Optional[dict] = None
    ai_diagnosis: Optional[AIDiagnosisResponse] = None
    images: List[RequestImageResponse] = []
