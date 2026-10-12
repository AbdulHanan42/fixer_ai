from typing import List, Optional
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for sending a new message."""
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    request_id: str
    sender_id: str
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    content: str
    sent_at: str

    class Config:
        from_attributes = True


class MessageHistoryResponse(BaseModel):
    """Schema for paginated message history response."""
    messages: List[MessageResponse]
    total: int
    skip: int
    limit: int
