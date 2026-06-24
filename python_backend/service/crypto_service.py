"""
Symmetric encryption for sensitive user data (e.g. API keys stored in Supabase).

Algorithm: Fernet — AES-128-CBC + HMAC-SHA256 (authenticated encryption).
Key derivation: SHA-256 of SECRET_KEY → 32 bytes → URL-safe base64 (Fernet key format).

Usage:
    from service.crypto_service import encrypt_field, decrypt_field

    ciphertext = encrypt_field("sk-my-api-key")   # store this in DB
    plaintext  = decrypt_field(ciphertext)         # recover on read
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Sentinel prefix so we can tell encrypted values from legacy plain-text values.
_ENC_PREFIX = "enc:"


def _build_fernet() -> Fernet:
    """Derive a stable Fernet key from SECRET_KEY."""
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        raise RuntimeError("SECRET_KEY is not set — cannot encrypt/decrypt API keys")
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()  # 32 bytes
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_field(plaintext: str) -> str:
    """Encrypt *plaintext* and return a prefixed, base64 ciphertext string.

    Empty strings are returned unchanged so that clearing a field works.
    """
    if not plaintext:
        return plaintext
    try:
        token = _build_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"{_ENC_PREFIX}{token}"
    except Exception as exc:
        logger.error("Encryption failed: %s", exc)
        raise


def decrypt_field(value: str) -> str:
    """Decrypt a value previously encrypted by :func:`encrypt_field`.

    If *value* does not carry the ``enc:`` prefix it is assumed to be a legacy
    plain-text value and returned as-is (graceful migration path).
    """
    if not value:
        return value
    if not value.startswith(_ENC_PREFIX):
        # Legacy plain-text stored before encryption was introduced
        return value
    ciphertext = value[len(_ENC_PREFIX):]
    try:
        return _build_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.warning("decrypt_field: invalid token — returning raw value")
        return value
    except Exception as exc:
        logger.error("Decryption failed: %s", exc)
        return value
