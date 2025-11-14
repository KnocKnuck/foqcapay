"""
Tests for Security Module

Agent: Bug & Resolution Agent
Squad: Alpha
Sprint: 4.1

CRITICAL TESTS - Security and API Key Protection

Tests Cover:
- API key encryption/decryption
- API key validation
- Trading mode validation
- Production safeguards
- Order validation
- Daily limits

Run:
    pytest tests/test_security.py -v
"""

import pytest
from core.security import (
    APIKeyManager,
    TradingModeValidator,
    ProductionSafeguards
)


def test_api_key_encryption_decryption():
    """Test API keys are encrypted and decrypted correctly."""
    manager = APIKeyManager(master_password="test-password-123")

    original_key = "my-secret-api-key-12345"

    # Encrypt
    encrypted = manager.encrypt_api_key(original_key)

    # Should be different from original
    assert encrypted != original_key

    # Should be base64 encoded (no special chars except safe ones)
    assert all(c.isalnum() or c in '-_=' for c in encrypted)

    # Decrypt
    decrypted = manager.decrypt_api_key(encrypted)

    # Should match original
    assert decrypted == original_key


def test_api_key_encryption_different_each_time():
    """Test encryption produces different output each time (IV randomization)."""
    manager = APIKeyManager()

    key = "test-api-key"

    encrypted1 = manager.encrypt_api_key(key)
    encrypted2 = manager.encrypt_api_key(key)

    # Should be different ciphertexts
    assert encrypted1 != encrypted2

    # But both should decrypt to same value
    assert manager.decrypt_api_key(encrypted1) == key
    assert manager.decrypt_api_key(encrypted2) == key


def test_api_key_encryption_empty_key():
    """Test encryption rejects empty keys."""
    manager = APIKeyManager()

    with pytest.raises(ValueError, match="API key cannot be empty"):
        manager.encrypt_api_key("")


def test_api_key_decryption_invalid_key():
    """Test decryption fails gracefully on invalid keys."""
    manager = APIKeyManager()

    with pytest.raises(ValueError, match="Invalid or corrupted"):
        manager.decrypt_api_key("not-a-valid-encrypted-key")


def test_api_key_decryption_empty_key():
    """Test decryption rejects empty keys."""
    manager = APIKeyManager()

    with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
        manager.decrypt_api_key("")


def test_api_key_validation_valid_keys():
    """Test valid API keys pass validation."""
    manager = APIKeyManager()

    api_key = "abcdef1234567890"  # 16 chars
    api_secret = "xyz9876543210abc"  # 16 chars

    is_valid, msg = manager.validate_api_key_format(api_key, api_secret)

    assert is_valid is True
    assert msg == "Valid"


def test_api_key_validation_too_short():
    """Test API keys that are too short are rejected."""
    manager = APIKeyManager()

    # Key too short
    is_valid, msg = manager.validate_api_key_format("short", "valid-secret-1234")
    assert is_valid is False
    assert "too short" in msg.lower()

    # Secret too short
    is_valid, msg = manager.validate_api_key_format("valid-key-123456", "short")
    assert is_valid is False
    assert "too short" in msg.lower()


def test_api_key_validation_same_key_and_secret():
    """Test API key and secret cannot be the same."""
    manager = APIKeyManager()

    same_value = "same-value-12345678"

    is_valid, msg = manager.validate_api_key_format(same_value, same_value)

    assert is_valid is False
    assert "cannot be the same" in msg.lower()


def test_api_key_validation_placeholder_values():
    """Test placeholder values are rejected."""
    manager = APIKeyManager()

    is_valid, msg = manager.validate_api_key_format(
        "your_api_key_here",
        "real-secret-123456"
    )

    assert is_valid is False
    assert "real api key" in msg.lower()


def test_api_key_validation_whitespace():
    """Test API keys with whitespace are rejected."""
    manager = APIKeyManager()

    # Key with space
    is_valid, msg = manager.validate_api_key_format(
        "key with space 123",
        "valid-secret-123456"
    )
    assert is_valid is False
    assert "cannot contain spaces" in msg.lower()

    # Secret with space
    is_valid, msg = manager.validate_api_key_format(
        "valid-key-123456",
        "secret with space"
    )
    assert is_valid is False
    assert "cannot contain spaces" in msg.lower()


def test_trading_mode_validator_no_api_keys():
    """Test live trading cannot be enabled without API keys."""
    can_enable, msg = TradingModeValidator.can_enable_live_trading(
        api_key=None,
        api_secret=None,
        user_confirmed=True
    )

    assert can_enable is False
    assert "required" in msg.lower()


def test_trading_mode_validator_no_confirmation():
    """Test live trading requires user confirmation."""
    can_enable, msg = TradingModeValidator.can_enable_live_trading(
        api_key="valid-key-123456",
        api_secret="valid-secret-123456",
        user_confirmed=False
    )

    assert can_enable is False
    assert "confirmation required" in msg.lower()


