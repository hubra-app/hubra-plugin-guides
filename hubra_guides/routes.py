"""Guides blueprint: /api/v1/guides.

GET    /guides/                    ?q=&itemId=  every guide (title, item, preview)
POST   /guides/                    {title, guide?, guideUrl?, itemId?, qualificationId?}
GET    /guides/<id>
PATCH  /guides/<id>                the fields given
DELETE /guides/<id>
GET    /guides/items               ?q=  inventory items to pick from
GET    /guides/qualification-kinds the qualifications a guide can name

A guide is a how-to: for a machine or tool, or for anything else the club
does ("Lock up the clubhouse"). It may belong to an inventory item and may
name the qualification it takes. Both come from the other plugins' queries
(Inventory: ``inventory.items.get``/``list``; Qualifications:
``qualifications.kinds.list``/``member.holds``), never their tables or
code; without them a guide simply has no item or qualification.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import or_, select

from hubra.core.auth.helpers import get_current_member
from hubra.core.contracts import SYSTEM, ActionFailed, ActionUnavailable, query
from hubra.core.errors import api_error, raise_error
from hubra.core.extensions import db
from hubra.core.permissions import permission_required
from hubra.core.utils import log_audit

from .models import Guide

guides_bp = Blueprint("guides_bp", __name__)

MAX_BODY = 100_000
MAX_TITLE = 200
ITEMS_GET = "inventory.items.get"
ITEMS_LIST = "inventory.items.list"
KINDS = "qualifications.kinds.list"
HOLDS = "qualifications.member.holds"
_BATCH = 500  # the most ids the item query takes at once


def _ask(name: str, **data) -> list[dict] | None:
    """Ask another plugin; ``None`` when it isn't there or is switched off.

    Guides checks its own rights, so it asks as the system.
    """
    try:
        return query(name, actor=SYSTEM, **data)
    except (ActionUnavailable, ActionFailed):
        return None


def _items(ids) -> dict[int, dict]:
    """The live inventory items with these ids, by id."""
    ids = [i for i in dict.fromkeys(ids) if i]
    out: dict[int, dict] = {}
    for start in range(0, len(ids), _BATCH):
        rows = _ask(ITEMS_GET, ids=ids[start : start + _BATCH]) or []
        out.update({row["id"]: row for row in rows})
    return out


def _qualification(kind_id: int | None) -> dict | None:
    """The qualification the guide takes, and whether the reader holds it."""
    if not kind_id:
        return None
    kinds = _ask(KINDS, ids=[kind_id])
    if not kinds:
        return None
    member = get_current_member()
    mine = None
    if member is not None:
        held = _ask(HOLDS, member_id=member.id, kind_ids=[kind_id]) or []
        mine = next((h.get("state") for h in held if h["kind_id"] == kind_id), None)
    return {"id": kind_id, "name": kinds[0]["name"], "mine": mine}


def _preview(body: str | None) -> str:
    """The first lines of text, without Markdown headings."""
    for line in (body or "").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line[:200]
    return ""


def _summary(g: Guide, item: dict | None) -> dict:
    return {
        "id": g.id,
        "title": g.title,
        "itemId": item["id"] if item else None,
        "itemName": item["name"] if item else None,
        "preview": _preview(g.body),
        "hasText": bool(g.body),
        "guideUrl": g.url,
        "updatedAt": g.updated_at.isoformat() if g.updated_at else None,
    }


def _full(g: Guide) -> dict:
    item = _items([g.item_id]).get(g.item_id) if g.item_id else None
    return {
        **_summary(g, item),
        "guide": g.body or "",
        "instructionRequired": bool(item and item.get("instruction_required")),
        "qualification": _qualification(g.qualification_kind_id),
    }


def _get(guide_id: int) -> Guide:
    g = db.session.get(Guide, guide_id)
    if g is None:
        raise_error(404, "NOT_FOUND", f"Guide {guide_id} not found")
    return g  # type: ignore[return-value]


@guides_bp.get("/")
@permission_required("guides", "read", "Read guides")
def list_guides():
    stmt = select(Guide)
    q = (request.args.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Guide.title.ilike(like), Guide.body.ilike(like)))
    item_id = request.args.get("itemId", type=int)
    if item_id is not None:
        stmt = stmt.where(Guide.item_id == item_id)
    guides = db.session.scalars(stmt).all()
    items = _items(g.item_id for g in guides)
    rows = [_summary(g, items.get(g.item_id)) for g in guides]  # type: ignore[arg-type]
    rows.sort(key=lambda r: (r["title"].casefold(), r["id"]))
    return jsonify(rows), 200


@guides_bp.get("/<int:guide_id>")
@permission_required("guides", "read", "Read guides")
def get_guide(guide_id: int):
    return jsonify(_full(_get(guide_id))), 200


def _read(g: Guide, body: dict) -> str | None:
    """Apply the fields in *body*; an error message, or ``None``."""
    if "title" in body or g.id is None:
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            return "title is required"
        if len(title.strip()) > MAX_TITLE:
            return "title is too long"
        g.title = title.strip()
    if "guide" in body:
        text = body.get("guide")
        if text is not None and not isinstance(text, str):
            return "guide must be text"
        if text and len(text) > MAX_BODY:
            return "guide is too long"
        g.body = (text or "").strip() or None
    if "guideUrl" in body:
        url = body.get("guideUrl")
        if url:
            if not isinstance(url, str) or not url.startswith("https://"):
                return "guideUrl must start with https://"
            if len(url) > 500:
                return "guideUrl is too long"
        g.url = (url or "").strip() or None
    if "itemId" in body:
        item_id = body.get("itemId")
        if item_id is not None and (
            not isinstance(item_id, int)
            or isinstance(item_id, bool)
            or item_id not in _items([item_id])
        ):
            return "itemId must be an inventory item"
        g.item_id = item_id
    if "qualificationId" in body:
        qid = body.get("qualificationId")
        # Only the club's own qualifications, never self-service ones.
        if qid is not None and (
            not isinstance(qid, int)
            or isinstance(qid, bool)
            or not _ask(KINDS, ids=[qid])
        ):
            return "qualificationId must be one of the club's qualifications"
        g.qualification_kind_id = qid
    return None


@guides_bp.post("/")
@permission_required("guides", "write", "Write guides")
def create_guide():
    body = request.get_json(silent=True) or {}
    g = Guide()
    error = _read(g, body)
    if error:
        return api_error("VALIDATION_ERROR", error, 400)
    member = get_current_member()
    g.created_by = member.id if member else None
    db.session.add(g)
    db.session.flush()
    log_audit(g.created_by, "create_guide", "Guide", g.id, g.title)
    db.session.commit()
    return jsonify(_full(g)), 201


@guides_bp.patch("/<int:guide_id>")
@permission_required("guides", "write", "Write guides")
def update_guide(guide_id: int):
    g = _get(guide_id)
    error = _read(g, request.get_json(silent=True) or {})
    if error:
        db.session.rollback()
        return api_error("VALIDATION_ERROR", error, 400)
    member = get_current_member()
    log_audit(member.id if member else None, "update_guide", "Guide", g.id, g.title)
    db.session.commit()
    return jsonify(_full(g)), 200


@guides_bp.delete("/<int:guide_id>")
@permission_required("guides", "write", "Write guides")
def delete_guide(guide_id: int):
    g = _get(guide_id)
    member = get_current_member()
    log_audit(member.id if member else None, "delete_guide", "Guide", g.id, g.title)
    db.session.delete(g)
    db.session.commit()
    return "", 204


@guides_bp.get("/items")
@permission_required("guides", "write", "Write guides")
def pick_items():
    """Items a guide can belong to (empty without Inventory)."""
    q = (request.args.get("q") or "").strip()
    rows = _ask(ITEMS_LIST, search=q or None, limit=50) or []
    return jsonify([{"id": r["id"], "name": r["name"]} for r in rows]), 200


@guides_bp.get("/qualification-kinds")
@permission_required("guides", "write", "Write guides")
def qualification_kinds():
    """Qualifications a guide can name (empty without Qualifications)."""
    rows = _ask(KINDS) or []
    return jsonify([{"id": r["id"], "name": r["name"]} for r in rows]), 200
