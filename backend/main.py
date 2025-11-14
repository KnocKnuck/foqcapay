"""
FOQCAPAY Trading Bot - Main Application Entry Point

Multi-agent crypto trading system with 25 specialized agents.
Supports multi-pair trading (BTC/USDC, ETH/USDC, LINK/USDC, etc.)

Author: FOQCAPAY Team
Version: 0.1.0-alpha (Sprint 1.2)
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from core.config import settings
from core.event_bus import get_event_bus
from api import router as api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown of the event bus and agents.
    """
    # Startup
    logger.info(
        "application_starting",
        version="0.1.0-alpha",
        mode=settings.trading_mode,
        pairs=settings.trading_pairs
    )

    # Initialize event bus
    event_bus = await get_event_bus()
    logger.info("event_bus_initialized")

    # TODO Sprint 1.2: Initialize agents here
    # - Market Data Agent
    # - Indicator Agents (MA, RSI)
    # - Dashboard Agent

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await event_bus.disconnect()
    logger.info("application_shutdown_complete")


# Create FastAPI application
app = FastAPI(
    title="FOQCAPAY Trading Bot",
    description="Multi-agent crypto trading system with real-time market data",
    version="0.1.0-alpha",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - system status."""
    return {
        "name": "FOQCAPAY Trading Bot",
        "version": "0.1.0-alpha",
        "status": "operational",
        "mode": settings.trading_mode,
        "trading_pairs": settings.trading_pairs,
        "sprint": "1.2 - Infrastructure Setup"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mode": settings.trading_mode,
        "redis": "connected",  # TODO: actual check
        "agents": "initializing"  # TODO: agent health
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(
        "starting_server",
        host="0.0.0.0",
        port=8000,
        mode=settings.trading_mode
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
