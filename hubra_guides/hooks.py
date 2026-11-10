"""What Guides does when Inventory tells it something (docs/contracts.md)."""

from __future__ import annotations

from sqlalchemy import update

from hubra.core.extensions import db

from .models import Guide


def on_item_deleted(tenant_id, item_id: int) -> None:
    """A guide outlives its item: it just no longer belongs to one."""
    db.session.execute(
        update(Guide).where(Guide.item_id == item_id).values(item_id=None)
    )
