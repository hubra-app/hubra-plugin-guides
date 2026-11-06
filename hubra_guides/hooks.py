"""What Guides does when Inventory tells it something (docs/contracts.md)."""

from __future__ import annotations

from hubra.core.extensions import db

from .models import ItemGuide


def on_item_deleted(tenant_id, item_id: int) -> None:
    """A deleted item's guide goes with it."""
    row = db.session.get(ItemGuide, item_id)
    if row is not None:
        db.session.delete(row)
