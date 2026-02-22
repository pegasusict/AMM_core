"""Make users.date_of_birth nullable.

Revision ID: 20260222_0002
Revises: 20260219_0001
Create Date: 2026-02-22 16:45:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260222_0002"
down_revision = "20260219_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name in {"mysql", "mariadb"}:
        op.execute("ALTER TABLE users MODIFY date_of_birth datetime NULL")


def downgrade() -> None:
    # Downgrade is intentionally a no-op:
    # restoring NOT NULL could fail if NULL values exist.
    return

