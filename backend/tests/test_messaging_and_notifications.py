import json
import pytest
from starlette.websockets import WebSocketDisconnect

from app.websocket.connection_manager import manager


def test_authorized_send_and_get_messages(client, test_setup):
    """Test authorized customer and mechanic messaging and history retrieval."""
    req_id = str(test_setup["repair_request"].id)
    cust_token = test_setup["customer_token"]
    mech_token = test_setup["mechanic_token"]

    # 1. Customer sends message
    cust_resp = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"content": "Hi mechanic, when can you inspect my car?"},
    )
    assert cust_resp.status_code == 201
    cust_data = cust_resp.json()
    assert cust_data["content"] == "Hi mechanic, when can you inspect my car?"
    assert cust_data["sender_id"] == str(test_setup["customer"].id)
    assert cust_data["sender_role"] == "customer"
    assert "sent_at" in cust_data

    # 2. Mechanic replies
    mech_resp = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {mech_token}"},
        json={"content": "Hello! I can inspect it this afternoon at 2 PM."},
    )
    assert mech_resp.status_code == 201
    mech_data = mech_resp.json()
    assert mech_data["content"] == "Hello! I can inspect it this afternoon at 2 PM."
    assert mech_data["sender_id"] == str(test_setup["mechanic_user"].id)
    assert mech_data["sender_role"] == "mechanic"

    # 3. Retrieve history as customer
    history_resp = client.get(
        f"/api/v1/repairs/{req_id}/messages?skip=0&limit=10",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert history["total"] >= 2
    assert len(history["messages"]) >= 2
    contents = [m["content"] for m in history["messages"]]
    assert "Hi mechanic, when can you inspect my car?" in contents
    assert "Hello! I can inspect it this afternoon at 2 PM." in contents

    # 4. Retrieve history as mechanic
    mech_history = client.get(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {mech_token}"},
    )
    assert mech_history.status_code == 200
    assert mech_history.json()["total"] == history["total"]


def test_unauthorized_conversation_access(client, test_setup):
    """Test that unauthorized users cannot view or send messages in another's conversation."""
    req_id = str(test_setup["repair_request"].id)
    unauth_token = test_setup["unauthorized_token"]

    # Unauthorized customer cannot view messages
    resp_get = client.get(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert resp_get.status_code == 403
    assert "access denied" in resp_get.json()["detail"].lower()

    # Unauthorized customer cannot send messages
    resp_post = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {unauth_token}"},
        json={"content": "I am an unauthorized intruder trying to chat."},
    )
    assert resp_post.status_code == 403

    # Unauthenticated request returns 401
    unauthenticated = client.get(f"/api/v1/repairs/{req_id}/messages")
    assert unauthenticated.status_code == 401

    # Non-existent repair request returns 404
    fake_id = "00000000-0000-0000-0000-000000000000"
    not_found = client.get(
        f"/api/v1/repairs/{fake_id}/messages",
        headers={"Authorization": f"Bearer {test_setup['customer_token']}"},
    )
    assert not_found.status_code == 404


def test_message_on_pending_request_without_mechanic(client, test_setup):
    """Test that sending a message on a request with no mechanic assigned returns an error."""
    pending_id = str(test_setup["pending_request"].id)
    cust_token = test_setup["customer_token"]

    resp = client.post(
        f"/api/v1/repairs/{pending_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"content": "Can anybody hear me?"},
    )
    assert resp.status_code == 400
    assert "assigned mechanic" in resp.json()["detail"].lower()


def test_message_validation_limits(client, test_setup):
    """Test validation on empty message and excessively long messages."""
    req_id = str(test_setup["repair_request"].id)
    cust_token = test_setup["customer_token"]

    # Empty content
    empty_resp = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"content": ""},
    )
    assert empty_resp.status_code == 422

    # Whitespace only
    ws_resp = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"content": "   "},
    )
    assert ws_resp.status_code == 400

    # Over 2000 characters
    long_content = "x" * 2001
    long_resp = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"content": long_content},
    )
    assert long_resp.status_code == 422


def test_notifications_creation_and_read_status(client, test_setup):
    """Test notification creation on new message and marking read/unread operations."""
    req_id = str(test_setup["repair_request"].id)
    cust_token = test_setup["customer_token"]
    mech_token = test_setup["mechanic_token"]
    unauth_token = test_setup["unauthorized_token"]

    # Customer sends message -> mechanic gets notification
    send_resp = client.post(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"content": "Notification trigger test message."},
    )
    assert send_resp.status_code == 201

    # Mechanic checks notifications list
    notif_list_resp = client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {mech_token}"},
    )
    assert notif_list_resp.status_code == 200
    data = notif_list_resp.json()
    assert data["total"] >= 1
    assert data["unread_count"] >= 1

    # Find the newly created notification
    matching_notifs = [n for n in data["notifications"] if "Notification trigger test message" in n["content"]]
    assert len(matching_notifs) >= 1
    target_notif = matching_notifs[0]
    assert target_notif["is_read"] is False
    assert target_notif["type"] == "new_message"

    # Mechanic checks unread count endpoint
    unread_resp = client.get(
        "/api/v1/notifications/unread-count",
        headers={"Authorization": f"Bearer {mech_token}"},
    )
    assert unread_resp.status_code == 200
    initial_unread = unread_resp.json()["unread_count"]
    assert initial_unread >= 1

    # Unauthorized user tries to mark mechanic's notification as read
    unauth_mark = client.put(
        f"/api/v1/notifications/{target_notif['id']}/read",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert unauth_mark.status_code == 404

    # Mechanic marks individual notification as read
    mark_resp = client.put(
        f"/api/v1/notifications/{target_notif['id']}/read",
        headers={"Authorization": f"Bearer {mech_token}"},
    )
    assert mark_resp.status_code == 200
    assert mark_resp.json()["is_read"] is True

    # Mechanic marks all as read
    read_all_resp = client.put(
        "/api/v1/notifications/read-all",
        headers={"Authorization": f"Bearer {mech_token}"},
    )
    assert read_all_resp.status_code == 200
    assert read_all_resp.json()["success"] is True

    # Check unread count is now 0
    final_unread = client.get(
        "/api/v1/notifications/unread-count",
        headers={"Authorization": f"Bearer {mech_token}"},
    )
    assert final_unread.json()["unread_count"] == 0


def test_repair_lifecycle_notifications(client, test_setup):
    """Test notifications created during repair request status transitions."""
    req_id = str(test_setup["repair_request"].id)
    cust_token = test_setup["customer_token"]
    mech_token = test_setup["mechanic_token"]

    # Mechanic completes the repair
    complete_resp = client.put(
        f"/api/v1/repairs/{req_id}",
        headers={"Authorization": f"Bearer {mech_token}"},
        json={"status": "completed"},
    )
    assert complete_resp.status_code == 200

    # Customer should have a repair_completed notification
    cust_notifs = client.get(
        "/api/v1/notifications",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert cust_notifs.status_code == 200
    notifs = cust_notifs.json()["notifications"]
    completed_notifs = [n for n in notifs if n["type"] == "repair_completed"]
    assert len(completed_notifs) >= 1
    assert "completed" in completed_notifs[0]["title"].lower()


def test_websocket_chat_authorized_and_delivery(client, test_setup):
    """Test WebSocket chat authentication, real-time message exchange, and ping-pong."""
    req_id = str(test_setup["repair_request"].id)
    cust_token = test_setup["customer_token"]
    mech_token = test_setup["mechanic_token"]

    # 1. Customer connects, verifies handshake, sends ping-pong, and sends a message
    with client.websocket_connect(f"/api/v1/repairs/{req_id}/ws?token={cust_token}") as ws_cust:
        init_frame = ws_cust.receive_json()
        assert init_frame["type"] == "connected"
        assert init_frame["role"] == "customer"
        assert init_frame["request_id"] == req_id

        # Ping-pong
        ws_cust.send_json({"type": "ping"})
        pong = ws_cust.receive_json()
        assert pong["type"] == "pong"

        # Customer sends chat message via WebSocket
        ws_cust.send_json({"type": "message", "content": "Live WebSocket message from customer"})

    # 2. Mechanic connects, verifies handshake, and sends ping-pong
    with client.websocket_connect(f"/api/v1/repairs/{req_id}/ws?token={mech_token}") as ws_mech:
        mech_init = ws_mech.receive_json()
        assert mech_init["type"] == "connected"
        assert mech_init["role"] == "mechanic"

        ws_mech.send_json({"type": "ping"})
        assert ws_mech.receive_json()["type"] == "pong"

        # Mechanic sends chat message via WebSocket
        ws_mech.send_json({"type": "message", "content": "Live WebSocket reply from mechanic"})

    # 3. Verify messages were saved in database
    history = client.get(
        f"/api/v1/repairs/{req_id}/messages",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert history.status_code == 200
    contents = [m["content"] for m in history.json()["messages"]]
    assert "Live WebSocket message from customer" in contents
    assert "Live WebSocket reply from mechanic" in contents


def test_websocket_chat_unauthorized_and_invalid_token(client, test_setup):
    """Test that unauthorized users and invalid tokens are rejected on WebSocket connection."""
    req_id = str(test_setup["repair_request"].id)
    unauth_token = test_setup["unauthorized_token"]

    # 1. Invalid token rejected with policy violation (1008)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/v1/repairs/{req_id}/ws?token=invalid.jwt.token"):
            pass
    assert exc_info.value.code == 1008

    # 2. Missing token rejected
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/v1/repairs/{req_id}/ws"):
            pass
    assert exc_info.value.code == 1008

    # 3. Unauthorized participant rejected with policy violation (1008)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/v1/repairs/{req_id}/ws?token={unauth_token}"):
            pass
    assert exc_info.value.code == 1008


def test_websocket_notification_stream(client, test_setup):
    """Test connection, authentication, initial handshake and ping-pong on notification WebSocket."""
    mech_token = test_setup["mechanic_token"]

    with client.websocket_connect(f"/api/v1/notifications/ws?token={mech_token}") as ws_notif:
        init_frame = ws_notif.receive_json()
        assert init_frame["type"] == "connected"
        assert init_frame["user_id"] == str(test_setup["mechanic_user"].id)
        assert "unread_count" in init_frame

        # Ping-pong test
        ws_notif.send_json({"type": "ping"})
        pong = ws_notif.receive_json()
        assert pong["type"] == "pong"


def test_rate_limiting_enforcement(client, test_setup):
    """Test that rapid request flood triggers rate limiting."""
    req_id = str(test_setup["repair_request"].id)
    cust_token = test_setup["customer_token"]

    # Exhaust rate limit quota
    rate_limited = False
    for i in range(35):
        resp = client.post(
            f"/api/v1/repairs/{req_id}/messages",
            headers={"Authorization": f"Bearer {cust_token}"},
            json={"content": f"Spam message {i}"},
        )
        if resp.status_code == 429:
            rate_limited = True
            assert "rate limit exceeded" in resp.json()["detail"].lower()
            break

    assert rate_limited, "Expected rate limit (429) to be triggered within 35 requests"


@pytest.mark.anyio
async def test_connection_manager_broadcast_and_pruning():
    """Test connection manager broadcast delivery and safe disconnected socket cleanup."""
    class MockWebSocket:
        def __init__(self, should_fail: bool = False):
            self.should_fail = should_fail
            self.sent_messages = []

        async def send_text(self, text: str):
            if self.should_fail:
                raise RuntimeError("Connection reset by peer")
            self.sent_messages.append(text)

    # Test repair room broadcast
    healthy_ws = MockWebSocket(should_fail=False)
    broken_ws = MockWebSocket(should_fail=True)
    room_id = "test-room-123"

    await manager.connect_repair_room(room_id, healthy_ws, "user-1")
    await manager.connect_repair_room(room_id, broken_ws, "user-2")

    # Broadcast message: broken socket should be pruned, healthy receives it
    await manager.broadcast_to_repair_room(room_id, {"type": "chat", "text": "hello"})
    assert len(healthy_ws.sent_messages) == 1
    assert "hello" in healthy_ws.sent_messages[0]

    # Verify broken socket was pruned
    assert broken_ws not in manager.repair_rooms[room_id]

    # Cleanup healthy socket
    await manager.disconnect_repair_room(room_id, healthy_ws)
    assert room_id not in manager.repair_rooms

    # Test notification dispatch to user
    user_id = "notif-user-1"
    user_ws = MockWebSocket(should_fail=False)
    await manager.connect_notifications(user_id, user_ws)
    await manager.send_notification_to_user(user_id, {"type": "alert", "text": "new alert"})
    assert len(user_ws.sent_messages) == 1
    assert "new alert" in user_ws.sent_messages[0]
    await manager.disconnect_notifications(user_id, user_ws)

