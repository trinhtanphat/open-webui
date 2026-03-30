"""add billing tables

Revision ID: d7e8f9a0b1c2
Revises: f1e2d3c4b5a6
Create Date: 2026-03-03 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from open_webui.migrations.util import get_existing_tables


revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = set(get_existing_tables())

    if "billing_payment_account" not in existing_tables:
        op.create_table(
            "billing_payment_account",
            sa.Column("id", sa.Text(), primary_key=True, nullable=False),
            sa.Column("provider", sa.Text(), nullable=False),
            sa.Column("account_name", sa.Text(), nullable=False),
            sa.Column("account_number", sa.Text(), nullable=False),
            sa.Column("qr_code_url", sa.Text(), nullable=True),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Text(), nullable=False, server_default="true"),
            sa.Column("created_by", sa.Text(), nullable=True),
            sa.Column("updated_by", sa.Text(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
        )

    if "billing_topup_request" not in existing_tables:
        op.create_table(
            "billing_topup_request",
            sa.Column("id", sa.Text(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("api_key_id", sa.Text(), nullable=False),
            sa.Column("payment_account_id", sa.Text(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.Text(), nullable=False, server_default="VND"),
            sa.Column("tx_ref", sa.Text(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
            sa.Column("reviewed_by", sa.Text(), nullable=True),
            sa.Column("reviewed_note", sa.Text(), nullable=True),
            sa.Column("reviewed_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
        )

    if "billing_invoice" not in existing_tables:
        op.create_table(
            "billing_invoice",
            sa.Column("id", sa.Text(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Text(), nullable=False),
            sa.Column("api_key_id", sa.Text(), nullable=False),
            sa.Column("topup_request_id", sa.Text(), nullable=True),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.Text(), nullable=False, server_default="VND"),
            sa.Column("credits", sa.BigInteger(), nullable=False),
            sa.Column("status", sa.Text(), nullable=False, server_default="paid"),
            sa.Column("data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
        )

    if "billing_audit_log" not in existing_tables:
        op.create_table(
            "billing_audit_log",
            sa.Column("id", sa.Text(), primary_key=True, nullable=False),
            sa.Column("actor_id", sa.Text(), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("target_type", sa.Text(), nullable=False),
            sa.Column("target_id", sa.Text(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=False),
        )


def downgrade() -> None:
    existing_tables = set(get_existing_tables())

    if "billing_audit_log" in existing_tables:
        op.drop_table("billing_audit_log")
    if "billing_invoice" in existing_tables:
        op.drop_table("billing_invoice")
    if "billing_topup_request" in existing_tables:
        op.drop_table("billing_topup_request")
    if "billing_payment_account" in existing_tables:
        op.drop_table("billing_payment_account")
