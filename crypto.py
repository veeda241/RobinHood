"""
RobinHood AI - Cryptographic Layer

Application-level field encryption for PII at rest, plus a blind-search index
for the PAN. Design points (defensible in a patent/publication context):

  * Per-field key derivation. A single leaked master key does NOT decrypt every
    column: the effective Fernet key for a column is HKDF(master, field_name),
    so `name` and `pan` ciphertexts are produced under independent keys.
  * Blind index for the PAN. Fernet is randomized (a fresh IV/timestamp per
    call), so ciphertext cannot be used in an equality lookup. We store
    HMAC-SHA256(pepper, PAN) in `pan_blind_index` for deterministic search
    without ever storing the PAN in plaintext.

If CRYPTO_KEY is absent from the environment (local dev / offline demo), a
clearly-labelled insecure dev key is derived so the pipeline stays runnable.
This MUST be replaced by a real key in production (see .env.example).
"""

import os
import base64
import hashlib
import hmac

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# --- Master key loading -------------------------------------------------------

_DEV_FALLBACK_WARNING = (
    "crypto.py: CRYPTO_KEY not set - using INSECURE development key. "
    "Never use this in production."
)


def _load_master_key() -> bytes:
    key = os.getenv("CRYPTO_KEY")
    if key:
        # Validate it is a usable Fernet key (raises otherwise).
        Fernet(key.encode() if isinstance(key, str) else key)
        return key.encode() if isinstance(key, str) else key
    print(_DEV_FALLBACK_WARNING)
    return base64.urlsafe_b64encode(
        hashlib.sha256(b"ROBINHOOD_INSECURE_DEV_FALLBACK_KEY").digest()
    )


_MASTER_KEY = _load_master_key()
_KEY_CACHE: dict[str, Fernet] = {}


def _fernet_for_field(field_name: str) -> Fernet:
    """Derive an independent Fernet key per protected field from the master key."""
    if field_name not in _KEY_CACHE:
        derived = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"robinhood-field-encryption-v1",
            info=field_name.encode("utf-8"),
        ).derive(_MASTER_KEY)
        _KEY_CACHE[field_name] = Fernet(base64.urlsafe_b64encode(derived))
    return _KEY_CACHE[field_name]


# --- Encrypt / decrypt --------------------------------------------------------

def encrypt_field(field_name: str, plaintext) -> str:
    """Encrypt a single PII value under the field's derived key.

    None / empty passes through as None so optional columns stay NULL.
    """
    if plaintext is None:
        return None
    if isinstance(plaintext, (int, float)):
        plaintext = str(plaintext)
    return _fernet_for_field(field_name).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_field(field_name: str, token) -> str | None:
    """Decrypt a field token back to plaintext. Returns None for NULL/empty."""
    if not token:
        return None
    return _fernet_for_field(field_name).decrypt(token.encode("utf-8")).decode("utf-8")


# --- Blind search index -------------------------------------------------------

def _pepper() -> bytes:
    pepper = os.getenv("PAN_BLIND_INDEX_PEPPER")
    if pepper:
        return pepper.encode("utf-8")
    # Deterministic dev pepper so local search still works. Insecure; must set
    # PAN_BLIND_INDEX_PEPPER in production.
    return b"ROBINHOOD_DEV_PEPPER"


def pan_blind_index(pan: str | None) -> str | None:
    """HMAC-SHA256(pepper, normalized PAN) -> lowercase hex.

    Deterministic: the same PAN always maps to the same index, enabling
    equality lookups on encrypted-at-rest PANs without decrypting anything.
    """
    if not pan:
        return None
    normalized = pan.strip().upper()
    return hmac.new(_pepper(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()
