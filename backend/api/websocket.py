"""
WebSocket API - Real-Time Updates

Agent: API Development Agent
Squad: Alpha
Sprint: 4.2

Provides WebSocket connections for real-time data streaming.

Features:
- Live price updates
- Position changes
- Trade execution notifications
- Risk alerts
- System metrics
- Health status

Agent: #20 API Development Agent
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Any
import asyncio
import json
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts.

    Handles:
    - Client connections/disconnections
    - Message broadcasting
    - Topic subscriptions
    - Connection health checks
    """

    def __init__(self):
        # Active connections
        self.active_connections: Set[WebSocket] = set()

        # Topic subscriptions: {topic: set of websockets}
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        logger.info("WebSocket Connection Manager initialized")

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Accept new WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "connected_at": datetime.utcnow().isoformat(),
            "subscriptions": set(),
        }

        logger.info(
            "WebSocket connected",
            client_id=client_id,
            total_connections=len(self.active_connections)
        )

    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket to disconnect
        """
        # Remove from active connections
        self.active_connections.discard(websocket)

        # Remove from all subscriptions
        for topic_subscribers in self.subscriptions.values():
            topic_subscribers.discard(websocket)

        # Remove metadata
        metadata = self.connection_metadata.pop(websocket, {})

        logger.info(
            "WebSocket disconnected",
            client_id=metadata.get("client_id"),
            total_connections=len(self.active_connections)
        )

    async def subscribe(self, websocket: WebSocket, topic: str):
        """
        Subscribe WebSocket to a topic.

        Args:
            websocket: WebSocket connection
            topic: Topic to subscribe to
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()

        self.subscriptions[topic].add(websocket)

        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].add(topic)

        logger.info(
            "WebSocket subscribed",
            client_id=self.connection_metadata.get(websocket, {}).get("client_id"),
            topic=topic
        )

    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """
        Unsubscribe WebSocket from a topic.

        Args:
            websocket: WebSocket connection
            topic: Topic to unsubscribe from
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)

        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["subscriptions"].discard(topic)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message to broadcast
        """
        if not self.active_connections:
            return

        # Convert to JSON
        message_json = json.dumps(message)

        # Send to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error("Failed to send message", error=str(e))
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """
        Broadcast message to subscribers of a topic.

        Args:
            topic: Topic to broadcast to
            message: Message to send
        """
        if topic not in self.subscriptions:
            return

        subscribers = self.subscriptions[topic]
        if not subscribers:
            return

        # Add topic to message
        message["topic"] = topic

        # Convert to JSON
        message_json = json.dumps(message)

        # Send to subscribers
        disconnected = []
        for connection in subscribers:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(
                    "Failed to send topic message",
                    topic=topic,
                    error=str(e)
                )
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "total_topics": len(self.subscriptions),
            "topics": {
                topic: len(subscribers)
                for topic, subscribers in self.subscriptions.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time updates.

    Protocol:
    - Client connects with unique client_id
    - Client sends JSON messages to subscribe/unsubscribe
    - Server sends JSON messages with updates

    Message format (client to server):
    {
        "action": "subscribe" | "unsubscribe",
        "topic": "prices" | "positions" | "trades" | "alerts" | "metrics"
    }

    Message format (server to client):
    {
        "topic": "prices",
        "type": "update",
        "data": {...},
        "timestamp": "2024-01-01T00:00:00Z"
    }
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")
                topic = message.get("topic")

                if action == "subscribe" and topic:
                    await manager.subscribe(websocket, topic)
                    await websocket.send_json({
                        "type": "subscribed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif action == "unsubscribe" and topic:
                    await manager.unsubscribe(websocket, topic)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "topic": topic,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif action == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received", client_id=client_id)
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", client_id=client_id, error=str(e))
        manager.disconnect(websocket)


async def broadcast_price_update(pair: str, price: float, change_24h: float):
    """Broadcast price update to subscribers."""
    await manager.broadcast_to_topic("prices", {
        "type": "price_update",
        "data": {
            "pair": pair,
            "price": price,
            "change_24h": change_24h,
        },
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_position_update(position: Dict[str, Any]):
    """Broadcast position update to subscribers."""
    await manager.broadcast_to_topic("positions", {
        "type": "position_update",
        "data": position,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_trade_executed(trade: Dict[str, Any]):
    """Broadcast trade execution to subscribers."""
    await manager.broadcast_to_topic("trades", {
        "type": "trade_executed",
        "data": trade,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_risk_alert(alert: Dict[str, Any]):
    """Broadcast risk alert to subscribers."""
    await manager.broadcast_to_topic("alerts", {
        "type": "risk_alert",
        "data": alert,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_metrics_update(metrics: Dict[str, Any]):
    """Broadcast system metrics to subscribers."""
    await manager.broadcast_to_topic("metrics", {
        "type": "metrics_update",
        "data": metrics,
        "timestamp": datetime.utcnow().isoformat()
    })


def get_connection_manager() -> ConnectionManager:
    """Get global connection manager."""
    return manager
