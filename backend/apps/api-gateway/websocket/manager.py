import json
import asyncio
import logging
from typing import List
from fastapi import WebSocket
from config.redis import redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to a connection, marking as stale: {e}")
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


ws_manager = ConnectionManager()


async def redis_subscriber():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("ws:events")
    logger.info("Redis pub/sub subscriber listening on channel 'ws:events'")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await ws_manager.broadcast(data)
                except Exception as e:
                    logger.error(f"Failed to broadcast Redis message: {e}")
    except asyncio.CancelledError:
        await pubsub.unsubscribe("ws:events")
        logger.info("Redis subscriber stopped cleanly.")
