import asyncio
import json
import time
from collections import defaultdict, deque
from typing import Any, Dict, Optional, Set
from fastapi import WebSocket


class RateLimiter:
    """In-memory sliding-window rate limiter per user."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        """Check if request is within allowed rate limit."""
        async with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            timestamps = self.history[key]

            # Pop expired timestamps
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                return False

            timestamps.append(now)
            return True


class ConnectionManager:
    """
    Manages active WebSocket connections for repair request conversations
    and user-specific real-time notifications.
    """

    def __init__(self):
        # Maps request_id -> Set of WebSocket connections
        self.repair_rooms: Dict[str, Set[WebSocket]] = defaultdict(set)
        # Maps request_id -> Dict[WebSocket, user_id]
        self.room_users: Dict[str, Dict[WebSocket, str]] = defaultdict(dict)
        # Maps user_id -> Set of WebSocket connections for notifications
        self.notification_listeners: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.lock = asyncio.Lock()
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

    # ---------------- Repair Conversation Rooms ----------------

    async def connect_repair_room(
        self, request_id: str, websocket: WebSocket, user_id: str
    ) -> None:
        """Register a WebSocket connection to a repair request chat room."""
        async with self.lock:
            self.repair_rooms[request_id].add(websocket)
            self.room_users[request_id][websocket] = user_id

    async def disconnect_repair_room(
        self, request_id: str, websocket: WebSocket
    ) -> None:
        """Safely unregister a WebSocket connection from a chat room."""
        async with self.lock:
            self.repair_rooms[request_id].discard(websocket)
            self.room_users[request_id].pop(websocket, None)
            if not self.repair_rooms[request_id]:
                self.repair_rooms.pop(request_id, None)
                self.room_users.pop(request_id, None)

    async def broadcast_to_repair_room(
        self, request_id: str, message: Dict[str, Any], exclude: Optional[WebSocket] = None
    ) -> None:
        """
        Broadcast a message payload to all active clients in a repair room.
        Stale/broken connections are safely pruned.
        """
        async with self.lock:
            sockets = list(self.repair_rooms.get(request_id, set()))

        disconnected: Set[WebSocket] = set()
        text_data = json.dumps(message)

        for ws in sockets:
            if ws is exclude:
                continue
            try:
                await ws.send_text(text_data)
            except Exception:
                disconnected.add(ws)

        if disconnected:
            async with self.lock:
                for ws in disconnected:
                    self.repair_rooms[request_id].discard(ws)
                    self.room_users[request_id].pop(ws, None)
                if not self.repair_rooms[request_id]:
                    self.repair_rooms.pop(request_id, None)
                    self.room_users.pop(request_id, None)

    # ---------------- User Notifications ----------------

    async def connect_notifications(self, user_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection for user real-time notifications."""
        async with self.lock:
            self.notification_listeners[user_id].add(websocket)

    async def disconnect_notifications(self, user_id: str, websocket: WebSocket) -> None:
        """Safely unregister a user notification WebSocket."""
        async with self.lock:
            self.notification_listeners[user_id].discard(websocket)
            if not self.notification_listeners[user_id]:
                self.notification_listeners.pop(user_id, None)

    async def send_notification_to_user(
        self, user_id: str, notification: Dict[str, Any]
    ) -> None:
        """
        Deliver a notification to all active sockets of a specific user.
        Stale connections are safely pruned.
        """
        async with self.lock:
            sockets = list(self.notification_listeners.get(user_id, set()))

        if not sockets:
            return

        disconnected: Set[WebSocket] = set()
        text_data = json.dumps(notification)

        for ws in sockets:
            try:
                await ws.send_text(text_data)
            except Exception:
                disconnected.add(ws)

        if disconnected:
            async with self.lock:
                for ws in disconnected:
                    self.notification_listeners[user_id].discard(ws)
                if not self.notification_listeners[user_id]:
                    self.notification_listeners.pop(user_id, None)


# Global singleton instance
manager = ConnectionManager()
