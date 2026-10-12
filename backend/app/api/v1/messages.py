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
from app.schemas.message import (
    MessageCreate,
    MessageHistoryResponse,
    MessageResponse,
)
from app.services.message import MessageService
from app.websocket.connection_manager import manager

router = APIRouter(tags=["Messaging"])


# ---------------- REST Endpoints ----------------

@router.post(
    "/repairs/{request_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_repair_message(
    request_id: str,
    message_data: MessageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Send a message within an assigned repair request conversation.
    - Sender must be either the customer or the assigned mechanic.
    - Requires an assigned mechanic on the repair request.
    - Rate limited to prevent spam.
    """
    # Rate limit check
    if not await manager.rate_limiter.is_allowed(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a moment before sending more messages.",
        )

    try:
        return MessageService.send_message(
            db=db,
            request_id=request_id,
            sender=current_user,
            content=message_data.content,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        error_msg = str(e)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in error_msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=error_msg)


@router.get(
    "/repairs/{request_id}/messages",
    response_model=MessageHistoryResponse,
)
async def get_repair_messages(
    request_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max records to return"),
):
    """
    Get paginated message history for a repair request conversation.
    - Accessible only by the repair customer or assigned mechanic.
    """
    try:
        return MessageService.get_message_history(
            db=db,
            request_id=request_id,
            user=current_user,
            skip=skip,
            limit=limit,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ---------------- WebSocket Handler ----------------

async def _handle_chat_websocket(
    websocket: WebSocket,
    request_id: str,
    token: str | None = None,
):
    """Authenticate, authorize, and manage a WebSocket chat connection."""
    # Extract token from query or Authorization header
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

        # Validate authorization for this repair request
        try:
            _request, role = MessageService.validate_conversation_access(db, request_id, user)
        except (ValueError, PermissionError):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await manager.connect_repair_room(request_id, websocket, str(user.id))

        # Initial handshake frame
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "request_id": request_id,
                "user_id": str(user.id),
                "role": role,
            })
        )

        while True:
            raw_text = await websocket.receive_text()
            try:
                msg_json = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": "Invalid JSON format"})
                )
                continue

            msg_type = msg_json.get("type", "message")
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            content = msg_json.get("content")
            if not content:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": "Message content cannot be empty"})
                )
                continue

            # Rate limit check per WebSocket sender
            if not await manager.rate_limiter.is_allowed(str(user.id)):
                await websocket.send_text(
                    json.dumps({
                        "type": "error",
                        "detail": "Rate limit exceeded. Please wait a moment.",
                    })
                )
                continue

            try:
                MessageService.send_message(
                    db=db,
                    request_id=request_id,
                    sender=user,
                    content=content,
                )
            except ValueError as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": str(e)})
                )
            except PermissionError as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "detail": str(e)})
                )

    except WebSocketDisconnect:
        pass
    except Exception:
        # Prevent unhandled exception leaks
        pass
    finally:
        await manager.disconnect_repair_room(request_id, websocket)
        db.close()


@router.websocket("/repairs/{request_id}/ws")
async def repair_chat_websocket(
    websocket: WebSocket,
    request_id: str,
    token: str | None = Query(None),
):
    """WebSocket endpoint for real-time customer-mechanic repair conversation."""
    await _handle_chat_websocket(websocket, request_id, token)


@router.websocket("/ws/repairs/{request_id}")
async def repair_chat_websocket_alias(
    websocket: WebSocket,
    request_id: str,
    token: str | None = Query(None),
):
    """Alias WebSocket endpoint for real-time repair conversation."""
    await _handle_chat_websocket(websocket, request_id, token)
