"""Password hashing and verification helpers.

We intentionally use a scheme that does not require extra C extensions
to keep installs predictable on small/private servers.
"""

from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    password = (password or "").strip()
    if not password:
        raise ValueError("Password is required")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    password = password or ""
    password_hash = password_hash or ""
    if not password or not password_hash:
        return False
    return bool(_pwd_context.verify(password, password_hash))

