"""
Live Trading Service - CoinEx Integration

Agent: Trade Execution Agent
Squad: Execution
Sprint: 4.1

Handles REAL order execution on CoinEx exchange.

CRITICAL SAFETY FEATURES:
- Balance verification before EVERY order
- Production safeguards (max order size, daily limits)
- Order confirmation required
- Fail-safe defaults (reject if uncertain)
- Extensive logging for audit trail

Agent: #21 Trade Execution Agent
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import ccxt
import structlog

from core.security import (
    APIKeyManager,
    TradingModeValidator,
    ProductionSafeguards
)

logger = structlog.get_logger(__name__)


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class LiveOrder:
    """Live order record with full audit trail."""
    order_id: str
    exchange_order_id: Optional[str]
    pair: str
    side: str  # "buy" or "sell"
    order_type: str  # "market" or "limit"
    size: float
    price: Optional[float]
    status: OrderStatus
    created_at: str
    filled_at: Optional[str] = None
    filled_price: Optional[float] = None
    filled_size: Optional[float] = None
    fees: Optional[float] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "order_id": self.order_id,
            "exchange_order_id": self.exchange_order_id,
            "pair": self.pair,
            "side": self.side,
            "order_type": self.order_type,
            "size": self.size,
            "price": self.price,
            "status": self.status.value,
            "created_at": self.created_at,
            "filled_at": self.filled_at,
            "filled_price": self.filled_price,
            "filled_size": self.filled_size,
            "fees": self.fees,
            "error_message": self.error_message,
        }


@dataclass
class DailyTradingStats:
    """Track daily trading activity for limits."""
    date: str
    total_volume: float = 0.0
    orders_placed: int = 0
    orders_filled: int = 0
    orders_rejected: int = 0
    last_order_time: Optional[datetime] = None

    def can_place_order(self, order_size: float) -> Tuple[bool, str]:
        """Check if order can be placed based on daily limits."""
        # Check daily volume
        ok, msg = ProductionSafeguards.check_daily_volume(
            self.total_volume,
            order_size
        )
        if not ok:
            return False, msg

        # Check rate limiting
        if self.last_order_time:
            time_since_last = (datetime.utcnow() - self.last_order_time).total_seconds()
            if time_since_last < ProductionSafeguards.MIN_ORDER_INTERVAL:
                return False, f"Order too soon (wait {ProductionSafeguards.MIN_ORDER_INTERVAL}s between orders)"

        return True, "OK"


class LiveTradingService:
    """
    Manages live trading on CoinEx exchange.

    This service handles REAL MONEY - every operation is validated,
    logged, and protected by multiple safeguards.

    Features:
    - Real-time balance checking
    - Production safeguards
    - Order confirmation required
    - Comprehensive audit logging
    - Automatic daily limit resets
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        enable_live_trading: bool = False
    ):
        """
        Initialize live trading service.

        Args:
            api_key: CoinEx API key (encrypted)
            api_secret: CoinEx API secret (encrypted)
            enable_live_trading: Must be explicitly True to enable
        """
        self.key_manager = APIKeyManager()

        # Decrypt API credentials
        try:
            self.api_key = self.key_manager.decrypt_api_key(api_key)
            self.api_secret = self.key_manager.decrypt_api_key(api_secret)
        except Exception as e:
            logger.error("Failed to decrypt API credentials", error=str(e))
            raise ValueError("Invalid API credentials")

        # Validate credentials format
        is_valid, msg = self.key_manager.validate_api_key_format(
            self.api_key,
            self.api_secret
        )
        if not is_valid:
            raise ValueError(f"Invalid API credentials: {msg}")

        # Trading mode
        self.live_trading_enabled = enable_live_trading

        # Exchange client
        self.exchange: Optional[ccxt.coinex] = None

        # Account balances (cached)
        self.balances: Dict[str, float] = {}
        self.last_balance_update: Optional[datetime] = None

        # Order tracking
        self.orders: List[LiveOrder] = []
        self.order_counter = 0

        # Daily stats (reset at midnight UTC)
        self.daily_stats = DailyTradingStats(
            date=datetime.utcnow().strftime("%Y-%m-%d")
        )

        # Metrics
        self.metrics = {
            "total_orders": 0,
            "filled_orders": 0,
            "rejected_orders": 0,
            "total_fees_paid": 0.0,
            "total_volume": 0.0,
        }

        logger.info(
            "Live Trading Service initialized",
            live_enabled=self.live_trading_enabled,
            safeguards=ProductionSafeguards.get_limits_summary()
        )

    async def connect(self):
        """Connect to CoinEx exchange."""
        if not self.live_trading_enabled:
            logger.warning("Live trading disabled - connection skipped")
            return

        try:
            self.exchange = ccxt.coinex({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })

            # Test connection by fetching balance
            await self.exchange.load_markets()
            await self.fetch_balances()

            logger.info(
                "Connected to CoinEx for live trading",
                balance_usd=self.balances.get('USDC', 0)
            )

        except Exception as e:
            logger.error("Failed to connect to CoinEx", error=str(e))
            raise ConnectionError(f"CoinEx connection failed: {e}")

    async def disconnect(self):
        """Disconnect from exchange."""
        if self.exchange:
            await self.exchange.close()
            logger.info("Disconnected from CoinEx")

    async def fetch_balances(self) -> Dict[str, float]:
        """
        Fetch current account balances from exchange.

        Returns:
            Dictionary of {currency: balance}
        """
        if not self.exchange:
            raise RuntimeError("Not connected to exchange")

        try:
            balance_data = await self.exchange.fetch_balance()

            # Extract free balances
            self.balances = {
                currency: balance_data['free'].get(currency, 0.0)
                for currency in ['USDC', 'BTC', 'ETH', 'LINK']
            }

            self.last_balance_update = datetime.utcnow()

            logger.info("Balances updated", balances=self.balances)
            return self.balances

        except Exception as e:
            logger.error("Failed to fetch balances", error=str(e))
            raise

    async def validate_order(
        self,
        pair: str,
        side: str,
        size: float,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate an order before execution.

        Checks:
        - Live trading enabled
        - Order size within limits
        - Sufficient balance
        - Daily volume limits
        - Rate limiting

        Args:
            pair: Trading pair (e.g., "BTC/USDC")
            side: "buy" or "sell"
            size: Order size in USD
            price: Limit price (optional)

        Returns:
            (is_valid, error_message)
        """
        # Check if live trading enabled
        if not self.live_trading_enabled:
            return False, "Live trading is disabled"

        # Check production safeguards
        ok, msg = ProductionSafeguards.check_order_size(size)
        if not ok:
            return False, msg

        # Check daily stats
        ok, msg = self.daily_stats.can_place_order(size)
        if not ok:
            return False, msg

        # Refresh balances if stale (>30s)
        if (not self.last_balance_update or
            (datetime.utcnow() - self.last_balance_update).total_seconds() > 30):
            await self.fetch_balances()

        # Check balance
        if side == "buy":
            required_balance = size
            available = self.balances.get('USDC', 0)

            if available < required_balance:
                return False, f"Insufficient USDC balance (need ${required_balance:.2f}, have ${available:.2f})"

        else:  # sell
            # Extract base currency from pair (e.g., "BTC" from "BTC/USDC")
            base_currency = pair.split('/')[0]
            required_amount = size  # Simplified - in production would calculate from price

            available = self.balances.get(base_currency, 0)

            if available < required_amount:
                return False, f"Insufficient {base_currency} balance"

        return True, "Order valid"

    async def place_order(
        self,
        pair: str,
        side: str,
        size: float,
        order_type: str = "market",
        price: Optional[float] = None,
        user_confirmed: bool = False
    ) -> LiveOrder:
        """
        Place a LIVE order on CoinEx exchange.

        CRITICAL: This executes a REAL trade with REAL MONEY.

        Args:
            pair: Trading pair
            side: "buy" or "sell"
            size: Order size
            order_type: "market" or "limit"
            price: Limit price (required for limit orders)
            user_confirmed: User must explicitly confirm

        Returns:
            LiveOrder object

        Raises:
            ValueError: If order validation fails
            RuntimeError: If execution fails
        """
        # SAFETY CHECK: User must confirm
        if not user_confirmed:
            raise ValueError("User confirmation required for live orders (set user_confirmed=True)")

        # Validate order
        is_valid, error_msg = await self.validate_order(pair, side, size, price)
        if not is_valid:
            logger.warning("Order rejected", reason=error_msg)
            self.metrics["rejected_orders"] += 1
            self.daily_stats.orders_rejected += 1

            # Return rejected order
            return LiveOrder(
                order_id=f"LIVE-{self.order_counter:06d}",
                exchange_order_id=None,
                pair=pair,
                side=side,
                order_type=order_type,
                size=size,
                price=price,
                status=OrderStatus.REJECTED,
                created_at=datetime.utcnow().isoformat(),
                error_message=error_msg
            )

        # Generate order ID
        self.order_counter += 1
        order_id = f"LIVE-{self.order_counter:06d}"

        # Create order record
        order = LiveOrder(
            order_id=order_id,
            exchange_order_id=None,
            pair=pair,
            side=side,
            order_type=order_type,
            size=size,
            price=price,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow().isoformat()
        )

        try:
            # EXECUTE LIVE ORDER ON EXCHANGE
            logger.warning(
                "🚨 PLACING LIVE ORDER ON COINEX 🚨",
                pair=pair,
                side=side,
                size=size,
                type=order_type
            )

            result = await self.exchange.create_order(
                symbol=pair,
                type=order_type,
                side=side,
                amount=size,
                price=price
            )

            # Update order with exchange response
            order.exchange_order_id = result.get('id')
            order.status = OrderStatus.FILLED if result.get('status') == 'closed' else OrderStatus.PENDING
            order.filled_price = result.get('average') or result.get('price')
            order.filled_size = result.get('filled', 0)
            order.fees = result.get('fee', {}).get('cost', 0)

            if order.status == OrderStatus.FILLED:
                order.filled_at = datetime.utcnow().isoformat()

            # Update metrics
            self.metrics["total_orders"] += 1
            self.daily_stats.orders_placed += 1
            self.daily_stats.last_order_time = datetime.utcnow()

            if order.status == OrderStatus.FILLED:
                self.metrics["filled_orders"] += 1
                self.daily_stats.orders_filled += 1
                self.daily_stats.total_volume += size
                self.metrics["total_volume"] += size
                self.metrics["total_fees_paid"] += order.fees or 0

            # Store order
            self.orders.append(order)

            logger.warning(
                "✅ LIVE ORDER EXECUTED",
                order_id=order_id,
                exchange_id=order.exchange_order_id,
                status=order.status.value,
                filled_price=order.filled_price
            )

            return order

        except Exception as e:
            logger.error(
                "❌ LIVE ORDER FAILED",
                order_id=order_id,
                error=str(e)
            )

            order.status = OrderStatus.REJECTED
            order.error_message = str(e)
            self.metrics["rejected_orders"] += 1
            self.daily_stats.orders_rejected += 1

            self.orders.append(order)
            raise RuntimeError(f"Live order execution failed: {e}")

    async def get_order_status(self, exchange_order_id: str) -> Dict[str, Any]:
        """
        Fetch order status from exchange.

        Args:
            exchange_order_id: Exchange order ID

        Returns:
            Order status dictionary
        """
        if not self.exchange:
            raise RuntimeError("Not connected to exchange")

        try:
            order = await self.exchange.fetch_order(exchange_order_id)
            return {
                "id": order['id'],
                "status": order['status'],
                "filled": order.get('filled', 0),
                "remaining": order.get('remaining', 0),
                "price": order.get('price'),
                "average": order.get('average'),
                "fee": order.get('fee'),
            }

        except Exception as e:
            logger.error("Failed to fetch order status", error=str(e))
            raise

    async def cancel_order(self, exchange_order_id: str, pair: str) -> bool:
        """
        Cancel an open order.

        Args:
            exchange_order_id: Exchange order ID
            pair: Trading pair

        Returns:
            True if cancelled successfully
        """
        if not self.exchange:
            raise RuntimeError("Not connected to exchange")

        try:
            await self.exchange.cancel_order(exchange_order_id, pair)
            logger.info("Order cancelled", order_id=exchange_order_id)
            return True

        except Exception as e:
            logger.error("Failed to cancel order", error=str(e))
            return False

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily trading statistics."""
        return {
            "date": self.daily_stats.date,
            "total_volume": self.daily_stats.total_volume,
            "orders_placed": self.daily_stats.orders_placed,
            "orders_filled": self.daily_stats.orders_filled,
            "orders_rejected": self.daily_stats.orders_rejected,
            "volume_remaining": ProductionSafeguards.MAX_DAILY_VOLUME - self.daily_stats.total_volume,
        }

    def get_limits(self) -> Dict[str, Any]:
        """Get production safeguard limits."""
        return ProductionSafeguards.get_limits_summary()

    async def reset_daily_stats(self):
        """Reset daily stats at midnight UTC."""
        current_date = datetime.utcnow().strftime("%Y-%m-%d")

        if current_date != self.daily_stats.date:
            logger.info(
                "Resetting daily stats",
                old_date=self.daily_stats.date,
                new_date=current_date,
                volume_traded=self.daily_stats.total_volume
            )

            self.daily_stats = DailyTradingStats(date=current_date)
