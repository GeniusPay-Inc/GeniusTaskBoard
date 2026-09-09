from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Note: en v1 pas d'auth stricte sur le WS (écran TV interne). En phase 2,
    # valider un token/clé passé en query param (voir docs/ADR.md ADR-003).
    await manager.connect(websocket)
    try:
        while True:
            # on ne traite pas de messages entrants pour l'instant, juste le keep-alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
