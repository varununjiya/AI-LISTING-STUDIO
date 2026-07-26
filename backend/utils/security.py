"""Security & Encryption Utility for Sensitive Marketplace Credentials.

Uses Fernet symmetric encryption to encrypt access tokens, refresh tokens, and client secrets.
Never exposes raw credentials to the frontend.
"""
from __future__ import annotations

import os
import base64
import logging
from typing import Dict, Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("security_utils")

# Get or derive master encryption key
_RAW_KEY = os.getenv("ENCRYPTION_KEY", "ai-listing-studio-default-secret-key-2026")

def _get_fernet_key(secret: str) -> bytes:
    """Derive a valid 32-byte url-safe base64 key from any string."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ai_listing_studio_salt_v1",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode("utf-8")))
    return key

_FERNET = Fernet(_get_fernet_key(_RAW_KEY))


def encrypt_token(plain_text: Optional[str]) -> str:
    """Encrypt a sensitive token or secret string."""
    if not plain_text:
        return ""
    try:
        return _FERNET.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error("Encryption failed: %s", e)
        return plain_text


def decrypt_token(cipher_text: Optional[str]) -> str:
    """Decrypt an encrypted token or secret string."""
    if not cipher_text:
        return ""
    try:
        return _FERNET.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        # If decryption fails (e.g. legacy plain text), return as-is
        return cipher_text


def sanitize_marketplace_connection(conn: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize connection dictionary for frontend safety."""
    sanitized = {**conn}
    # Remove sensitive fields
    sanitized.pop("access_token", None)
    sanitized.pop("refresh_token", None)
    sanitized.pop("client_secret", None)
    sanitized.pop("api_secret", None)
    sanitized.pop("_id", None)
    
    # Indicate if credentials are present
    sanitized["has_credentials"] = True
    return sanitized
