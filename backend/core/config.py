"""
Configuration management for FOQCAPAY trading bot.
Loads settings from environment variables with validation.

Agent: DevOps/Config Agent
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # CoinEx API
    coinex_api_key: str = Field(default="", alias="COINEX_API_KEY")
    coinex_api_secret: str = Field(default="", alias="COINEX_API_SECRET")
    coinex_api_url: str = Field(
        default="https://api.coinex.com",
        alias="COINEX_API_URL"
    )

    # Trading Pairs - Multi-pair support!
    trading_pairs: str = Field(
        default="BTC/USDC,ETH/USDC,LINK/USDC",
        alias="TRADING_PAIRS"
    )

    @validator("trading_pairs")
    def parse_trading_pairs(cls, v) -> List[str]:
        """Parse comma-separated trading pairs."""
        if isinstance(v, str):
            return [pair.strip() for pair in v.split(",")]
        return v

    # Trading Mode
    trading_mode: str = Field(default="demo", alias="TRADING_MODE")

    @validator("trading_mode")
    def validate_trading_mode(cls, v):
        """Validate trading mode is either demo or live."""
        if v not in ["demo", "live"]:
            raise ValueError("Trading mode must be 'demo' or 'live'")
        return v

    # Demo Mode Settings
    demo_starting_balance: float = Field(
        default=10000.0,
        alias="DEMO_STARTING_BALANCE"
    )
    demo_slippage_pct: float = Field(default=0.1, alias="DEMO_SLIPPAGE_PCT")

    # Redis (Event Bus)
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./foqcapay.db",
        alias="DATABASE_URL"
    )

    # Risk Management Defaults
    default_stop_loss_pct: float = Field(
        default=2.0,
        alias="DEFAULT_STOP_LOSS_PCT"
    )
    default_take_profit_pct: float = Field(
        default=4.0,
        alias="DEFAULT_TAKE_PROFIT_PCT"
    )
    max_position_size_pct: float = Field(
        default=20.0,
        alias="MAX_POSITION_SIZE_PCT"
    )
    max_concurrent_positions: int = Field(
        default=5,
        alias="MAX_CONCURRENT_POSITIONS"
    )
    max_drawdown_pct: float = Field(
        default=10.0,
        alias="MAX_DRAWDOWN_PCT"
    )

    # Strategy Defaults
    default_strategy: str = Field(default="intraday", alias="DEFAULT_STRATEGY")
    enable_scalping: bool = Field(default=True, alias="ENABLE_SCALPING")
    enable_intraday: bool = Field(default=True, alias="ENABLE_INTRADAY")
    enable_swing: bool = Field(default=True, alias="ENABLE_SWING")

    # Performance
    max_workers: int = Field(default=10, alias="MAX_WORKERS")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    # Frontend
    frontend_url: str = Field(
        default="http://localhost:3000",
        alias="FRONTEND_URL"
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS"
    )

    @validator("cors_origins")
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Monitoring
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
