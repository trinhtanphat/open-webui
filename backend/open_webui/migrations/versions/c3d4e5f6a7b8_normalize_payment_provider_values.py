"""normalize payment provider values

Revision ID: c3d4e5f6a7b8
Revises: a7b8c9d0e1f2
Create Date: 2026-03-05 23:20:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


PROVIDER_ALIASES = {
    "vng": "zalopay",
    "vngpay": "zalopay",
    "zalo": "zalopay",
    "zalo_pay": "zalopay",
    "zalo-pay": "zalopay",
    "zalopay": "zalopay",
    "vnpay": "vnpay",
    "vn_pay": "vnpay",
    "vn-pay": "vnpay",
    "momo": "momo",
    "mo_mo": "momo",
    "mo-mo": "momo",
    "paypal": "paypal",
    "pay_pal": "paypal",
    "pay-pal": "paypal",
    "bank": "bank_transfer",
    "banktransfer": "bank_transfer",
    "bank_transfer": "bank_transfer",
    "bank-transfer": "bank_transfer",
    "stripe": "stripe",
    "generic": "generic",
}


def _normalize_provider(provider: str | None) -> str:
    if not provider:
        return "generic"

    normalized = provider.strip().lower().replace(" ", "_").replace("-", "_")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch == "_")

    return PROVIDER_ALIASES.get(normalized, normalized or "generic")


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "billing_payment_account" not in inspector.get_table_names():
        return

    columns = [col["name"] for col in inspector.get_columns("billing_payment_account")]
    if "provider" not in columns:
        return

    payment_account_table = sa.table(
        "billing_payment_account",
        sa.column("id", sa.Text),
        sa.column("provider", sa.Text),
    )

    rows = conn.execute(
        sa.select(payment_account_table.c.id, payment_account_table.c.provider)
    ).fetchall()

    for account_id, provider in rows:
        normalized = _normalize_provider(provider)
        if provider != normalized:
            conn.execute(
                payment_account_table.update()
                .where(payment_account_table.c.id == account_id)
                .values(provider=normalized)
            )


def downgrade() -> None:
    # Irreversible data normalization
    pass
