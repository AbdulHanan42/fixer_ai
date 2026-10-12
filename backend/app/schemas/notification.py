from typing import List, Optional
from pydantic import BaseModel
from app.db.models import NotificationType


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    user_id: str
    type: NotificationType
    title: str
    content: str
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for paginated notification list response."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    skip: int
    limit: int


class UnreadCountResponse(BaseModel):
    """Schema for unread count response."""
    unread_count: int


class MarkReadResponse(BaseModel):
    """Schema for mark read response."""
    success: bool
    marked_count: int
