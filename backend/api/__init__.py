"""
FastAPI routes for the FOQCAPAY trading bot.

Agent: Dashboard Agent (provides data to frontend)
"""

from fastapi import APIRouter

router = APIRouter()

# Import route modules
from . import market_data, health

__all__ = ["router"]
