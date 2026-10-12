from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class VehicleCreate(BaseModel):
    """Schema for creating a vehicle."""
    make: str = Field(..., min_length=2, max_length=50)
    model: str = Field(..., min_length=2, max_length=50)
    year: int = Field(..., ge=1900, le=2100)


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    make: Optional[str] = Field(None, min_length=2, max_length=50)
    model: Optional[str] = Field(None, min_length=2, max_length=50)
    year: Optional[int] = Field(None, ge=1900, le=2100)


class VehicleResponse(BaseModel):
    """Schema for vehicle response."""
    id: str
    customer_id: str
    make: str
    model: str
    year: int

    class Config:
        from_attributes = True
