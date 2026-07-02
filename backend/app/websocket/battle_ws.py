"""
WebSocket route handler for competitive coding battles.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.websocket.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/battle/{battle_id}")
async def battle_websocket_endpoint(
    websocket: WebSocket,
    battle_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for a specific battle room."""
    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        username = payload.get("username", "Unknown")
        if not user_id_str:
            await websocket.close(code=4001, reason="Invalid token payload")
            return
    except Exception as exc:
        logger.warning("WebSocket authentication failed: %s", exc)
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await ws_manager.connect(websocket, battle_id)

    await ws_manager.send_personal_message(
        {"type": "connected", "username": username, "user_id": user_id_str},
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    await ws_manager.send_personal_message({"type": "pong"}, websocket)

                elif msg_type == "chat":
                    text = message.get("text", "")
                    await ws_manager.broadcast_to_room(
                        battle_id,
                        {"type": "chat", "username": username, "text": text},
                    )

                elif msg_type == "opponent_status":
                    await ws_manager.broadcast_to_room(
                        battle_id,
                        {
                            "type": "opponent_status",
                            "user_id": user_id_str,
                            "username": username,
                            "event": message.get("event", "typing"),
                        },
                    )

            except json.JSONDecodeError:
                await ws_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON format"},
                    websocket,
                )

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, battle_id)
        await ws_manager.broadcast_to_room(
            battle_id,
            {
                "type": "opponent_status",
                "username": username,
                "user_id": user_id_str,
                "event": "disconnected",
            },
        )
