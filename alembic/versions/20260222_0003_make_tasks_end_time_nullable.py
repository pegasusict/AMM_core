"""Make tasks.end_time nullable.

Revision ID: 20260222_0003
Revises: 20260222_0002
Create Date: 2026-02-22 16:50:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260222_0003"
down_revision = "20260222_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name in {"mysql", "mariadb"}:
        op.execute("ALTER TABLE tasks MODIFY end_time datetime NULL")


def downgrade() -> None:
    # Downgrade is intentionally a no-op:
    # restoring NOT NULL could fail once NULL values exist.
    return

