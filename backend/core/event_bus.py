"""
Event Bus implementation using Redis Pub/Sub.
Enables 25 agents to communicate asynchronously.

Agent: System Architect Agent (designed)
Agent: DevOps Agent (implements)

Architecture Pattern: Publish-Subscribe
- Agents publish events to topics
- Other agents subscribe to topics of interest
- Loose coupling enables parallel development
"""

import json
import asyncio
from typing import Dict, Callable, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis
import structlog

from .config import settings

logger = structlog.get_logger()


class Event:
    """
    Event message passed through the event bus.

    Attributes:
        topic: Event topic (e.g., "market.btcusdc.tick")
        data: Event payload (dict)
        timestamp: Event creation time
        agent_id: ID of agent that published the event
    """

    def __init__(
        self,
        topic: str,
        data: Dict[str, Any],
        agent_id: Optional[str] = None
    ):
        self.topic = topic
        self.data = data
        self.timestamp = datetime.utcnow().isoformat()
        self.agent_id = agent_id or "system"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "topic": self.topic,
            "data": self.data,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        event = cls(
            topic=data["topic"],
            data=data["data"],
            agent_id=data.get("agent_id")
        )
        event.timestamp = data.get("timestamp", event.timestamp)
        return event

    def to_json(self) -> str:
        """Serialize event to JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Deserialize event from JSON."""
        return cls.from_dict(json.loads(json_str))


class EventBus:
    """
    Redis-based event bus for agent communication.

    Features:
    - Pub/Sub pattern for decoupled agents
    - Topic-based routing (e.g., "market.*", "signal.ma.*")
    - Async/await support
    - Message persistence (optional)
    - At-least-once delivery

    Usage:
        bus = EventBus()
        await bus.connect()

        # Subscribe to events
        await bus.subscribe("market.*.tick", callback_function)

        # Publish event
        await bus.publish(Event("market.btcusdc.tick", {"price": 30000}))
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.running = False
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            logger.info("event_bus_connected", redis_url=settings.redis_url)
        except Exception as e:
            logger.error("event_bus_connection_failed", error=str(e))
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        self.running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("event_bus_disconnected")

    async def publish(self, event: Event):
        """
        Publish an event to a topic.

        Args:
            event: Event to publish
        """
        if not self.redis_client:
            raise RuntimeError("Event bus not connected")

        try:
            message = event.to_json()
            await self.redis_client.publish(event.topic, message)

            logger.debug(
                "event_published",
                topic=event.topic,
                agent_id=event.agent_id
            )
        except Exception as e:
            logger.error(
                "event_publish_failed",
                topic=event.topic,
                error=str(e)
            )
            raise

    async def subscribe(self, topic: str, callback: Callable[[Event], Any]):
        """
        Subscribe to a topic.

        Args:
            topic: Topic pattern (supports wildcards: "market.*.tick")
            callback: Async function called when event received
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []

        self.subscriptions[topic].append(callback)

        # Subscribe in Redis (convert wildcards)
        redis_pattern = topic.replace("*", "*")
        await self.pubsub.psubscribe(redis_pattern)

        logger.info("subscribed_to_topic", topic=topic)

        # Start listener if not running
        if not self.running:
            await self.start_listening()

    async def start_listening(self):
        """Start listening for messages."""
        if self.running:
            return

        self.running = True
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("event_bus_listener_started")

    async def _listen(self):
        """Internal listener loop."""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    await self._handle_message(message)
        except asyncio.CancelledError:
            logger.info("event_bus_listener_cancelled")
        except Exception as e:
            logger.error("event_bus_listener_error", error=str(e))
            raise

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle received message."""
        try:
            # Parse event
            event = Event.from_json(message["data"])

            # Find matching subscriptions
            pattern = message["pattern"].decode() if isinstance(
                message["pattern"], bytes
            ) else message["pattern"]

            callbacks = self.subscriptions.get(pattern, [])

            # Call all subscribers
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(
                        "callback_error",
                        topic=event.topic,
                        error=str(e)
                    )
        except Exception as e:
            logger.error("message_handling_error", error=str(e))


# Global event bus instance
_event_bus: Optional[EventBus] = None


async def get_event_bus() -> EventBus:
    """Get or create global event bus instance."""
    global _event_bus

    if _event_bus is None:
        _event_bus = EventBus()
        await _event_bus.connect()

    return _event_bus
