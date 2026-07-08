import logging 
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections:List[WebSocket]=[]

    async def connect(self,websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total connection :{len(self.active_connections)}")

    def disconnect(self,websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections:{len(self.active_connections)}")

    async def broadcast(self,message: dict):
        stale_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to a connection, marking as stale: {e}")
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)