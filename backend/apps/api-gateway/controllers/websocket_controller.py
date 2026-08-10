import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from config.settings import settings
from websocket import ws_manager
logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


def _authenticate_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub") is not None
    except JWTError:
        return False


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    if not _authenticate_token(token):
        await websocket.close(code=4001)
        logger.warning("WebSocket connection rejected: invalid or missing token.")
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received heartbeat from client: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket cleanly.")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
        ws_manager.disconnect(websocket)