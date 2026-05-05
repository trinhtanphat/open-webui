"""merge chat/calendar and api key migration heads

Revision ID: f6a7b8c9d0e1
Revises: 56359461a091, d5e6f7a8b9c0
Create Date: 2026-05-05 12:00:00.000000

"""

from typing import Sequence, Union


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, tuple[str, str], None] = ('56359461a091', 'd5e6f7a8b9c0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass