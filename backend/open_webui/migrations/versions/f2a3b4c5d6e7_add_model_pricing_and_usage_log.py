"""add model_pricing and usage_log tables

Revision ID: f2a3b4c5d6e7
Revises: e9f0a1b2c3d4
Create Date: 2026-03-03

"""

from alembic import op
import sqlalchemy as sa

revision = "f2a3b4c5d6e7"
down_revision = "e9f0a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = inspector.get_table_names()

    if "model_pricing" not in existing:
        op.create_table(
            "model_pricing",
            sa.Column("id", sa.Text(), primary_key=True, unique=True),
            sa.Column("model_id", sa.Text(), nullable=False, unique=True),
            sa.Column("display_name", sa.Text(), nullable=True),
            sa.Column("input_cost_per_1k_tokens", sa.Float(), nullable=False, server_default="0"),
            sa.Column("output_cost_per_1k_tokens", sa.Float(), nullable=False, server_default="0"),
            sa.Column("per_request_cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("currency", sa.Text(), nullable=False, server_default="USD"),
            sa.Column("is_active", sa.Text(), nullable=False, server_default="true"),
            sa.Column("created_by", sa.Text(), nullable=True),
            sa.Column("updated_by", sa.Text(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
        )

    if "usage_log" not in existing:
        op.create_table(
            "usage_log",
            sa.Column("id", sa.Text(), primary_key=True, unique=True),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("api_key_id", sa.Text(), nullable=False),
            sa.Column("model", sa.Text(), nullable=False),
            sa.Column("endpoint", sa.Text(), nullable=True),
            sa.Column("prompt_tokens", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("completion_tokens", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("total_tokens", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("input_cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("output_cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("total_cost", sa.Float(), nullable=False, server_default="0"),
            sa.Column("credits_deducted", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("currency", sa.Text(), nullable=False, server_default="USD"),
            sa.Column("request_metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
        )


def downgrade():
    op.drop_table("usage_log")
    op.drop_table("model_pricing")
