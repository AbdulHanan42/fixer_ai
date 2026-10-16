import asyncio

from sqlalchemy.orm import Session

from app.db.models import Notification, NotificationType, RepairRequest
from app.repositories.mechanic import MechanicRepository
from app.repositories.notification import NotificationRepository
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)
from app.websocket.connection_manager import manager


class NotificationService:
    """Service for notification business logic and real-time dispatch."""

    @staticmethod
    def _to_response(notification: Notification) -> NotificationResponse:
        """Convert Notification ORM instance to Pydantic schema."""
        return NotificationResponse(
            id=str(notification.id),
            user_id=str(notification.user_id),
            type=notification.type,
            title=notification.title,
            content=notification.content,
            reference_id=str(notification.reference_id) if notification.reference_id else None,
            reference_type=notification.reference_type,
            is_read=notification.is_read,
            created_at=notification.created_at.isoformat() if notification.created_at else "",
        )

    @staticmethod
    def _send_realtime(user_id: str, response: NotificationResponse) -> None:
        """Send notification over WebSocket if an event loop is active."""
        try:
            loop = asyncio.get_running_loop()
            payload = {
                "type": "notification",
                "data": response.model_dump(),
            }
            loop.create_task(manager.send_notification_to_user(user_id, payload))
        except RuntimeError:
            # No running event loop in this context (e.g. background thread or script)
            pass

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        type: NotificationType,
        title: str,
        content: str,
        reference_id: str | None = None,
        reference_type: str | None = None,
    ) -> NotificationResponse:
        """Persist a notification in PostgreSQL and attempt real-time WebSocket delivery."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )
        created = NotificationRepository.create(db, notification)
        response = NotificationService._to_response(created)
        NotificationService._send_realtime(user_id, response)
        return response

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> NotificationListResponse:
        """Retrieve paginated notifications for the authenticated user."""
        items = NotificationRepository.get_by_user(
            db, user_id, unread_only=unread_only, skip=skip, limit=limit
        )
        total = NotificationRepository.count_by_user(db, user_id, unread_only=unread_only)
        unread_count = NotificationRepository.count_unread_by_user(db, user_id)

        return NotificationListResponse(
            notifications=[NotificationService._to_response(n) for n in items],
            total=total,
            unread_count=unread_count,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        """Get the count of unread notifications for a user."""
        return NotificationRepository.count_unread_by_user(db, user_id)

    @staticmethod
    def mark_as_read(
        db: Session, notification_id: str, user_id: str
    ) -> NotificationResponse:
        """Mark a notification as read."""
        notification = NotificationRepository.mark_as_read(db, notification_id, user_id)
        if not notification:
            raise ValueError("Notification not found or access denied")
        return NotificationService._to_response(notification)

    @staticmethod
    def mark_all_as_read(db: Session, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        return NotificationRepository.mark_all_as_read(db, user_id)

    # ---------------- Event-driven Helpers ----------------

    @staticmethod
    def notify_new_repair_request(db: Session, request: RepairRequest) -> None:
        """Notify relevant mechanics about a new pending repair request."""
        # Find mechanics nearby or all registered mechanics
        mechanics = []
        try:
            # Query all mechanic profiles to notify
            mechanics = [
                mechanic
                for mechanic in MechanicRepository.get_all(db, skip=0, limit=100)
                if mechanic.is_online
            ]
        except Exception:
            pass

        req_id_short = str(request.id)[:8]
        desc_snippet = request.description[:60] + "..." if len(request.description) > 60 else request.description

        for mechanic in mechanics:
            NotificationService.create_notification(
                db=db,
                user_id=str(mechanic.user_id),
                type=NotificationType.new_repair_request,
                title="New Repair Request Available",
                content=f"Request #{req_id_short}: {desc_snippet}",
                reference_id=str(request.id),
                reference_type="repair_request",
            )

    @staticmethod
    def notify_request_accepted(
        db: Session, request: RepairRequest, shop_name: str
    ) -> None:
        """Notify the customer that their repair request has been accepted."""
        req_id_short = str(request.id)[:8]
        NotificationService.create_notification(
            db=db,
            user_id=str(request.customer_id),
            type=NotificationType.request_accepted,
            title="Repair Request Accepted",
            content=f"Your repair request #{req_id_short} was accepted by {shop_name}.",
            reference_id=str(request.id),
            reference_type="repair_request",
        )

    @staticmethod
    def notify_request_rejected(db: Session, request: RepairRequest) -> None:
        """Notify the customer that their repair request was cancelled or rejected."""
        req_id_short = str(request.id)[:8]
        NotificationService.create_notification(
            db=db,
            user_id=str(request.customer_id),
            type=NotificationType.request_rejected,
            title="Repair Request Cancelled",
            content=f"Repair request #{req_id_short} has been cancelled.",
            reference_id=str(request.id),
            reference_type="repair_request",
        )

    @staticmethod
    def notify_repair_completed(db: Session, request: RepairRequest) -> None:
        """Notify the customer that their vehicle repair is completed."""
        req_id_short = str(request.id)[:8]
        NotificationService.create_notification(
            db=db,
            user_id=str(request.customer_id),
            type=NotificationType.repair_completed,
            title="Repair Completed",
            content=f"Your repair request #{req_id_short} has been completed! Please check your vehicle.",
            reference_id=str(request.id),
            reference_type="repair_request",
        )

    @staticmethod
    def notify_status_changed(
        db: Session, request: RepairRequest, old_status: str, new_status: str
    ) -> None:
        """Notify customer of a general status update on their repair request."""
        req_id_short = str(request.id)[:8]
        NotificationService.create_notification(
            db=db,
            user_id=str(request.customer_id),
            type=NotificationType.status_changed,
            title="Repair Status Updated",
            content=f"Status for repair #{req_id_short} changed to {new_status}.",
            reference_id=str(request.id),
            reference_type="repair_request",
        )

    @staticmethod
    def notify_new_message(
        db: Session,
        request_id: str,
        sender_name: str,
        recipient_id: str,
        content: str,
    ) -> None:
        """Notify message recipient of a new message."""
        snippet = content[:60] + "..." if len(content) > 60 else content
        NotificationService.create_notification(
            db=db,
            user_id=recipient_id,
            type=NotificationType.new_message,
            title=f"New Message from {sender_name}",
            content=snippet,
            reference_id=request_id,
            reference_type="repair_request",
        )
