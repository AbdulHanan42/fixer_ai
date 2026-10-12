
from pydantic import BaseModel


class PendingMechanicResponse(BaseModel):
    """Schema for a mechanic awaiting verification by admin."""
    id: str
    user_id: str
    shop_name: str
    address: str
    is_verified: bool
    average_rating: float
    mechanic_name: str | None = None
    mechanic_email: str | None = None
    mechanic_phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    class Config:
        from_attributes = True


class VerifyMechanicResponse(BaseModel):
    """Schema for mechanic verification response."""
    mechanic_id: str
    shop_name: str
    is_verified: bool
    message: str
