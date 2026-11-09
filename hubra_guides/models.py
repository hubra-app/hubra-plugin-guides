"""A guide: a how-to in Markdown and/or a link to a manual or video."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from hubra.core.extensions import db


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Guide(db.Model):
    """How to use a machine or tool, or how to do something in the club
    ("Lock up the clubhouse"). It may belong to an inventory item.

    The item and the qualification it takes belong to other plugins
    (Inventory, Qualifications), so only their ids are kept, without a
    foreign key; names come from their queries.
    """

    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(db.String(500), nullable=True)
    item_id: Mapped[int | None] = mapped_column(db.Integer, nullable=True, index=True)
    qualification_kind_id: Mapped[int | None] = mapped_column(db.Integer, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        db.Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=False
    )
