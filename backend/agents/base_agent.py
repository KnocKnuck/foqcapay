"""
Base Agent class that all agents inherit from.

Provides common functionality for agent lifecycle, event bus integration,
and health monitoring.

Agent: System Architect Agent (designed)
Agent: All Agents (implement)
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional
import structlog

from core.event_bus import EventBus, get_event_bus, Event

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Base class for all agents in the system.

    All 25 agents inherit from this class and implement the required methods.
    Provides common functionality for lifecycle management and event bus integration.

    Attributes:
        agent_id: Unique identifier for this agent
        event_bus: Reference to the global event bus
        running: Whether the agent is currently running

    Example:
        class MyAgent(BaseAgent):
            async def start(self):
                await super().start()
                await self.event_bus.subscribe("some.topic", self.handle_event)

            async def handle_event(self, event: Event):
                # Process event
                pass
    """

    def __init__(self, agent_id: str):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier (e.g., "market_data", "ma_indicator")
        """
        self.agent_id = agent_id
        self.event_bus: Optional[EventBus] = None
        self.running = False
        self._tasks: list[asyncio.Task] = []

        logger.info("agent_initialized", agent_id=agent_id)

    async def initialize(self):
        """
        Initialize agent with event bus connection.

        Called before start(). Sets up event bus reference.
        """
        self.event_bus = await get_event_bus()
        logger.info("agent_connected_to_event_bus", agent_id=self.agent_id)

    @abstractmethod
    async def start(self):
        """
        Start the agent.

        Override this method to implement agent-specific startup logic.
        Don't forget to call super().start() at the beginning!

        Example:
            async def start(self):
                await super().start()
                # Your startup logic here
                await self.event_bus.subscribe("topic", self.handler)
        """
        self.running = True
        logger.info("agent_started", agent_id=self.agent_id)

    async def stop(self):
        """
        Stop the agent gracefully.

        Cancels all background tasks and cleans up resources.
        """
        self.running = False

        # Cancel all background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("agent_stopped", agent_id=self.agent_id)

    async def publish(self, topic: str, data: dict):
        """
        Publish an event to the event bus.

        Args:
            topic: Event topic (e.g., "market.btcusdc.tick")
            data: Event payload

        Example:
            await self.publish("market.btcusdc.tick", {
                "price": 30125.50,
                "volume": 1234.56
            })
        """
        if not self.event_bus:
            raise RuntimeError(f"Agent {self.agent_id} not initialized")

        event = Event(topic=topic, data=data, agent_id=self.agent_id)
        await self.event_bus.publish(event)

        logger.debug(
            "event_published",
            agent_id=self.agent_id,
            topic=topic
        )

    async def subscribe(self, topic: str, callback):
        """
        Subscribe to events on a topic.

        Args:
            topic: Topic pattern (supports wildcards: "market.*.tick")
            callback: Async function to call when event received

        Example:
            await self.subscribe("market.*.tick", self.handle_tick)
        """
        if not self.event_bus:
            raise RuntimeError(f"Agent {self.agent_id} not initialized")

        await self.event_bus.subscribe(topic, callback)

        logger.info(
            "subscribed_to_topic",
            agent_id=self.agent_id,
            topic=topic
        )

    def create_task(self, coro):
        """
        Create a background task that will be cancelled on agent stop.

        Args:
            coro: Coroutine to run as background task

        Returns:
            asyncio.Task: The created task

        Example:
            self.create_task(self.periodic_health_check())
        """
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task

    async def health_check(self) -> dict:
        """
        Return health status of this agent.

        Override to provide agent-specific health metrics.

        Returns:
            dict: Health status with at minimum {"status": "healthy"|"unhealthy"}

        Example:
            {
                "status": "healthy",
                "last_update": "2025-11-14T10:30:00Z",
                "messages_processed": 1234
            }
        """
        return {
            "agent_id": self.agent_id,
            "status": "healthy" if self.running else "stopped",
            "running": self.running
        }
