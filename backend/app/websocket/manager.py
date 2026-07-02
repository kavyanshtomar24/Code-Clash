"""
WebSocket connection manager with Redis Pub/Sub synchronization.

Manages active connections grouped by room (battle_id), and syncs messages across
multiple backend instances using Redis Pub/Sub.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and Redis Pub/Sub subscriptions for room-based broadcasting."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        """Accept connection and add it to the room list."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)

        if room_id not in self.pubsub_tasks:
            self.pubsub_tasks[room_id] = asyncio.create_task(self._redis_listener(room_id))

        logger.info(
            "WebSocket connected to room %s (%d clients)",
            room_id,
            len(self.active_connections[room_id]),
        )

    async def disconnect(self, websocket: WebSocket, room_id: str) -> None:
        """Remove connection from room."""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
                if room_id in self.pubsub_tasks:
                    self.pubsub_tasks[room_id].cancel()
                    del self.pubsub_tasks[room_id]
                    logger.info("Stopped Redis listener for empty room %s", room_id)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send message directly to a single socket client."""
        await websocket.send_text(json.dumps(message))

    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        """Publish message to Redis Pub/Sub so all server instances broadcast it.

        When Redis is available the listener task picks up the message and
        delivers it to local clients, so we must NOT also call
        ``_local_broadcast`` here — that would cause duplicate delivery.
        """
        payload = json.dumps(message)
        try:
            await cache_service.publish(f"battle:{room_id}", payload)
        except Exception as exc:
            logger.warning("Redis publish failed: %s — local fallback", exc)
            await self._local_broadcast(room_id, message)

    async def _local_broadcast(self, room_id: str, message: dict) -> None:
        """Broadcast message only to clients connected to THIS server instance."""
        sockets = self.active_connections.get(room_id, set())
        if sockets:
            payload = json.dumps(message)
            await asyncio.gather(
                *[self._safe_send(ws, payload, room_id) for ws in list(sockets)],
                return_exceptions=True,
            )

    async def _safe_send(self, websocket: WebSocket, payload: str, room_id: str) -> None:
        """Send payload to a socket, cleaning up disconnected clients."""
        try:
            await websocket.send_text(payload)
        except Exception:
            await self.disconnect(websocket, room_id)

    async def _redis_listener(self, room_id: str) -> None:
        """Subscribe to Redis Pub/Sub channel and broadcast to local connections."""
        channel_name = f"battle:{room_id}"
        logger.info("Started Redis listener for room %s", room_id)

        while True:
            pubsub = None
            try:
                redis_client = await cache_service.get_client()
                pubsub = redis_client.pubsub()
                await pubsub.subscribe(channel_name)

                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            await self._local_broadcast(room_id, data)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON on channel %s", channel_name)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Redis listener error for room %s: %s", room_id, exc)
                await asyncio.sleep(2.0)
            finally:
                if pubsub is not None:
                    try:
                        await pubsub.unsubscribe(channel_name)
                        await pubsub.close()
                    except Exception:
                        pass


ws_manager = ConnectionManager()
