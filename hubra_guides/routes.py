"""Guides blueprint: /api/v1/guides/<item_id>.

The guide lives in this plugin's own table (``item_guides``), one row per
inventory item, so it stays when the module is switched off and on again.
Items come from Inventory's query ``inventory.items.get`` (docs/contracts.md
in hubra-app/hubra), never from its tables or code.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from hubra.api.auth.helpers import get_current_member
from hubra.api.permissions import permission_required
from hubra.api.utils import log_audit
from hubra.core.errors import api_error, raise_error
from hubra.core.extensions import db

from hubra.core.contracts import SYSTEM, ActionFailed, ActionUnavailable, query

from .models import ItemGuide

guides_bp = Blueprint("guides_bp", __name__)

_MAX_GUIDE = 100_000
_ITEMS = "inventory.items.get"
_BATCH = 500  # the most ids the query takes at once


def _items(ids) -> dict[int, dict]:
    """The live inventory items with these ids, by id (deleted ones left out)."""
    ids = list(dict.fromkeys(ids))
    out: dict[int, dict] = {}
    for start in range(0, len(ids), _BATCH):
        try:
            # Guides checks its own rights; Inventory's read right isn't needed.
            rows = query(_ITEMS, ids=ids[start : start + _BATCH], actor=SYSTEM)
        except (ActionUnavailable, ActionFailed):
            return {}
        out.update({row["id"]: row for row in rows})
    return out


def _to_dict(item: dict, guide: ItemGuide | None) -> dict:
    return {
        "itemId": item["id"],
        "itemName": item["name"],
        "guide": (guide.guide if guide else None) or "",
        "guideUrl": guide.guide_url if guide else None,
        "instructionRequired": bool(item.get("instruction_required")),
    }


@guides_bp.get("/")
@permission_required("guides", "read", "Read guides")
def list_guides():
    guides = db.session.scalars(
        select(ItemGuide).where(
            (ItemGuide.guide.isnot(None)) | (ItemGuide.guide_url.isnot(None))
        )
    ).all()
    items = _items(g.item_id for g in guides)
    rows = [(items[g.item_id], g) for g in guides if g.item_id in items]
    rows.sort(key=lambda pair: (pair[0]["name"].casefold(), pair[0]["id"]))
    return jsonify([_to_dict(item, guide) for item, guide in rows]), 200


def _live_item(item_id: int):
    """The item, or 404 when there is none or it is deleted."""
    item = _items([item_id]).get(item_id)
    if item is None:
        raise_error(404, "NOT_FOUND", f"Item {item_id} not found")
    return item


@guides_bp.get("/<int:item_id>")
@permission_required("guides", "read", "Read guides")
def get_guide(item_id: int):
    item = _live_item(item_id)
    return jsonify(_to_dict(item, db.session.get(ItemGuide, item["id"]))), 200


@guides_bp.put("/<int:item_id>")
@permission_required("guides", "write", "Write guides")
def save_guide(item_id: int):
    body = request.get_json(silent=True) or {}
    guide = body.get("guide")
    url = body.get("guide_url")
    if guide is not None and not isinstance(guide, str):
        return api_error("VALIDATION_ERROR", "guide must be text", 400)
    if guide and len(guide) > _MAX_GUIDE:
        return api_error("VALIDATION_ERROR", "guide is too long", 400)
    if url:
        if not isinstance(url, str) or not url.startswith("https://"):
            return api_error(
                "VALIDATION_ERROR", "guide_url must start with https://", 400
            )
        if len(url) > 500:
            return api_error("VALIDATION_ERROR", "guide_url is too long", 400)
    item = _live_item(item_id)
    row = db.session.get(ItemGuide, item["id"])
    if row is None:
        row = ItemGuide(item_id=item["id"])
        db.session.add(row)
    if "guide" in body:
        row.guide = (guide or "").strip() or None
    if "guide_url" in body:
        row.guide_url = (url or "").strip() or None
    log_audit(
        get_current_member().id,
        "update_guide",
        "InventoryItem",
        item["id"],
        item["name"],
    )
    db.session.commit()
    return jsonify(_to_dict(item, row)), 200
