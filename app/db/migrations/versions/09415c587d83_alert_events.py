"""alert_events

Revision ID: 09415c587d83
Revises: 3669d14011b0
Create Date: 2025-10-12 21:38:23.785274

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09415c587d83'
down_revision: Union[str, Sequence[str], None] = '3669d14011b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "alert_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "alert_id",
            sa.Integer(),
            sa.ForeignKey("alerts.id", ondelete="CASCADE"),  # чтобы события удалялись вместе с алертом
            nullable=False,
        ),
        sa.Column("triggered_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
    )

    op.create_index(op.f("ix_alert_events_alert_id"), "alert_events", ["alert_id"], unique=False)
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_alert_events_alert_id"), table_name="alert_events")
    op.drop_table("alert_events")
    pass
