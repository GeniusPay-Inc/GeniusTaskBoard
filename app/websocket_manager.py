import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("taskboard.ws")


class ConnectionManager:
    """Garde la liste des clients connectés (dashboard TV, back-office, clients externes)
    et diffuse les événements métier (voir docs/CONCEPTION.md §4)."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Client WS connecté (%d actifs)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("Client WS déconnecté (%d actifs)", len(self._connections))

    async def broadcast(self, event: dict) -> None:
        payload = json.dumps(event, default=str)
        dead = []
        for connection in self._connections:
            try:
                await connection.send_text(payload)
            except Exception:  # connexion fermée / cassée
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection)


manager = ConnectionManager()
