import logging 
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket.manager import ConnectionManager

ws_manager=ConnectionManager()

logger = logging.getLogger(__name__)

router= APIRouter(tags=["WebSockets"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data=await websocket.receive_text()
            logger.debug(f"Received heartbeat from client: {data}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket cleanly.")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error:{e}")
        ws_manager.disconnect(websocket)