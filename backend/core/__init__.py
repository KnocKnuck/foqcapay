"""
Core infrastructure for FOQCAPAY trading bot.

This module provides the foundational components for the multi-agent system:
- Event bus for agent communication
- Base agent class
- Configuration management
- Logging infrastructure
"""

from .config import settings, get_settings

__all__ = ["settings", "get_settings"]
