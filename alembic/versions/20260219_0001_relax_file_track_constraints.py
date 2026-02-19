"""Relax file/track constraints and backfill placeholder tracks.

Revision ID: 20260219_0001
Revises:
Create Date: 2026-02-19 16:05:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260219_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name not in {"mysql", "mariadb"}:
        return

    statements = [
        "ALTER TABLE files MODIFY processed datetime NULL",
        "ALTER TABLE files MODIFY bitrate int(11) NULL",
        "ALTER TABLE files MODIFY sample_rate int(11) NULL",
        "ALTER TABLE files MODIFY channels int(11) NULL",
        "ALTER TABLE files MODIFY file_type varchar(20) NULL",
        "ALTER TABLE files MODIFY file_size int(11) NULL",
        "ALTER TABLE files MODIFY file_name varchar(255) NULL",
        "ALTER TABLE files MODIFY file_extension varchar(16) NULL",
        "ALTER TABLE files MODIFY duration int(11) NULL",
        "ALTER TABLE files MODIFY track_id int(11) NULL",
        "ALTER TABLE files MODIFY task_id int(11) NULL",
        "ALTER TABLE files MODIFY batch_id int(11) NULL",
        "ALTER TABLE tracks MODIFY task_id int(11) NULL",
        """
        INSERT INTO tracks (composed, release_date, mbid, task_id)
        SELECT '1000-01-01', '1000-01-01',
               CONCAT('local_', LPAD(f.id, 34, '0')),
               NULL
        FROM files f
        LEFT JOIN tracks t
          ON t.mbid = CONCAT('local_', LPAD(f.id, 34, '0'))
        WHERE f.track_id IS NULL
          AND t.id IS NULL
        """,
        """
        UPDATE files f
        JOIN tracks t
          ON t.mbid = CONCAT('local_', LPAD(f.id, 34, '0'))
        SET f.track_id = t.id
        WHERE f.track_id IS NULL
        """,
    ]

    for stmt in statements:
        op.execute(stmt)


def downgrade() -> None:
    # Downgrade is intentionally a no-op:
    # restoring stricter NOT NULL constraints is unsafe once NULL data exists.
    return

