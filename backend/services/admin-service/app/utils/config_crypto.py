"""Encryption for system config secret values."""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken


def _get_fernet_key(encryption_key: str | None, fallback_secret: str) -> bytes:
    """Get Fernet key from env or derive from fallback."""
    raw = encryption_key or os.environ.get("SYSTEM_CONFIG_ENCRYPTION_KEY")
    if raw and len(raw) >= 16:
        return base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    return base64.urlsafe_b64encode(hashlib.sha256(fallback_secret.encode()).digest())


ENCRYPTED_PREFIX = "fernet:"


def encrypt_value(plain: str, encryption_key: str | None = None, fallback: str = "change-me") -> str:
    """Encrypt a secret value. Returns ENCRYPTED_PREFIX + base64 string."""
    key = _get_fernet_key(encryption_key, fallback)
    f = Fernet(key)
    return ENCRYPTED_PREFIX + f.encrypt(plain.encode()).decode()


def decrypt_value(stored: str, encryption_key: str | None = None, fallback: str = "change-me") -> str | None:
    """Decrypt a secret value. If not encrypted (no prefix), returns as-is. Returns None if decrypt fails."""
    if not stored.startswith(ENCRYPTED_PREFIX):
        return stored
    try:
        key = _get_fernet_key(encryption_key, fallback)
        f = Fernet(key)
        return f.decrypt(stored[len(ENCRYPTED_PREFIX) :].encode()).decode()
    except (InvalidToken, Exception):
        return None


def mask_secret(value: str, visible_tail: int = 4) -> str:
    """Mask secret for display. Shows last N chars."""
    if not value:
        return "****"
    if len(value) <= visible_tail:
        return "****"
    return "*" * (len(value) - visible_tail) + value[-visible_tail:]
