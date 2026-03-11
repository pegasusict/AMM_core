"""Bootstrap helpers for local-auth deployments.

This is intended for private networks where external OAuth providers
aren't available. It allows operators to seed an initial admin account
via environment variables.
"""

from __future__ import annotations

import os

from typing import Any

from sqlmodel import select

from Singletons import DBInstance, Logger
from core.dbmodels import DBUser
from core.enums import UserRole
from .passwords import hash_password


def _bootstrap_credentials() -> tuple[str, str, str] | None:
    username = (os.getenv("AMM_BOOTSTRAP_ADMIN_USERNAME") or "").strip()
    email = (os.getenv("AMM_BOOTSTRAP_ADMIN_EMAIL") or "").strip()
    password = os.getenv("AMM_BOOTSTRAP_ADMIN_PASSWORD") or ""
    if not (username and email and password):
        return None
    return username, email, password


async def _find_user(session: Any, *, username: str, email: str) -> DBUser | None:
    existing = (await session.exec(select(DBUser).where(DBUser.username == username))).first()
    if existing:
        return existing
    return (await session.exec(select(DBUser).where(DBUser.email == email))).first()


def _set_if_different(obj: Any, attr: str, value: Any) -> bool:
    if getattr(obj, attr) == value:
        return False
    setattr(obj, attr, value)
    return True


def _is_admin_role(role: Any) -> bool:
    return str(role).upper() == str(UserRole.ADMIN.value).upper()


def _apply_bootstrap_updates(user: DBUser, *, email: str, pwd_hash: str) -> bool:
    changed = False
    changed |= _set_if_different(user, "email", email)
    changed |= _set_if_different(user, "password_hash", pwd_hash)
    changed |= _set_if_different(user, "is_active", True)
    if not _is_admin_role(user.role):
        user.role = UserRole.ADMIN
        changed = True
    return changed


async def ensure_bootstrap_admin(logger: Logger | None = None) -> None:
    creds = _bootstrap_credentials()
    if not creds:
        return
    username, email, password = creds

    pwd_hash = hash_password(password)

    async for session in DBInstance.get_session():
        existing = await _find_user(session, username=username, email=email)
        if existing is None:
            user = DBUser(
                username=username,
                email=email,
                password_hash=pwd_hash,
                first_name="",
                middle_name="",
                last_name="",
                is_active=True,
                role=UserRole.ADMIN,
            )
            session.add(user)
            await session.commit()
            if logger:
                logger.info(f"Bootstrapped admin user '{username}'.")
            return

        changed = _apply_bootstrap_updates(existing, email=email, pwd_hash=pwd_hash)

        if changed:
            session.add(existing)
            await session.commit()
            if logger:
                logger.info(f"Updated bootstrapped admin user '{existing.username}'.")
        return
