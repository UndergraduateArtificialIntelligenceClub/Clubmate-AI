import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .config import settings

if not settings.AES_MASTER_KEY:
    # Fallback for dev if not set, DO NOT USE IN PROD
    print("WARNING: AES_MASTER_KEY not set")
    MASTER_KEY = os.urandom(32)
else:
    MASTER_KEY = base64.urlsafe_b64decode(settings.AES_MASTER_KEY)


def encrypt_value(plaintext: str) -> tuple[bytes, bytes, bytes]:
    aesgcm = AESGCM(MASTER_KEY)
    nonce = os.urandom(12)
    # encrypt returns ciphertext + tag
    full = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    tag = full[-16:]
    ciphertext = full[:-16]
    return ciphertext, nonce, tag


def decrypt_value(ciphertext: bytes, nonce: bytes, tag: bytes) -> str:
    aesgcm = AESGCM(MASTER_KEY)
    full = ciphertext + tag
    return aesgcm.decrypt(nonce, full, None).decode("utf-8")
