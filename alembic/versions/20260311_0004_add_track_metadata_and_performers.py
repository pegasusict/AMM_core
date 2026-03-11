"""Add track title fields and performer links.

Revision ID: 20260311_0004
Revises: 20260222_0003
Create Date: 2026-03-11 16:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260311_0004"
down_revision = "20260222_0003"
branch_labels = None
depends_on = None


def _column_exists(bind: sa.engine.Connection, table: str, column: str) -> bool:
    result = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            """
        ),
        {"table": table, "column": column},
    )
    return bool(result.scalar())


def _table_exists(bind: sa.engine.Connection, table: str) -> bool:
    result = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
            """
        ),
        {"table": table},
    )
    return bool(result.scalar())


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name not in {"mysql", "mariadb"}:
        return

    if not _column_exists(bind, "tracks", "title"):
        op.execute("ALTER TABLE tracks ADD COLUMN title varchar(255) NOT NULL DEFAULT ''")
    if not _column_exists(bind, "tracks", "subtitle"):
        op.execute("ALTER TABLE tracks ADD COLUMN subtitle varchar(255) NULL")
    if not _column_exists(bind, "tracks", "title_sort"):
        op.execute("ALTER TABLE tracks ADD COLUMN title_sort varchar(255) NOT NULL DEFAULT ''")

    if not _table_exists(bind, "track_persons"):
        op.execute(
            """
            CREATE TABLE track_persons (
                track_id INT NOT NULL,
                person_id INT NOT NULL,
                PRIMARY KEY (track_id, person_id),
                INDEX ix_track_persons_person_id (person_id),
                CONSTRAINT fk_track_persons_track_id
                    FOREIGN KEY (track_id) REFERENCES tracks (id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_track_persons_person_id
                    FOREIGN KEY (person_id) REFERENCES persons (id)
                    ON DELETE CASCADE
            )
            """
        )


def downgrade() -> None:
    # Downgrade is intentionally a no-op. Removing columns/tables may lose data.
    return
