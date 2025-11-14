"""
Database Models - SQLAlchemy ORM Models

Agent: System Architect Agent + API Development Agent
Squad: Alpha
Sprint: 4.3

Defines database schema for persistent storage of trading data.

Models:
- Trade: Completed trades with P&L
- Position: Open/closed positions
- Order: Individual orders (entry/exit)
- AccountState: Account balance snapshots
- TradingEvent: Audit trail of all trading decisions

Agent: #25 System Architect Agent, #20 API Development Agent
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import structlog

logger = structlog.get_logger(__name__)

Base = declarative_base()


class Trade(Base):
    """
    Completed trade with entry and exit details.

    Represents a full trade lifecycle from entry to exit with P&L calculation.
    """

    __tablename__ = "trades"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)

    # Trading Pair & Strategy
    pair = Column(String(20), nullable=False, index=True)
    strategy = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy or sell

    # Entry Details
    entry_time = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    entry_order_id = Column(String(50))

    # Exit Details
    exit_time = Column(DateTime, nullable=False, index=True)
    exit_price = Column(Float, nullable=False)
    exit_order_id = Column(String(50))
    exit_reason = Column(
        String(50), nullable=False
    )  # stop_loss, take_profit, signal, manual

    # Position Sizing
    size = Column(Float, nullable=False)  # Amount in base currency
    position_value_usd = Column(Float, nullable=False)

    # Performance Metrics
    pnl = Column(Float, nullable=False)  # Profit/loss in USD
    pnl_percent = Column(Float, nullable=False)  # P&L as percentage
    fees = Column(Float, default=0.0)  # Trading fees
    net_pnl = Column(Float, nullable=False)  # P&L after fees

    # Risk Parameters (at time of trade)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    trailing_stop = Column(Float)

    # Metadata
    duration_minutes = Column(Integer)  # How long position was held
    slippage = Column(Float, default=0.0)  # Price slippage
    notes = Column(Text)  # Additional notes or annotations

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index("idx_trades_pair_strategy", "pair", "strategy"),
        Index("idx_trades_exit_time_desc", exit_time.desc()),
        Index("idx_trades_pnl", "pnl"),
    )

    def __repr__(self):
        return (
            f"<Trade(id={self.trade_id}, pair={self.pair}, "
            f"pnl=${self.pnl:.2f}, exit={self.exit_time})>"
        )


class Position(Base):
    """
    Trading position (open or closed).

    Tracks individual positions with real-time P&L updates.
    """

    __tablename__ = "positions"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(50), unique=True, nullable=False, index=True)

    # Trading Pair & Strategy
    pair = Column(String(20), nullable=False, index=True)
    strategy = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy or sell

    # Entry Details
    entry_time = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    entry_order_id = Column(String(50))

    # Position Sizing
    size = Column(Float, nullable=False)  # Amount in base currency
    position_value_usd = Column(Float, nullable=False)

    # Current State
    current_price = Column(Float)  # Last known price
    unrealized_pnl = Column(Float, default=0.0)  # Current unrealized P&L
    unrealized_pnl_percent = Column(Float, default=0.0)

    # Risk Parameters
    stop_loss = Column(Float)
    take_profit = Column(Float)
    trailing_stop = Column(Float)
    trailing_stop_activation = Column(Float)  # Price that activates trailing stop

    # Status
    status = Column(
        String(20), nullable=False, default="open", index=True
    )  # open, closed
    closed_at = Column(DateTime)
    closed_by = Column(String(50))  # What closed it: stop_loss, take_profit, etc.

    # Realized P&L (when closed)
    realized_pnl = Column(Float)
    realized_pnl_percent = Column(Float)

    # Metadata
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_positions_status", "status"),
        Index("idx_positions_pair_status", "pair", "status"),
        Index("idx_positions_entry_time_desc", entry_time.desc()),
    )

    def __repr__(self):
        return (
            f"<Position(id={self.position_id}, pair={self.pair}, "
            f"status={self.status}, entry={self.entry_price})>"
        )


class Order(Base):
    """
    Individual order (entry or exit).

    Low-level order tracking for audit trail.
    """

    __tablename__ = "orders"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)

    # Exchange & Trading Pair
    exchange = Column(String(20), default="coinex")
    pair = Column(String(20), nullable=False, index=True)

    # Order Details
    order_type = Column(String(20), nullable=False)  # market, limit, stop
    side = Column(String(10), nullable=False)  # buy or sell
    price = Column(Float)  # Limit price (if applicable)
    size = Column(Float, nullable=False)  # Order size

    # Execution
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, filled, cancelled, failed
    filled_price = Column(Float)  # Actual fill price
    filled_size = Column(Float)  # Actual filled amount
    filled_at = Column(DateTime)

    # Fees
    fee = Column(Float, default=0.0)
    fee_currency = Column(String(10))

    # Associations
    position_id = Column(String(50), index=True)  # Link to position
    trade_id = Column(String(50), index=True)  # Link to trade (if closed)

    # Error Handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Order(id={self.order_id}, {self.side} {self.size} {self.pair}, "
            f"status={self.status})>"
        )


class AccountState(Base):
    """
    Account balance snapshots over time.

    Records account state for performance tracking and recovery.
    """

    __tablename__ = "account_states"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Account Details
    account_id = Column(String(50), default="default")
    mode = Column(String(10), nullable=False, index=True)  # demo or live

    # Balances
    total_balance = Column(Float, nullable=False)  # Total account value in USD
    available_balance = Column(Float, nullable=False)  # Available for trading
    allocated_balance = Column(Float, default=0.0)  # In open positions

    # Performance Metrics
    total_pnl = Column(Float, default=0.0)  # All-time P&L
    daily_pnl = Column(Float, default=0.0)  # Today's P&L
    unrealized_pnl = Column(Float, default=0.0)  # Open positions P&L

    # Position Counts
    open_positions = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)

    # Drawdown Tracking
    peak_balance = Column(Float)  # Highest balance ever
    current_drawdown = Column(Float, default=0.0)  # Current drawdown %
    max_drawdown = Column(Float, default=0.0)  # Maximum drawdown ever

    # Risk Status
    risk_status = Column(String(20), default="normal")  # normal, warning, critical
    trading_paused = Column(Boolean, default=False)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes
    __table_args__ = (
        Index("idx_account_mode_time", "mode", timestamp.desc()),
        Index("idx_account_timestamp_desc", timestamp.desc()),
    )

    def __repr__(self):
        return (
            f"<AccountState(mode={self.mode}, balance=${self.total_balance:.2f}, "
            f"pnl=${self.total_pnl:.2f}, time={self.timestamp})>"
        )


class TradingEvent(Base):
    """
    Audit trail of all trading decisions and events.

    Comprehensive logging for compliance, debugging, and analysis.
    """

    __tablename__ = "trading_events"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event Classification
    event_type = Column(
        String(50), nullable=False, index=True
    )  # signal, order, position, risk, system
    event_category = Column(String(50), nullable=False)  # entry, exit, alert, error
    severity = Column(
        String(20), default="info"
    )  # debug, info, warning, error, critical

    # Event Details
    message = Column(Text, nullable=False)
    data = Column(Text)  # JSON-encoded event data

    # Associations
    pair = Column(String(20), index=True)
    strategy = Column(String(50))
    position_id = Column(String(50))
    order_id = Column(String(50))
    trade_id = Column(String(50))

    # Agent Attribution
    agent_name = Column(String(100))  # Which agent generated this event
    agent_id = Column(String(50))

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes for fast querying
    __table_args__ = (
        Index("idx_events_type_time", "event_type", timestamp.desc()),
        Index("idx_events_pair_time", "pair", timestamp.desc()),
        Index("idx_events_severity", "severity"),
        Index("idx_events_timestamp_desc", timestamp.desc()),
    )

    def __repr__(self):
        return (
            f"<TradingEvent(type={self.event_type}, severity={self.severity}, "
            f"time={self.timestamp})>"
        )


# Migration helper
def create_all_tables(engine):
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info(
        "Database tables created successfully",
        tables=[
            "trades",
            "positions",
            "orders",
            "account_states",
            "trading_events",
        ],
    )


def drop_all_tables(engine):
    """
    Drop all database tables (use with caution!).

    Args:
        engine: SQLAlchemy engine
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(engine)
    logger.warning("All database tables dropped")
