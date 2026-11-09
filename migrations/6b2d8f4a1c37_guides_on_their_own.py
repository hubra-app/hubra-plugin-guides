"""guides: a guide of its own, for an item or not

Up to 1.x a guide was one row per inventory item (``item_guides``). Now a
guide stands on its own, with a title, and may belong to an item. Every
item's guide that has text or a link is copied once, titled with the
item's name. ``item_guides`` stays for now; a later release drops it.

The qualification tables belong to the Qualifications plugin since this
release; they are left as they are for it to take over.

Revision ID: 6b2d8f4a1c37
Revises: 4d7b2f9c1a63
Create Date: 2026-11-09 16:30:00

"""

from alembic import op
import sqlalchemy as sa

from hubra.core.plugins.ops import has_table


revision = "6b2d8f4a1c37"
down_revision = "4d7b2f9c1a63"
branch_labels = None
depends_on = None


def upgrade():
    if not has_table("guides"):
        op.create_table(
            "guides",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("url", sa.String(length=500), nullable=True),
            sa.Column("item_id", sa.Integer(), nullable=True),
            sa.Column("qualification_kind_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["created_by"], ["members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_guides_item_id", "guides", ["item_id"])
    if has_table("item_guides"):
        _copy_item_guides()


def _copy_item_guides() -> None:
    # The item's name when Inventory's table is there; a plain title if not.
    if has_table("inventory_items"):
        title = "COALESCE(i.name, 'Guide')"
        join = " LEFT JOIN inventory_items i ON i.id = g.item_id"
    else:
        title, join = "'Guide'", ""
    op.get_bind().execute(
        sa.text(
            "INSERT INTO guides (title, body, url, item_id, qualification_kind_id,"
            " created_at, updated_at)"
            f" SELECT {title}, g.guide, g.guide_url, g.item_id, g.qualification_id,"
            " COALESCE(g.updated_at, CURRENT_TIMESTAMP),"
            " COALESCE(g.updated_at, CURRENT_TIMESTAMP)"
            f" FROM item_guides g{join}"
            " WHERE (g.guide IS NOT NULL OR g.guide_url IS NOT NULL)"
            " AND NOT EXISTS (SELECT 1 FROM guides x WHERE x.item_id = g.item_id)"
        )
    )


def downgrade():
    op.drop_index("ix_guides_item_id", "guides")
    op.drop_table("guides")