def test_trading_mode_validator_invalid_api_keys():
    """Test live trading rejects invalid API keys."""
    can_enable, msg = TradingModeValidator.can_enable_live_trading(
        api_key="short",  # Too short
        api_secret="valid-secret-123456",
        user_confirmed=True
    )

    assert can_enable is False
    assert "invalid" in msg.lower()


def test_trading_mode_validator_valid_all():
    """Test live trading can be enabled with valid credentials."""
    can_enable, msg = TradingModeValidator.can_enable_live_trading(
        api_key="valid-key-123456",
        api_secret="valid-secret-123456",
        user_confirmed=True
    )

    assert can_enable is True
    assert msg == "Live trading can be enabled"


def test_live_order_validation_negative_size():
    """Test orders with negative size are rejected."""
    is_valid, msg = TradingModeValidator.validate_live_order(
        order_size=-100.0,
        account_balance=1000.0
    )

    assert is_valid is False
    assert "positive" in msg.lower()


def test_live_order_validation_zero_size():
    """Test orders with zero size are rejected."""
    is_valid, msg = TradingModeValidator.validate_live_order(
        order_size=0.0,
        account_balance=1000.0
    )

    assert is_valid is False
    assert "positive" in msg.lower()


def test_live_order_validation_exceeds_max():
    """Test orders exceeding max size are rejected."""
    is_valid, msg = TradingModeValidator.validate_live_order(
        order_size=2000.0,
        account_balance=5000.0,
        max_order_size=1000.0
    )

    assert is_valid is False
    assert "exceeds maximum" in msg.lower()


def test_live_order_validation_insufficient_balance():
    """Test orders exceeding balance are rejected."""
    is_valid, msg = TradingModeValidator.validate_live_order(
        order_size=1500.0,
        account_balance=1000.0
    )

    assert is_valid is False
    assert "insufficient balance" in msg.lower()


def test_live_order_validation_exceeds_50_percent():
    """Test orders exceeding 50% of balance are rejected (safety)."""
    is_valid, msg = TradingModeValidator.validate_live_order(
        order_size=600.0,
        account_balance=1000.0
    )

    assert is_valid is False
    assert "50%" in msg.lower()


def test_live_order_validation_valid():
    """Test valid orders pass validation."""
    is_valid, msg = TradingModeValidator.validate_live_order(
        order_size=400.0,  # 40% of balance
        account_balance=1000.0
    )

    assert is_valid is True
    assert msg == "Order valid"


def test_production_safeguards_max_order_size():
    """Test production max order size limit."""
    # Under limit - OK
    ok, msg = ProductionSafeguards.check_order_size(4000.0)
    assert ok is True

    # At limit - OK
    ok, msg = ProductionSafeguards.check_order_size(5000.0)
    assert ok is True

    # Over limit - REJECTED
    ok, msg = ProductionSafeguards.check_order_size(5001.0)
    assert ok is False
    assert "$5" in msg or "5000" in msg


def test_production_safeguards_daily_volume():
    """Test production daily volume limit."""
    # Under limit - OK
    ok, msg = ProductionSafeguards.check_daily_volume(
        current_volume=15000.0,
        new_order=4000.0
    )
    assert ok is True

    # At limit - OK
    ok, msg = ProductionSafeguards.check_daily_volume(
        current_volume=15000.0,
        new_order=5000.0
    )
    assert ok is True

    # Over limit - REJECTED
    ok, msg = ProductionSafeguards.check_daily_volume(
        current_volume=15000.0,
        new_order=5001.0
    )
    assert ok is False
    assert "daily volume" in msg.lower()


def test_production_safeguards_limits_summary():
    """Test production limits summary contains all limits."""
    limits = ProductionSafeguards.get_limits_summary()

    assert "max_order_size" in limits
    assert "max_daily_volume" in limits
    assert "max_orders_per_minute" in limits
    assert "max_open_positions" in limits
    assert "min_order_interval" in limits

    assert limits["max_order_size"] == 5000.0
    assert limits["max_daily_volume"] == 20000.0


def test_api_key_manager_different_passwords():
    """Test different master passwords produce different encryptions."""
    manager1 = APIKeyManager(master_password="password1")
    manager2 = APIKeyManager(master_password="password2")

    api_key = "test-key-123456"

    encrypted1 = manager1.encrypt_api_key(api_key)
    encrypted2 = manager2.encrypt_api_key(api_key)

    # Different passwords should produce different ciphertexts
    # (Note: Due to Fernet's IV, they'll be different anyway, but
    # the underlying keys are different)
    assert encrypted1 != encrypted2

    # Each manager can only decrypt its own encryption
    assert manager1.decrypt_api_key(encrypted1) == api_key
    assert manager2.decrypt_api_key(encrypted2) == api_key

    # Cross-decryption should fail
    with pytest.raises(ValueError):
        manager1.decrypt_api_key(encrypted2)

    with pytest.raises(ValueError):
        manager2.decrypt_api_key(encrypted1)
