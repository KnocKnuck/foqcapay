"""
Market Data Agent - Multi-pair real-time price streaming from CoinEx.

Connects to CoinEx exchange via CCXT library and streams real-time market data
for multiple trading pairs (BTC/USDC, ETH/USDC, LINK/USDC, etc.).

Agent: Market Data Agent
Collaborates With: Data Validation Agent, All Indicator Agents
Publishes Events:
  - "market.{pair}.tick" - Real-time price/volume updates
  - "market.{pair}.candle" - OHLCV candle data

Example Event:
    {
        "topic": "market.btcusdc.tick",
        "data": {
            "pair": "BTC/USDC",
            "price": 30125.50,
            "volume": 1234.56,
            "timestamp": "2025-11-14T10:30:00Z"
        }
    }

Configuration:
    TRADING_PAIRS env variable (comma-separated): BTC/USDC,ETH/USDC,LINK/USDC

Sprint: 1.2 (Multi-pair support from day one!)
Status: In Development
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import ccxt.async_support as ccxt
import structlog

from .base_agent import BaseAgent
from core.config import settings

logger = structlog.get_logger()


class MarketDataAgent(BaseAgent):
    """
    Streams real-time market data for multiple trading pairs from CoinEx.

    Attributes:
        pairs: List of trading pairs to monitor (e.g., ["BTC/USDC", "ETH/USDC"])
        exchange: CCXT exchange instance (CoinEx)
        update_interval: Seconds between price updates (default: 1.0)
    """

    def __init__(self, pairs: List[str] = None):
        """
        Initialize Market Data Agent.

        Args:
            pairs: Trading pairs to monitor. If None, uses settings.trading_pairs
        """
        super().__init__(agent_id="market_data")

        # Multi-pair support!
        self.pairs = pairs or settings.trading_pairs
        self.exchange: Optional[ccxt.coinex] = None
        self.update_interval = 1.0  # 1 second updates

        # Track latest data for each pair
        self.latest_data: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "market_data_agent_initialized",
            pairs=self.pairs,
            num_pairs=len(self.pairs)
        )

    async def start(self):
        """
        Start the Market Data Agent.

        Connects to CoinEx and begins streaming data for all configured pairs.
        """
        await super().start()

        # Initialize CoinEx exchange
        await self._connect_to_exchange()

        # Start fetching data for all pairs in parallel
        for pair in self.pairs:
            self.create_task(self._fetch_pair_data(pair))

        logger.info(
            "market_data_agent_started",
            pairs=self.pairs,
            exchange="coinex"
        )

    async def _connect_to_exchange(self):
        """
        Connect to CoinEx exchange via CCXT.

        Uses API keys from settings if in live mode, otherwise uses public API.
        """
        try:
            config = {
                "enableRateLimit": True,  # Respect rate limits
                "timeout": 30000,  # 30 second timeout
            }

            # Add API credentials if in live mode
            if settings.trading_mode == "live" and settings.coinex_api_key:
                config["apiKey"] = settings.coinex_api_key
                config["secret"] = settings.coinex_api_secret

            self.exchange = ccxt.coinex(config)

            # Load markets
            await self.exchange.load_markets()

            logger.info(
                "connected_to_coinex",
                mode=settings.trading_mode,
                markets_loaded=len(self.exchange.markets)
            )

        except Exception as e:
            logger.error(
                "coinex_connection_failed",
                error=str(e)
            )
            raise

    async def _fetch_pair_data(self, pair: str):
        """
        Fetch data for a single trading pair in a loop.

        Args:
            pair: Trading pair (e.g., "BTC/USDC")
        """
        logger.info("starting_pair_stream", pair=pair)

        while self.running:
            try:
                # Fetch ticker (current price, volume, etc.)
                ticker = await self.exchange.fetch_ticker(pair)

                # Extract relevant data
                data = {
                    "pair": pair,
                    "price": ticker["last"],  # Last traded price
                    "bid": ticker.get("bid"),
                    "ask": ticker.get("ask"),
                    "volume_24h": ticker.get("quoteVolume", 0),
                    "high_24h": ticker.get("high"),
                    "low_24h": ticker.get("low"),
                    "change_24h_pct": ticker.get("percentage", 0),
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Store latest data
                self.latest_data[pair] = data

                # Publish tick event
                await self._publish_tick(pair, data)

                # Wait before next update
                await asyncio.sleep(self.update_interval)

            except ccxt.NetworkError as e:
                logger.warning(
                    "network_error_fetching_data",
                    pair=pair,
                    error=str(e)
                )
                # Wait a bit longer before retry
                await asyncio.sleep(5.0)

            except Exception as e:
                logger.error(
                    "error_fetching_pair_data",
                    pair=pair,
                    error=str(e)
                )
                await asyncio.sleep(5.0)

    async def _publish_tick(self, pair: str, data: Dict[str, Any]):
        """
        Publish a price tick event for a trading pair.

        Args:
            pair: Trading pair (e.g., "BTC/USDC")
            data: Market data dictionary

        Publishes to topic: "market.{normalized_pair}.tick"
        Example: "market.btcusdc.tick"
        """
        # Normalize pair for topic (BTC/USDC -> btcusdc)
        normalized_pair = pair.replace("/", "").lower()
        topic = f"market.{normalized_pair}.tick"

        await self.publish(topic, data)

        logger.debug(
            "tick_published",
            pair=pair,
            price=data["price"],
            topic=topic
        )

    async def get_latest_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest cached data for a pair.

        Args:
            pair: Trading pair (e.g., "BTC/USDC")

        Returns:
            dict: Latest market data or None if not available
        """
        return self.latest_data.get(pair)

    async def stop(self):
        """Stop the agent and close exchange connection."""
        await super().stop()

        if self.exchange:
            await self.exchange.close()
            logger.info("exchange_connection_closed")

    async def health_check(self) -> dict:
        """
        Health check for Market Data Agent.

        Returns:
            dict: Health status including connection state and data freshness
        """
        base_health = await super().health_check()

        # Add agent-specific health metrics
        base_health.update({
            "exchange_connected": self.exchange is not None,
            "pairs_monitored": len(self.pairs),
            "pairs_with_data": len(self.latest_data),
            "update_interval": self.update_interval
        })

        # Check data freshness for each pair
        stale_pairs = []
        for pair, data in self.latest_data.items():
            timestamp = datetime.fromisoformat(data["timestamp"])
            age = (datetime.utcnow() - timestamp).total_seconds()
            if age > 10:  # Data older than 10 seconds is stale
                stale_pairs.append(pair)

        if stale_pairs:
            base_health["status"] = "degraded"
            base_health["stale_pairs"] = stale_pairs

        return base_health


# TODO Sprint 1.2: Integrate with main.py to start this agent
# TODO Sprint 1.2: Add WebSocket support for even lower latency (optional)
# TODO Sprint 2: Add OHLCV candle aggregation for charting
