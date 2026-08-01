"""add message attachments column

Revision ID: a1b2c3_add_msg_attachments
Revises: e7912d53124b
Create Date: 2026-08-01 10:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3_add_msg_attachments'
down_revision: Union[str, None] = 'e7912d53124b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('attachments', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'attachments')
