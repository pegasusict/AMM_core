"""Bootstrap helpers for local-auth deployments.

This is intended for private networks where external OAuth providers
aren't available. It allows operators to seed an initial admin account
via environment variables.
"""

from __future__ import annotations

import os

from sqlmodel import select

from Singletons import DBInstance, Logger
from core.dbmodels import DBUser
from core.enums import UserRole
from .passwords import hash_password


async def ensure_bootstrap_admin(logger: Logger | None = None) -> None:
    username = (os.getenv("AMM_BOOTSTRAP_ADMIN_USERNAME") or "").strip()
    email = (os.getenv("AMM_BOOTSTRAP_ADMIN_EMAIL") or "").strip()
    password = os.getenv("AMM_BOOTSTRAP_ADMIN_PASSWORD") or ""

    if not (username and email and password):
        return

    pwd_hash = hash_password(password)

    async for session in DBInstance.get_session():
        existing = (await session.exec(select(DBUser).where(DBUser.username == username))).first()
        if not existing:
            existing = (await session.exec(select(DBUser).where(DBUser.email == email))).first()

        if not existing:
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

        changed = False
        if existing.email != email:
            existing.email = email
            changed = True
        if existing.password_hash != pwd_hash:
            existing.password_hash = pwd_hash
            changed = True
        if not existing.is_active:
            existing.is_active = True
            changed = True
        if str(existing.role).upper() != str(UserRole.ADMIN.value).upper():
            existing.role = UserRole.ADMIN
            changed = True

        if changed:
            session.add(existing)
            await session.commit()
            if logger:
                logger.info(f"Updated bootstrapped admin user '{existing.username}'.")
        return

