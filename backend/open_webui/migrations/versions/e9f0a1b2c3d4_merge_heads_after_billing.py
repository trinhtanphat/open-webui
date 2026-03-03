"""merge heads after billing

Revision ID: e9f0a1b2c3d4
Revises: b2c3d4e5f6a7, d7e8f9a0b1c2
Create Date: 2026-03-03 22:30:00.000000
"""

from typing import Sequence, Union


revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, tuple[str, str], None] = ("b2c3d4e5f6a7", "d7e8f9a0b1c2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
