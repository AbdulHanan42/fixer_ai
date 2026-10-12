import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import SessionLocal, get_db
from app.dependencies.auth import get_current_user
from app.repositories.user import UserRepository
from app.schemas.notification import (
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification import NotificationService
from app.websocket.connection_manager import manager

router = APIRouter(tags=["Notifications"])


# ---------------- REST Endpoints ----------------

@router.get(
    "/notifications",
    response_model=NotificationListResponse,
)
async def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
):
    """
    Get paginated notifications for the authenticated user.
    """
    return NotificationService.get_user_notifications(
        db=db,
        user_id=str(current_user.id),
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/notifications/unread-count",
    response_model=UnreadCountResponse,
)
async def get_unread_notification_count(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get total unread notification count for the authenticated user.
    """
    count = NotificationService.get_unread_count(db=db, user_id=str(current_user.id))
    return UnreadCountResponse(unread_count=count)


@router.put(
    "/notifications/read-all",
    response_model=MarkReadResponse,
)
async def mark_all_notifications_as_read(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Mark all unread notifications as read for the authenticated user.
    """
    count = NotificationService.mark_all_as_read(db=db, user_id=str(current_user.id))
    return MarkReadResponse(success=True, marked_count=count)


@router.put(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_notification_as_read(
    notification_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Mark an individual notification as read.
    """
    try:
        return NotificationService.mark_as_read(
            db=db,
            notification_id=notification_id,
            user_id=str(current_user.id),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ---------------- WebSocket Handler ----------------

async def _handle_notification_websocket(
    websocket: WebSocket,
    token: str | None = None,
):
    """Authenticate and manage a real-time notification WebSocket stream."""
    auth_token = token
    if not auth_token:
        header_auth = websocket.headers.get("Authorization") or websocket.headers.get("authorization")
        if header_auth and header_auth.startswith("Bearer "):
            auth_token = header_auth[7:].strip()

    if not auth_token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(auth_token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload.get("sub")
    db = SessionLocal()
    try:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await manager.connect_notifications(str(user.id), websocket)

        unread_count = NotificationService.get_unread_count(db, str(user.id))
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "user_id": str(user.id),
                "unread_count": unread_count,
            })
        )

        while True:
            raw_text = await websocket.receive_text()
            try:
                msg_json = json.loads(raw_text)
            except json.JSONDecodeError:
                continue

            if msg_json.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await manager.disconnect_notifications(str(user_id), websocket)
        db.close()


@router.websocket("/notifications/ws")
async def notifications_websocket(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    """WebSocket endpoint for receiving real-time personal notifications."""
    await _handle_notification_websocket(websocket, token)


@router.websocket("/ws/notifications")
async def notifications_websocket_alias(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    """Alias WebSocket endpoint for receiving real-time personal notifications."""
    await _handle_notification_websocket(websocket, token)
