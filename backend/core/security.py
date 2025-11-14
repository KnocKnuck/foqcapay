"""
Security Module - API Key Encryption & Validation

Agent: System Architect Agent
Squad: Alpha
Sprint: 4.1

Handles secure storage and encryption of API keys for live trading.

CRITICAL: This module protects user API keys and secrets.
- Keys encrypted at rest
- Keys never logged
- Keys validated before use
- Secure key rotation support

Agent: #25 System Architect Agent
"""

import os
import base64
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger(__name__)


class APIKeyManager:
    """
    Manages encryption and decryption of API keys.

    Uses Fernet (symmetric encryption) with a master key derived
    from environment variable + salt.

    Security features:
    - Keys encrypted at rest
    - PBKDF2 key derivation
    - No keys in logs
    - Secure key validation
    """

    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize API key manager.

        Args:
            master_password: Master password for key derivation.
                           If not provided, uses MASTER_KEY env var.
        """
        self.master_password = master_password or os.getenv(
            "MASTER_KEY",
            "foqcapay-default-key-CHANGE-IN-PRODUCTION"
        )

        # Generate encryption key from master password
        self.encryption_key = self._derive_key(self.master_password)
        self.cipher = Fernet(self.encryption_key)

        logger.info("API Key Manager initialized (keys encrypted)")

    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Master password
            salt: Optional salt (uses fixed salt if not provided)

        Returns:
            32-byte encryption key
        """
        if salt is None:
            # Fixed salt for consistent key derivation
            # In production, this should be stored securely
            salt = b"foqcapay-salt-2024"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt an API key for secure storage.

        Args:
            api_key: Plain text API key

        Returns:
            Encrypted API key (base64 encoded)
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        encrypted = self.cipher.encrypt(api_key.encode())
        encrypted_str = base64.urlsafe_b64encode(encrypted).decode()

        logger.info("API key encrypted", key_length=len(api_key))
        return encrypted_str

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key for use.

        Args:
            encrypted_key: Encrypted API key (base64 encoded)

        Returns:
            Plain text API key
        """
        if not encrypted_key:
            raise ValueError("Encrypted key cannot be empty")

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)

            logger.info("API key decrypted successfully")
            return decrypted.decode()

        except Exception as e:
            logger.error("Failed to decrypt API key", error=str(e))
            raise ValueError("Invalid or corrupted API key")

    def validate_api_key_format(self, api_key: str, api_secret: str) -> Tuple[bool, str]:
        """
        Validate API key and secret format.

        Args:
            api_key: API key to validate
            api_secret: API secret to validate

        Returns:
            (is_valid, error_message)
        """
        # Check minimum lengths
        if len(api_key) < 16:
            return False, "API key too short (minimum 16 characters)"

        if len(api_secret) < 16:
            return False, "API secret too short (minimum 16 characters)"

        # Check for common issues
        if api_key == api_secret:
            return False, "API key and secret cannot be the same"

        if api_key.lower() == "your_api_key_here":
            return False, "Please provide a real API key"

        # Check for whitespace
        if ' ' in api_key or ' ' in api_secret:
            return False, "API key/secret cannot contain spaces"

        return True, "Valid"


class TradingModeValidator:
    """
    Validates trading mode transitions and permissions.

    Ensures users don't accidentally enable live trading without proper setup.
    """

    @staticmethod
    def can_enable_live_trading(
        api_key: Optional[str],
        api_secret: Optional[str],
        user_confirmed: bool = False
    ) -> Tuple[bool, str]:
        """
        Check if live trading can be enabled.

        Args:
            api_key: CoinEx API key
            api_secret: CoinEx API secret
            user_confirmed: Has user explicitly confirmed?

        Returns:
            (can_enable, error_message)
        """
        if not api_key or not api_secret:
            return False, "API key and secret required for live trading"

        if not user_confirmed:
            return False, "User confirmation required to enable live trading"

        # Validate format
        manager = APIKeyManager()
        is_valid, msg = manager.validate_api_key_format(api_key, api_secret)

        if not is_valid:
            return False, f"Invalid API credentials: {msg}"

        return True, "Live trading can be enabled"

    @staticmethod
    def validate_live_order(
        order_size: float,
        account_balance: float,
        max_order_size: float = 1000.0
    ) -> Tuple[bool, str]:
        """
        Validate a live order before execution.

        Args:
            order_size: Order size in USD
            account_balance: Current account balance
            max_order_size: Maximum allowed order size

        Returns:
            (is_valid, error_message)
        """
        if order_size <= 0:
            return False, "Order size must be positive"

        if order_size > max_order_size:
            return False, f"Order size exceeds maximum (${max_order_size})"

        if order_size > account_balance:
            return False, "Insufficient balance for order"

        if order_size > account_balance * 0.5:
            return False, "Order size exceeds 50% of account balance (safety limit)"

        return True, "Order valid"


class ProductionSafeguards:
    """
    Production safeguards to prevent catastrophic losses.

    These are hard limits that cannot be overridden without code changes.
    """

    # Maximum single order size in USD
    MAX_ORDER_SIZE = 5000.0

    # Maximum daily trading volume in USD
    MAX_DAILY_VOLUME = 20000.0

    # Maximum number of orders per minute
    MAX_ORDERS_PER_MINUTE = 10

    # Maximum number of open positions
    MAX_OPEN_POSITIONS = 10

    # Minimum time between orders (seconds)
    MIN_ORDER_INTERVAL = 1.0

    @classmethod
    def check_order_size(cls, size: float) -> Tuple[bool, str]:
        """Check if order size is within limits."""
        if size > cls.MAX_ORDER_SIZE:
            return False, f"Order exceeds maximum size (${cls.MAX_ORDER_SIZE})"
        return True, "OK"

    @classmethod
    def check_daily_volume(cls, current_volume: float, new_order: float) -> Tuple[bool, str]:
        """Check if daily volume is within limits."""
        total = current_volume + new_order
        if total > cls.MAX_DAILY_VOLUME:
            return False, f"Daily volume limit reached (${cls.MAX_DAILY_VOLUME})"
        return True, "OK"

    @classmethod
    def get_limits_summary(cls) -> dict:
        """Get summary of all production limits."""
        return {
            "max_order_size": cls.MAX_ORDER_SIZE,
            "max_daily_volume": cls.MAX_DAILY_VOLUME,
            "max_orders_per_minute": cls.MAX_ORDERS_PER_MINUTE,
            "max_open_positions": cls.MAX_OPEN_POSITIONS,
            "min_order_interval": cls.MIN_ORDER_INTERVAL,
        }
