"""
Database Service - Async Database Operations

Agent: System Architect Agent
Squad: Alpha
Sprint: 4.3

Provides async database operations and session management.

Features:
- Async SQLite database connections
- Session management with context managers
- CRUD operations for all models
- Query helpers
- Transaction management
- Connection pooling

Agent: #25 System Architect Agent
"""

import os
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
import structlog

from models.database import (
    Base,
    Trade,
    Position,
    Order,
    AccountState,
    TradingEvent,
)
from core.config import settings

logger = structlog.get_logger(__name__)


class DatabaseService:
    """
    Async database service for managing trading data persistence.

    Provides high-level API for database operations with proper
    async/await support and transaction management.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database service.

        Args:
            database_url: Optional database URL (defaults to config)
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.async_session_maker = None
        self._initialized = False

        logger.info("DatabaseService initialized", database_url=self.database_url)

    def _get_database_url(self) -> str:
        """Get database URL from config or environment."""
        # Use SQLite by default
        db_path = os.path.join(os.getcwd(), "data", "foqcapay.db")

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        return f"sqlite+aiosqlite:///{db_path}"

    async def initialize(self):
        """
        Initialize database engine and create tables.

        Must be called before using the database service.
        """
        if self._initialized:
            logger.warning("DatabaseService already initialized")
            return

        logger.info("Initializing database engine...")

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL query logging
            future=True,
        )

        # Create session maker
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self._initialized = True
        logger.info(
            "Database initialized successfully",
            tables=["trades", "positions", "orders", "account_states", "trading_events"],
        )

    async def shutdown(self):
        """Shutdown database engine and cleanup."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine disposed")

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """
        Get async database session context manager.

        Usage:
            async with db_service.get_session() as session:
                result = await session.execute(select(Trade))
        """
        if not self._initialized:
            await self.initialize()

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", error=str(e))
                raise
            finally:
                await session.close()

    # ========== TRADE OPERATIONS ==========

    async def create_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """
        Create new trade record.

        Args:
            trade_data: Trade data dictionary

        Returns:
            Created Trade object
        """
        async with self.get_session() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            await session.flush()
            await session.refresh(trade)

            logger.info(
                "Trade created",
                trade_id=trade.trade_id,
                pair=trade.pair,
                pnl=trade.pnl,
            )

            return trade

    async def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get trade by ID."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Trade).where(Trade.trade_id == trade_id)
            )
            return result.scalar_one_or_none()

    async def get_trades(
        self,
        pair: Optional[str] = None,
        strategy: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Trade]:
        """
        Get trades with optional filters.

        Args:
            pair: Filter by trading pair
            strategy: Filter by strategy
            start_date: Filter trades after this date
            end_date: Filter trades before this date
            limit: Maximum number of trades
            offset: Pagination offset

        Returns:
            List of Trade objects
        """
        async with self.get_session() as session:
            query = select(Trade)

            # Apply filters
            filters = []
            if pair:
                filters.append(Trade.pair == pair)
            if strategy:
                filters.append(Trade.strategy == strategy)
            if start_date:
                filters.append(Trade.exit_time >= start_date)
            if end_date:
                filters.append(Trade.exit_time <= end_date)

            if filters:
                query = query.where(and_(*filters))

            # Order by exit time (most recent first)
            query = query.order_by(desc(Trade.exit_time))

            # Pagination
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            return result.scalars().all()

    async def get_trade_count(
        self,
        pair: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> int:
        """Get total count of trades with optional filters."""
        async with self.get_session() as session:
            query = select(func.count(Trade.id))

            filters = []
            if pair:
                filters.append(Trade.pair == pair)
            if strategy:
                filters.append(Trade.strategy == strategy)

            if filters:
                query = query.where(and_(*filters))

            result = await session.execute(query)
            return result.scalar()

    # ========== POSITION OPERATIONS ==========

    async def create_position(self, position_data: Dict[str, Any]) -> Position:
        """Create new position record."""
        async with self.get_session() as session:
            position = Position(**position_data)
            session.add(position)
            await session.flush()
            await session.refresh(position)

            logger.info(
                "Position created",
                position_id=position.position_id,
                pair=position.pair,
                side=position.side,
            )

            return position

    async def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.position_id == position_id)
            )
            return result.scalar_one_or_none()

    async def get_open_positions(
        self,
        pair: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> List[Position]:
        """Get all open positions with optional filters."""
        async with self.get_session() as session:
            query = select(Position).where(Position.status == "open")

            if pair:
                query = query.where(Position.pair == pair)
            if strategy:
                query = query.where(Position.strategy == strategy)

            query = query.order_by(desc(Position.entry_time))

            result = await session.execute(query)
            return result.scalars().all()

    async def update_position(
        self, position_id: str, updates: Dict[str, Any]
    ) -> Optional[Position]:
        """Update position with new data."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Position).where(Position.position_id == position_id)
            )
            position = result.scalar_one_or_none()

            if position:
                for key, value in updates.items():
                    setattr(position, key, value)

                position.updated_at = datetime.utcnow()

                logger.debug(
                    "Position updated",
                    position_id=position_id,
                    updates=list(updates.keys()),
                )

            return position

    async def close_position(
        self, position_id: str, closed_by: str, realized_pnl: float
    ) -> Optional[Position]:
        """Close a position."""
        return await self.update_position(
            position_id,
            {
                "status": "closed",
                "closed_at": datetime.utcnow(),
                "closed_by": closed_by,
                "realized_pnl": realized_pnl,
            },
        )

    # ========== ORDER OPERATIONS ==========

    async def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create new order record."""
        async with self.get_session() as session:
            order = Order(**order_data)
            session.add(order)
            await session.flush()
            await session.refresh(order)

            logger.info(
                "Order created",
                order_id=order.order_id,
                pair=order.pair,
                side=order.side,
                status=order.status,
            )

            return order

    async def update_order(
        self, order_id: str, updates: Dict[str, Any]
    ) -> Optional[Order]:
        """Update order status and details."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Order).where(Order.order_id == order_id)
            )
            order = result.scalar_one_or_none()

            if order:
                for key, value in updates.items():
                    setattr(order, key, value)

                order.updated_at = datetime.utcnow()

            return order

    # ========== ACCOUNT STATE OPERATIONS ==========

    async def save_account_state(self, state_data: Dict[str, Any]) -> AccountState:
        """Save account state snapshot."""
        async with self.get_session() as session:
            account_state = AccountState(**state_data)
            session.add(account_state)
            await session.flush()
            await session.refresh(account_state)

            logger.debug(
                "Account state saved",
                mode=account_state.mode,
                balance=account_state.total_balance,
            )

            return account_state

    async def get_latest_account_state(self, mode: str = "demo") -> Optional[AccountState]:
        """Get most recent account state."""
        async with self.get_session() as session:
            result = await session.execute(
                select(AccountState)
                .where(AccountState.mode == mode)
                .order_by(desc(AccountState.timestamp))
                .limit(1)
            )
            return result.scalar_one_or_none()

    # ========== TRADING EVENT OPERATIONS ==========

    async def log_event(self, event_data: Dict[str, Any]) -> TradingEvent:
        """Log trading event to database."""
        async with self.get_session() as session:
            event = TradingEvent(**event_data)
            session.add(event)
            await session.flush()
            await session.refresh(event)

            return event

    async def get_events(
        self,
        event_type: Optional[str] = None,
        pair: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TradingEvent]:
        """Get trading events with filters."""
        async with self.get_session() as session:
            query = select(TradingEvent)

            filters = []
            if event_type:
                filters.append(TradingEvent.event_type == event_type)
            if pair:
                filters.append(TradingEvent.pair == pair)
            if severity:
                filters.append(TradingEvent.severity == severity)
            if start_time:
                filters.append(TradingEvent.timestamp >= start_time)

            if filters:
                query = query.where(and_(*filters))

            query = query.order_by(desc(TradingEvent.timestamp)).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    # ========== ANALYTICS & STATISTICS ==========

    async def get_performance_stats(
        self,
        pair: Optional[str] = None,
        strategy: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get performance statistics.

        Returns comprehensive stats including win rate, P&L, etc.
        """
        async with self.get_session() as session:
            # Build query for trades in time period
            start_date = datetime.utcnow() - timedelta(days=days)

            query = select(Trade).where(Trade.exit_time >= start_date)

            if pair:
                query = query.where(Trade.pair == pair)
            if strategy:
                query = query.where(Trade.strategy == strategy)

            result = await session.execute(query)
            trades = result.scalars().all()

            # Calculate statistics
            if not trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "largest_win": 0.0,
                    "largest_loss": 0.0,
                    "profit_factor": 0.0,
                    "expectancy": 0.0,
                }

            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl <= 0]

            total_pnl = sum(t.pnl for t in trades)
            total_wins = sum(t.pnl for t in winning_trades)
            total_losses = abs(sum(t.pnl for t in losing_trades))

            avg_win = (
                total_wins / len(winning_trades) if winning_trades else 0.0
            )
            avg_loss = (
                total_losses / len(losing_trades) if losing_trades else 0.0
            )

            win_rate = len(winning_trades) / len(trades) if trades else 0.0

            profit_factor = (
                total_wins / total_losses
                if total_losses > 0
                else float("inf") if total_wins > 0 else 0.0
            )

            expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

            return {
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "largest_win": max([t.pnl for t in winning_trades], default=0.0),
                "largest_loss": min([t.pnl for t in losing_trades], default=0.0),
                "profit_factor": profit_factor,
                "expectancy": expectancy,
            }


# Global database service instance
db_service = DatabaseService()


# FastAPI dependency
async def get_db_service() -> DatabaseService:
    """Dependency for FastAPI routes."""
    if not db_service._initialized:
        await db_service.initialize()
    return db_service
