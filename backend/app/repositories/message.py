
from sqlalchemy.orm import Session, joinedload

from app.db.models import Message


class MessageRepository:
    """Repository for Message database operations."""

    @staticmethod
    def create(db: Session, message: Message) -> Message:
        """Create and persist a new message."""
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_by_id(db: Session, message_id: str) -> Message | None:
        """Get a message by its UUID."""
        return (
            db.query(Message)
            .options(joinedload(Message.sender))
            .filter(Message.id == message_id)
            .first()
        )

    @staticmethod
    def get_by_request_id(
        db: Session,
        request_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Message]:
        """Get paginated messages for a repair request, ordered chronologically."""
        return (
            db.query(Message)
            .options(joinedload(Message.sender))
            .filter(Message.request_id == request_id)
            .order_by(Message.sent_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_by_request_id(db: Session, request_id: str) -> int:
        """Count total messages for a repair request."""
        return db.query(Message).filter(Message.request_id == request_id).count()
