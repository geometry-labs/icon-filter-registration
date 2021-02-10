"""baseline

Revision ID: 5bbb66a12c24
Revises:
Create Date: 2021-02-10 18:39:35.000498

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5bbb66a12c24"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "broadcasters",
        sa.Column("broadcaster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("broadcaster_id"),
        sa.UniqueConstraint("broadcaster_id"),
    )
    op.create_table(
        "event_registrations",
        sa.Column("reg_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("from_address", sa.String(), nullable=True),
        sa.Column("to_address", sa.String(), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("keyword", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("reg_id"),
    )
    op.create_table(
        "broadcaster_registrations",
        sa.Column("reg_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broadcaster_id", postgresql.UUID(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("last_used", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["broadcaster_id"],
            ["broadcasters.broadcaster_id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event_registrations.reg_id"],
        ),
        sa.PrimaryKeyConstraint("reg_id"),
        sa.UniqueConstraint("reg_id"),
    )


def downgrade():
    op.drop_table("broadcaster_registrations")
    op.drop_table("event_registrations")
    op.drop_table("broadcasters")


d
