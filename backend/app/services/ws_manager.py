"""
WebSocket connection manager for appointment chat channels.
"""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Set
from uuid import UUID

from fastapi import WebSocket


class ChatConnectionManager:
    """Stores active socket connections per appointment."""

    def __init__(self) -> None:
        self._rooms: DefaultDict[UUID, Set[WebSocket]] = defaultdict(set)

    async def connect(self, appointment_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[appointment_id].add(websocket)

    def disconnect(self, appointment_id: UUID, websocket: WebSocket) -> None:
        room = self._rooms.get(appointment_id)
        if not room:
            return
        room.discard(websocket)
        if not room:
            self._rooms.pop(appointment_id, None)

    async def broadcast(self, appointment_id: UUID, payload: dict) -> None:
        sockets = list(self._rooms.get(appointment_id, set()))
        for socket in sockets:
            await socket.send_json(payload)


chat_manager = ChatConnectionManager()
