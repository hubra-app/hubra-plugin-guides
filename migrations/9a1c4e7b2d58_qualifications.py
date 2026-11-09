"""qualification_kinds, member_qualifications, item_guides.qualification_id

Revision ID: 9a1c4e7b2d58
Revises: 57ed5a04682e
Create Date: 2026-11-05 17:00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9a1c4e7b2d58"
down_revision = "57ed5a04682e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "qualification_kinds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("valid_months", sa.Integer(), nullable=True),
        sa.Column("remind_days", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "member_qualifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("kind_id", sa.Integer(), nullable=False),
        sa.Column("obtained_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["kind_id"], ["qualification_kinds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id", "kind_id", name="uq_member_qualification"),
    )
    with op.batch_alter_table("member_qualifications", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_member_qualifications_member_id"), ["member_id"]
        )
        batch_op.create_index(
            batch_op.f("ix_member_qualifications_kind_id"), ["kind_id"]
        )
    with op.batch_alter_table("item_guides", schema=None) as batch_op:
        batch_op.add_column(sa.Column("qualification_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_item_guides_qualification",
            "qualification_kinds",
            ["qualification_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("item_guides", schema=None) as batch_op:
        batch_op.drop_constraint("fk_item_guides_qualification", type_="foreignkey")
        batch_op.drop_column("qualification_id")
    # The qualification tables belong to the Qualifications plugin since
    # Guides 2.0: removing Guides must never take them with it.
