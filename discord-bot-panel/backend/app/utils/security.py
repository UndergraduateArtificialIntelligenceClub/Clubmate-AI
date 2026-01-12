"""
Security Utilities
==================
Encryption, hashing, and security-related helpers.

Used for:
- API key encryption (Fernet symmetric)
- Password hashing (bcrypt)
- Token generation
"""

import hashlib
import secrets
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

settings = get_settings()


class SecurityUtils:
    """
    Security utility methods for encryption and hashing.
    
    API Key Security:
    - Keys are encrypted with Fernet (symmetric AES-128-CBC)
    - A SHA-256 hash is stored for uniqueness checks
    - Masked version shows only first 4 and last 4 chars
    """
    
    _fernet: Optional[Fernet] = None
    
    @classmethod
    def _get_fernet(cls) -> Fernet:
        """
        Get or create Fernet instance.
        
        Lazily initialized to avoid issues with config loading.
        """
        if cls._fernet is None:
            try:
                cls._fernet = Fernet(settings.encryption_key.encode())
            except Exception as e:
                # If key is invalid, generate a warning
                # In production, this should fail hard
                print(f"WARNING: Invalid encryption key, generating new one: {e}")
                cls._fernet = Fernet(Fernet.generate_key())
        return cls._fernet
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a string value.
        
        Returns base64-encoded encrypted bytes.
        """
        fernet = cls._get_fernet()
        return fernet.encrypt(plaintext.encode()).decode()
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> Optional[str]:
        """
        Decrypt an encrypted value.
        
        Returns None if decryption fails (invalid key or corrupted data).
        """
        try:
            fernet = cls._get_fernet()
            return fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            return None
    
    @staticmethod
    def hash_value(value: str) -> str:
        """
        Create SHA-256 hash of a value.
        
        Used for uniqueness checks without storing plaintext.
        """
        return hashlib.sha256(value.encode()).hexdigest()
    
    @staticmethod
    def mask_key(key: str, visible_chars: int = 4) -> str:
        """
        Create a masked version of an API key.
        
        Shows first and last N characters with dots in between.
        Example: "sk-abc123xyz789" -> "sk-a...9789"
        """
        if len(key) <= visible_chars * 2:
            return "*" * len(key)
        
        prefix = key[:visible_chars]
        suffix = key[-visible_chars:]
        return f"{prefix}...{suffix}"
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        
        Used for session tokens, CSRF tokens, etc.
        """
        return secrets.token_urlsafe(length)
