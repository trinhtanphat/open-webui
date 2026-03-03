"""add api_key key_hash column and backfill

Revision ID: a7b8c9d0e1f2
Revises: f2a3b4c5d6e7
Create Date: 2025-01-01 00:00:00.000000

"""

import hashlib
from alembic import op
import sqlalchemy as sa

revision = "a7b8c9d0e1f2"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _prefix(key: str) -> str:
    return key[:10] if len(key) > 10 else key


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Add key_hash column if it doesn't exist
    columns = [col["name"] for col in inspector.get_columns("api_key")]
    if "key_hash" not in columns:
        op.add_column("api_key", sa.Column("key_hash", sa.Text(), nullable=True))

    # 2. Backfill: hash existing plain-text keys, replace key with prefix
    api_key_table = sa.table(
        "api_key",
        sa.column("id", sa.Text),
        sa.column("key", sa.Text),
        sa.column("key_hash", sa.Text),
    )

    rows = conn.execute(
        sa.select(api_key_table.c.id, api_key_table.c.key).where(
            api_key_table.c.key_hash.is_(None)
        )
    ).fetchall()

    for row in rows:
        key_id, plain_key = row
        if plain_key:
            conn.execute(
                api_key_table.update()
                .where(api_key_table.c.id == key_id)
                .values(
                    key_hash=_hash_key(plain_key),
                    key=_prefix(plain_key),
                )
            )

    # 3. Create unique index on key_hash
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("api_key")]
    if "ix_api_key_key_hash" not in existing_indexes:
        op.create_index("ix_api_key_key_hash", "api_key", ["key_hash"], unique=True)


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_indexes = [idx["name"] for idx in inspector.get_indexes("api_key")]
    if "ix_api_key_key_hash" in existing_indexes:
        op.drop_index("ix_api_key_key_hash", table_name="api_key")

    columns = [col["name"] for col in inspector.get_columns("api_key")]
    if "key_hash" in columns:
        op.drop_column("api_key", "key_hash")
