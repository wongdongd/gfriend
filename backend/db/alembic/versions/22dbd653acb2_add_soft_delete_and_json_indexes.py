"""add soft_delete, json fields, and composite indexes

Revision ID: 22dbd653acb2
Revises: a1b2c3_add_msg_attachments
Create Date: 2026-08-02 10:03:30.453953

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '22dbd653acb2'
down_revision: Union[str, None] = 'a1b2c3_add_msg_attachments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- assets: soft delete column ---
    op.add_column('assets', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # --- json field migrations ---
    op.execute(
        "ALTER TABLE users ALTER COLUMN notification_prefs TYPE jsonb USING "
        "CASE WHEN notification_prefs IS NULL THEN NULL "
        "ELSE notification_prefs::jsonb END"
    )
    op.execute(
        "ALTER TABLE templates ALTER COLUMN display_config TYPE jsonb USING display_config::jsonb"
    )
    op.execute(
        "ALTER TABLE subscriptions ALTER COLUMN entitlements TYPE jsonb USING "
        "CASE WHEN entitlements IS NULL THEN NULL "
        "ELSE entitlements::jsonb END"
    )
    op.execute(
        "ALTER TABLE memories ALTER COLUMN detail TYPE jsonb USING "
        "CASE WHEN detail IS NULL THEN NULL "
        "ELSE detail::jsonb END"
    )
    op.execute(
        "ALTER TABLE memories ALTER COLUMN scope TYPE jsonb USING "
        "CASE WHEN scope IS NULL THEN NULL "
        "ELSE scope::jsonb END"
    )
    op.execute(
        "ALTER TABLE characters ALTER COLUMN interaction_bounds TYPE jsonb USING "
        "CASE WHEN interaction_bounds IS NULL THEN NULL "
        "ELSE interaction_bounds::jsonb END"
    )
    op.execute(
        "ALTER TABLE characters ALTER COLUMN model_params TYPE jsonb USING "
        "CASE WHEN model_params IS NULL THEN NULL "
        "ELSE model_params::jsonb END"
    )
    op.execute(
        "ALTER TABLE conversations ALTER COLUMN quick_topics TYPE jsonb USING "
        "CASE WHEN quick_topics IS NULL THEN NULL "
        "ELSE quick_topics::jsonb END"
    )
    # messages.attachments was previously TEXT, migrate to JSONB
    op.execute(
        "ALTER TABLE messages ALTER COLUMN attachments TYPE jsonb USING "
        "CASE WHEN attachments IS NULL THEN NULL "
        "ELSE attachments::jsonb END"
    )

    # --- composite indexes ---
    op.create_index(
        'ix_messages_conversation_created', 'messages',
        ['conversation_id', 'created_at'], unique=False,
    )
    op.create_index(
        'ix_gen_tasks_status_priority', 'generation_tasks',
        ['status', 'priority'], unique=False,
    )
    op.create_index(
        'ix_credit_ledger_user_created', 'credit_ledger',
        ['user_id', 'created_at'], unique=False,
    )
    op.create_index(
        'ix_conversations_char_lastmsg', 'conversations',
        ['character_id', 'last_message_at'], unique=False,
    )
    op.create_index(
        'ix_outbox_pending', 'outbox_events',
        ['is_published', 'created_at'], unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_outbox_pending', table_name='outbox_events')
    op.drop_index('ix_conversations_char_lastmsg', table_name='conversations')
    op.drop_index('ix_credit_ledger_user_created', table_name='credit_ledger')
    op.drop_index('ix_gen_tasks_status_priority', table_name='generation_tasks')
    op.drop_index('ix_messages_conversation_created', table_name='messages')

    op.execute("ALTER TABLE messages ALTER COLUMN attachments TYPE text USING attachments::text")
    op.execute(
        "ALTER TABLE conversations ALTER COLUMN quick_topics TYPE text USING quick_topics::text"
    )
    op.execute(
        "ALTER TABLE characters ALTER COLUMN model_params TYPE text USING model_params::text"
    )
    op.execute(
        "ALTER TABLE characters ALTER COLUMN interaction_bounds TYPE text USING interaction_bounds::text"
    )
    op.execute("ALTER TABLE memories ALTER COLUMN scope TYPE text USING scope::text")
    op.execute("ALTER TABLE memories ALTER COLUMN detail TYPE text USING detail::text")
    op.execute(
        "ALTER TABLE subscriptions ALTER COLUMN entitlements TYPE text USING entitlements::text"
    )
    op.execute(
        "ALTER TABLE templates ALTER COLUMN display_config TYPE text USING display_config::text"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN notification_prefs TYPE text USING notification_prefs::text"
    )

    op.drop_column('assets', 'deleted_at')
