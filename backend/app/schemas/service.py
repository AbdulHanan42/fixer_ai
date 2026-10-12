from typing import Optional
from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    """Schema for creating a service (admin only)."""
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=50)


class ServiceUpdate(BaseModel):
    """Schema for updating a service (admin only)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    category: Optional[str] = Field(None, min_length=2, max_length=50)


class ServiceResponse(BaseModel):
    """Schema for service response."""
    id: str
    name: str
    category: str

    class Config:
        from_attributes = True


class MechanicServiceCreate(BaseModel):
    """Schema for adding a service to a mechanic's profile."""
    service_id: str
    base_price: float = Field(..., gt=0)


class MechanicServiceUpdate(BaseModel):
    """Schema for updating a mechanic's service price."""
    base_price: float = Field(..., gt=0)


class MechanicServiceResponse(BaseModel):
    """Schema for mechanic service response."""
    id: str
    mechanic_id: str
    service_id: str
    base_price: float
    service_name: Optional[str] = None
    service_category: Optional[str] = None

    class Config:
        from_attributes = True
