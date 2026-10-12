
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    """Schema for submitting a repair review and rating."""
    request_id: str = Field(..., description="Completed repair request ID")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str = Field(..., min_length=1, max_length=1000, description="Review feedback comment")


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: str
    request_id: str
    customer_id: str
    mechanic_id: str
    rating: int
    comment: str
    mechanic_average_rating: float | None = None

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Schema for list of reviews."""
    reviews: list[ReviewResponse]
    total: int
    average_rating: float
