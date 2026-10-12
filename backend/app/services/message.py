import asyncio

from sqlalchemy.orm import Session

from app.db.models import Message, RepairRequest, User
from app.repositories.mechanic import MechanicRepository
from app.repositories.message import MessageRepository
from app.repositories.repair import RepairRequestRepository
from app.schemas.message import MessageHistoryResponse, MessageResponse
from app.services.notification import NotificationService
from app.websocket.connection_manager import manager


class MessageService:
    """Service for repair request chat messages."""

    @staticmethod
    def _to_response(message: Message, sender: User) -> MessageResponse:
        """Convert Message ORM model to response schema."""
        return MessageResponse(
            id=str(message.id),
            request_id=str(message.request_id),
            sender_id=str(message.sender_id),
            sender_name=sender.full_name if sender else None,
            sender_role=sender.role.value if sender and hasattr(sender.role, "value") else str(sender.role) if sender else None,
            content=message.content,
            sent_at=message.sent_at.isoformat() if message.sent_at else "",
        )

    @staticmethod
    def _broadcast_message(request_id: str, response: MessageResponse) -> None:
        """Broadcast message payload to the repair request WebSocket room."""
        try:
            loop = asyncio.get_running_loop()
            payload = {
                "type": "message",
                "data": response.model_dump(),
            }
            loop.create_task(manager.broadcast_to_repair_room(request_id, payload))
        except RuntimeError:
            pass

    @staticmethod
    def validate_conversation_access(
        db: Session, request_id: str, user: User
    ) -> tuple[RepairRequest, str]:
        """
        Validate that the repair request exists and the user is either
        the customer or the assigned mechanic.

        Returns:
            Tuple of (RepairRequest, role_str)
        """
        request = RepairRequestRepository.get_by_id(db, request_id)
        if not request:
            raise ValueError("Repair request not found")

        # Check if customer
        if str(request.customer_id) == str(user.id):
            return request, "customer"

        # Check if assigned mechanic
        if request.mechanic_id:
            profile = MechanicRepository.get_by_user_id(db, str(user.id))
            if profile and str(profile.id) == str(request.mechanic_id):
                return request, "mechanic"

        raise PermissionError("Access denied: You are not a participant in this repair request")

    @staticmethod
    def send_message(
        db: Session, request_id: str, sender: User, content: str
    ) -> MessageResponse:
        """
        Validate, persist, broadcast, and notify for a new message.
        """
        # Validate participation
        request, sender_role = MessageService.validate_conversation_access(db, request_id, sender)

        # Messaging requires an assigned mechanic
        if not request.mechanic_id:
            raise ValueError("Cannot send messages on a repair request without an assigned mechanic")

        stripped_content = content.strip()
        if not stripped_content:
            raise ValueError("Message content cannot be empty")
        if len(stripped_content) > 2000:
            raise ValueError("Message content cannot exceed 2000 characters")

        # Determine recipient
        if sender_role == "customer":
            recipient_id = str(request.mechanic.user_id)
        else:
            recipient_id = str(request.customer_id)

        # Persist message
        message = Message(
            request_id=request.id,
            sender_id=sender.id,
            content=stripped_content,
        )
        created = MessageRepository.create(db, message)
        response = MessageService._to_response(created, sender)

        # Real-time room broadcast
        MessageService._broadcast_message(str(request.id), response)

        # Persistent & real-time notification to recipient
        NotificationService.notify_new_message(
            db=db,
            request_id=str(request.id),
            sender_name=sender.full_name,
            recipient_id=recipient_id,
            content=stripped_content,
        )

        return response

    @staticmethod
    def get_message_history(
        db: Session, request_id: str, user: User, skip: int = 0, limit: int = 50
    ) -> MessageHistoryResponse:
        """
        Retrieve paginated chat message history for authorized participants.
        """
        # Authorization check
        MessageService.validate_conversation_access(db, request_id, user)

        messages = MessageRepository.get_by_request_id(db, request_id, skip=skip, limit=limit)
        total = MessageRepository.count_by_request_id(db, request_id)

        response_items = []
        for m in messages:
            sender = m.sender
            response_items.append(
                MessageResponse(
                    id=str(m.id),
                    request_id=str(m.request_id),
                    sender_id=str(m.sender_id),
                    sender_name=sender.full_name if sender else None,
                    sender_role=sender.role.value if sender and hasattr(sender.role, "value") else str(sender.role) if sender else None,
                    content=m.content,
                    sent_at=m.sent_at.isoformat() if m.sent_at else "",
                )
            )

        return MessageHistoryResponse(
            messages=response_items,
            total=total,
            skip=skip,
            limit=limit,
        )
