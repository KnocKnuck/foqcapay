"""
Tests for Event Bus (Redis Pub/Sub).

Agent: Bug & Resolution Agent
Squad: Alpha
Sprint: 1.2

Tests Cover:
- Connection to Redis
- Publishing events
- Subscribing to topics
- Message delivery
- Error handling

Run:
    pytest tests/test_event_bus.py -v
"""

import pytest
import asyncio
from core.event_bus import EventBus, Event


@pytest.mark.asyncio
async def test_event_bus_connection():
    """Test that event bus can connect to Redis."""
    bus = EventBus()
    await bus.connect()

    assert bus.redis_client is not None
    assert bus.pubsub is not None

    await bus.disconnect()


@pytest.mark.asyncio
async def test_publish_event():
    """Test publishing an event to the bus."""
    bus = EventBus()
    await bus.connect()

    event = Event(
        topic="test.topic",
        data={"message": "hello"},
        agent_id="test_agent"
    )

    # Should not raise exception
    await bus.publish(event)

    await bus.disconnect()


@pytest.mark.asyncio
async def test_subscribe_and_receive():
    """Test subscribing to a topic and receiving events."""
    bus = EventBus()
    await bus.connect()

    received_events = []

    async def callback(event: Event):
        received_events.append(event)

    # Subscribe
    await bus.subscribe("test.*", callback)

    # Give subscription time to register
    await asyncio.sleep(0.1)

    # Publish event
    test_event = Event(
        topic="test.message",
        data={"value": 42},
        agent_id="test_publisher"
    )
    await bus.publish(test_event)

    # Wait for delivery
    await asyncio.sleep(0.5)

    # Verify received
    assert len(received_events) > 0
    assert received_events[0].data["value"] == 42

    await bus.disconnect()


@pytest.mark.asyncio
async def test_event_serialization():
    """Test event to/from JSON serialization."""
    event = Event(
        topic="market.btcusdc.tick",
        data={"price": 30125.50, "volume": 1234.56},
        agent_id="market_data"
    )

    # Serialize
    json_str = event.to_json()
    assert isinstance(json_str, str)
    assert "30125.50" in json_str

    # Deserialize
    restored = Event.from_json(json_str)
    assert restored.topic == event.topic
    assert restored.data["price"] == 30125.50
    assert restored.agent_id == "market_data"
