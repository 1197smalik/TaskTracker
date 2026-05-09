"""Password hashing helpers using salted scrypt hashes.

This keeps password material one-way and non-deterministic without introducing
broader authentication concerns in this story.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 64
HASH_SCHEME = "scrypt"


def hash_password(password: str) -> str:
    """Hash a plaintext password with a random salt."""

    salt = secrets.token_bytes(SALT_BYTES)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_BYTES,
    )
    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_key = base64.b64encode(derived_key).decode("ascii")
    return (
        f"{HASH_SCHEME}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}$"
        f"{encoded_salt}${encoded_key}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored scrypt hash."""

    try:
        scheme, n, r, p, encoded_salt, encoded_key = password_hash.split("$")
        if scheme != HASH_SCHEME:
            return False

        salt = base64.b64decode(encoded_salt.encode("ascii"))
        expected_key = base64.b64decode(encoded_key.encode("ascii"))
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected_key),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(derived_key, expected_key)
