"""
SlickTrace v2 — WebSocket Endpoint for Real-Time Task Progress

Provides live pipeline progress updates to the frontend via WebSocket.
Frontend connects at: ws://host/ws/{incident_id}
Messages are JSON objects: {"type": "progress", "task": "...", "status": "...", "data": {...}}
"""
from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()

# In-memory connection manager
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, incident_id: str, ws: WebSocket):
        await ws.accept()
        if incident_id not in self._connections:
            self._connections[incident_id] = []
        self._connections[incident_id].append(ws)
        logger.info(f"[WS] Connected: incident={incident_id}")

    def disconnect(self, incident_id: str, ws: WebSocket):
        if incident_id in self._connections:
            try:
                self._connections[incident_id].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, incident_id: str, message: dict):
        """Broadcast a message to all WebSocket connections for an incident."""
        connections = self._connections.get(incident_id, [])
        dead = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(incident_id, ws)


manager = ConnectionManager()


@router.websocket("/{incident_id}")
async def websocket_endpoint(websocket: WebSocket, incident_id: str):
    """
    WebSocket endpoint for real-time pipeline progress.

    Connect: ws://host/api/v1/ws/{incident_id}
    Receive: JSON progress messages
    Send: ping (any text) to keep connection alive
    """
    await manager.connect(incident_id, websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "incident_id": incident_id,
            "message": "Connected to SlickTrace pipeline monitor",
        })

        # Keep connection alive, handle client pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send server-side ping
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(incident_id, websocket)
        logger.info(f"[WS] Disconnected: incident={incident_id}")
