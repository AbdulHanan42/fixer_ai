from typing import Optional, List
from pydantic import BaseModel, Field


class MechanicProfileCreate(BaseModel):
    """Schema for creating a mechanic profile."""
    shop_name: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class MechanicProfileUpdate(BaseModel):
    """Schema for updating a mechanic profile."""
    shop_name: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class MechanicProfileResponse(BaseModel):
    """Schema for mechanic profile response."""
    id: str
    user_id: str
    shop_name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_verified: bool
    average_rating: float

    class Config:
        from_attributes = True


class MechanicProfileWithServices(MechanicProfileResponse):
    """Schema for mechanic profile with services."""
    services: List[dict] = []
