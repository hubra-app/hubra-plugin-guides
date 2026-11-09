"""Qualifications: who holds which licence or induction, and until when.

GET    /qualifications/kinds          every member (to see what exists)
POST   /qualifications/kinds          {name, description?, validMonths?, remindDays?}
PATCH  /qualifications/kinds/<id>
DELETE /qualifications/kinds/<id>     with every member's entry of that kind
GET    /qualifications                ?kindId=&state=valid|soon|expired
POST   /qualifications                {memberId, kindId, obtainedOn, expiresOn?, note?}
                                      a second one for the same member and kind renews it
PATCH  /qualifications/<id>
DELETE /qualifications/<id>
GET    /qualifications/mine           the signed-in member's own
POST   /qualifications/mine           {kindId | name, note?} add what I can do
PATCH  /qualifications/mine/<id>      {note}
DELETE /qualifications/mine/<id>
GET    /qualifications/directory      ?q=&kindId= who can do what (every member)

Self-service kinds (``selfService``) are what members can do: "Elektriker",
"Grafik". Members add and remove those on themselves, naming a new one adds
it, and every member can search who has one. The club's own qualifications
(licences, inductions) stay with the managers: only they add, change and
see those for others, and only those can be what an item takes.

Everything else needs guides.qualifications.manage.
A daily job reminds the holder and the managers before one expires.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone

from flask import jsonify, request
from sqlalchemy import select

from hubra.core.auth.helpers import get_current_member
from hubra.core.permissions import permission_required, require_member
from hubra.core.utils import log_audit
from hubra.core.errors import api_error
from hubra.core.extensions import db
from hubra.core.models.member import Member

from .models import ItemGuide, MemberQualification, QualificationKind
from .routes import guides_bp

LABEL = "Manage qualifications"
MANAGE = "guides.qualifications.manage"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def add_months(day: date, months: int) -> date:
    month = day.month - 1 + months
    year, month = day.year + month // 12, month % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def state(q: MemberQualification, kind: QualificationKind, today: date) -> str:
    if q.expires_on is None:
        return "valid"
    if q.expires_on < today:
        return "expired"
    if q.expires_on <= today + timedelta(days=kind.remind_days):
        return "soon"
    return "valid"


def holds(member_id: int, kind_id: int, today: date | None = None) -> str | None:
    """``valid``, ``soon`` or ``expired`` for that member, or None."""
    q = db.session.scalar(
        select(MemberQualification)
        .where(MemberQualification.member_id == member_id)
        .where(MemberQualification.kind_id == kind_id)
    )
    kind = db.session.get(QualificationKind, kind_id)
    return state(q, kind, today or date.today()) if q and kind else None


def _kind_out(k: QualificationKind) -> dict:
    return {
        "id": k.id,
        "name": k.name,
        "description": k.description,
        "validMonths": k.valid_months,
        "remindDays": k.remind_days,
        "selfService": k.self_service,
    }


def _out(q: MemberQualification, kind: QualificationKind, name: str | None) -> dict:
    return {
        "id": q.id,
        "memberId": q.member_id,
        "memberName": name,
        "kindId": q.kind_id,
        "kindName": kind.name,
        "selfService": kind.self_service,
        "obtainedOn": q.obtained_on.isoformat(),
        "expiresOn": q.expires_on.isoformat() if q.expires_on else None,
        "note": q.note,
        "state": state(q, kind, date.today()),
    }


def _int(data, key, lo, hi, required=False):
    value = data.get(key)
    if value is None and not required:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
        raise ValueError(f"{key} must be a whole number from {lo} to {hi}")
    return value


def _day(data, key, required=False):
    value = data.get(key)
    if value in (None, "") and not required:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be a date (YYYY-MM-DD)") from None


def _read_kind(k: QualificationKind, data: dict) -> None:
    if "name" in data or k.name is None:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError("name is required (up to 120 characters)")
        k.name = name.strip()
    if "description" in data:
        text = data.get("description")
        if text is not None and (not isinstance(text, str) or len(text) > 2000):
            raise ValueError("description must be text up to 2000 characters")
        k.description = (text or "").strip() or None
    if "validMonths" in data:
        k.valid_months = _int(data, "validMonths", 1, 600)
    if "remindDays" in data:
        k.remind_days = _int(data, "remindDays", 0, 365, required=True)
    if "selfService" in data:
        value = data.get("selfService")
        if not isinstance(value, bool):
            raise ValueError("selfService must be true or false")
        if value and k.id and db.session.scalar(
            select(ItemGuide.item_id).where(ItemGuide.qualification_id == k.id)
        ):
            raise ValueError(
                "an item takes this qualification, so members cannot add it themselves"
            )
        k.self_service = value


def _bad(exc: ValueError):
    return api_error("VALIDATION_ERROR", str(exc), 400)


# ── Kinds ────────────────────────────────────────────────────────────────────


@guides_bp.get("/qualifications/kinds")
@require_member
def list_kinds():
    kinds = db.session.scalars(
        select(QualificationKind).order_by(QualificationKind.name)
    )
    return jsonify([_kind_out(k) for k in kinds])


@guides_bp.post("/qualifications/kinds")
@permission_required("qualifications", "manage", LABEL)
def create_kind():
    k = QualificationKind(name=None, remind_days=30, self_service=False)
    try:
        _read_kind(k, request.get_json(silent=True) or {})
    except ValueError as exc:
        return _bad(exc)
    if db.session.scalar(
        select(QualificationKind).where(QualificationKind.name == k.name)
    ):
        return api_error("DUPLICATE", "A qualification with this name exists.", 409)
    db.session.add(k)
    db.session.flush()
    log_audit(
        get_current_member().id, "guides.kind.create", "QualificationKind", k.id, k.name
    )
    db.session.commit()
    return jsonify(_kind_out(k)), 201


@guides_bp.patch("/qualifications/kinds/<int:kind_id>")
@permission_required("qualifications", "manage", LABEL)
def update_kind(kind_id: int):
    k = db.session.get(QualificationKind, kind_id)
    if k is None:
        return api_error("NOT_FOUND", "No such qualification.", 404)
    try:
        _read_kind(k, request.get_json(silent=True) or {})
    except ValueError as exc:
        db.session.rollback()
        return _bad(exc)
    other = db.session.scalar(
        select(QualificationKind)
        .where(QualificationKind.name == k.name)
        .where(QualificationKind.id != k.id)
    )
    if other:
        db.session.rollback()
        return api_error("DUPLICATE", "A qualification with this name exists.", 409)
    db.session.commit()
    return jsonify(_kind_out(k))


@guides_bp.delete("/qualifications/kinds/<int:kind_id>")
@permission_required("qualifications", "manage", LABEL)
def delete_kind(kind_id: int):
    k = db.session.get(QualificationKind, kind_id)
    if k is None:
        return api_error("NOT_FOUND", "No such qualification.", 404)
    log_audit(
        get_current_member().id, "guides.kind.delete", "QualificationKind", k.id, k.name
    )
    for q in db.session.scalars(
        select(MemberQualification).where(MemberQualification.kind_id == k.id)
    ):
        db.session.delete(q)
    db.session.delete(k)
    db.session.commit()
    return "", 204


# ── Members' qualifications ──────────────────────────────────────────────────


def _rows(q):
    rows = db.session.execute(
        q.join(QualificationKind, QualificationKind.id == MemberQualification.kind_id)
        .join(Member, Member.id == MemberQualification.member_id)
        .add_columns(QualificationKind, Member)
    ).all()
    return [_out(r[0], r[1], r[2].name) for r in rows]


@guides_bp.get("/qualifications")
@permission_required("qualifications", "manage", LABEL)
def list_qualifications():
    q = select(MemberQualification).where(Member.archived_at.is_(None))
    kind_id = request.args.get("kindId", type=int)
    if kind_id:
        q = q.where(MemberQualification.kind_id == kind_id)
    out = _rows(q)
    wanted = request.args.get("state")
    if wanted in ("valid", "soon", "expired"):
        out = [r for r in out if r["state"] == wanted]
    # Soonest expiry first; those that never expire last.
    out.sort(key=lambda r: (r["expiresOn"] or "9999", r["memberName"] or ""))
    return jsonify(out)


@guides_bp.get("/qualifications/mine")
@require_member
def my_qualifications():
    member = get_current_member()
    q = select(MemberQualification).where(MemberQualification.member_id == member.id)
    out = _rows(q)
    out.sort(key=lambda r: r["kindName"])
    return jsonify(out)


def _save(q: MemberQualification, data: dict, kind: QualificationKind) -> None:
    obtained = _day(data, "obtainedOn", required=q.obtained_on is None) or q.obtained_on
    if obtained > date.today():
        raise ValueError("obtainedOn cannot be in the future")
    if "expiresOn" in data:
        expires = _day(data, "expiresOn")
    elif obtained != q.obtained_on or q.expires_on is None:
        expires = add_months(obtained, kind.valid_months) if kind.valid_months else None
    else:
        expires = q.expires_on
    if expires and expires < obtained:
        raise ValueError("expiresOn must be after obtainedOn")
    if "note" in data:
        note = data.get("note")
        if note is not None and (not isinstance(note, str) or len(note) > 500):
            raise ValueError("note must be text up to 500 characters")
        q.note = (note or "").strip() or None
    if (obtained, expires) != (q.obtained_on, q.expires_on):
        q.reminded_at = None  # renewed: remind again before the new date
    q.obtained_on, q.expires_on, q.updated_at = obtained, expires, _now()


@guides_bp.post("/qualifications")
@permission_required("qualifications", "manage", LABEL)
def add_qualification():
    data = request.get_json(silent=True) or {}
    try:
        member_id = _int(data, "memberId", 1, 2**31 - 1, required=True)
        kind_id = _int(data, "kindId", 1, 2**31 - 1, required=True)
    except ValueError as exc:
        return _bad(exc)
    member = db.session.get(Member, member_id)
    kind = db.session.get(QualificationKind, kind_id)
    if member is None or kind is None:
        return api_error("VALIDATION_ERROR", "memberId and kindId must exist", 400)
    q = db.session.scalar(
        select(MemberQualification)
        .where(MemberQualification.member_id == member_id)
        .where(MemberQualification.kind_id == kind_id)
    )
    created = q is None
    if created:
        q = MemberQualification(
            member_id=member_id,
            kind_id=kind_id,
            created_by=get_current_member().id,
        )
    try:
        _save(q, data, kind)
    except ValueError as exc:
        db.session.rollback()
        return _bad(exc)
    if created:
        db.session.add(q)
    db.session.flush()
    log_audit(
        get_current_member().id,
        "guides.qualification.add" if created else "guides.qualification.renew",
        "MemberQualification",
        q.id,
        f"{member.name}: {kind.name}",
    )
    db.session.commit()
    return jsonify(_out(q, kind, member.name)), 201 if created else 200


@guides_bp.patch("/qualifications/<int:qid>")
@permission_required("qualifications", "manage", LABEL)
def update_qualification(qid: int):
    q = db.session.get(MemberQualification, qid)
    if q is None:
        return api_error("NOT_FOUND", "No such qualification.", 404)
    kind = db.session.get(QualificationKind, q.kind_id)
    try:
        _save(q, request.get_json(silent=True) or {}, kind)
    except ValueError as exc:
        db.session.rollback()
        return _bad(exc)
    db.session.commit()
    member = db.session.get(Member, q.member_id)
    return jsonify(_out(q, kind, member.name if member else None))


@guides_bp.delete("/qualifications/<int:qid>")
@permission_required("qualifications", "manage", LABEL)
def delete_qualification(qid: int):
    q = db.session.get(MemberQualification, qid)
    if q is None:
        return api_error("NOT_FOUND", "No such qualification.", 404)
    log_audit(
        get_current_member().id,
        "guides.qualification.delete",
        "MemberQualification",
        q.id,
        None,
    )
    db.session.delete(q)
    db.session.commit()
    return "", 204


# ── What members can do (self-service) ──────────────────────────────────────

MAX_OWN = 50


def _note(data: dict) -> str | None:
    note = data.get("note")
    if note is not None and (not isinstance(note, str) or len(note) > 500):
        raise ValueError("note must be text up to 500 characters")
    return (note or "").strip() or None


def _self_kind(data: dict) -> QualificationKind:
    """The self-service kind by id, or by name (added when new)."""
    if data.get("kindId") is not None:
        kind = db.session.get(
            QualificationKind, _int(data, "kindId", 1, 2**31 - 1, required=True)
        )
        if kind is None:
            raise LookupError("No such qualification.")
    else:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ValueError("kindId or name (up to 120 characters) is required")
        name = " ".join(name.split())
        kind = next(
            (
                k
                for k in db.session.scalars(select(QualificationKind))
                if k.name.casefold() == name.casefold()
            ),
            None,
        )
        if kind is None:
            kind = QualificationKind(
                name=name, remind_days=30, self_service=True, valid_months=None
            )
            db.session.add(kind)
            db.session.flush()
            return kind
    if not kind.self_service:
        raise PermissionError(
            f"{kind.name} is confirmed by the club; ask whoever manages qualifications."
        )
    return kind


@guides_bp.post("/qualifications/mine")
@require_member
def add_mine():
    member = get_current_member()
    data = request.get_json(silent=True) or {}
    try:
        note = _note(data)
        kind = _self_kind(data)
    except ValueError as exc:
        db.session.rollback()
        return _bad(exc)
    except LookupError as exc:
        db.session.rollback()
        return api_error("NOT_FOUND", str(exc), 404)
    except PermissionError as exc:
        db.session.rollback()
        return api_error("FORBIDDEN", str(exc), 403)
    q = db.session.scalar(
        select(MemberQualification)
        .where(MemberQualification.member_id == member.id)
        .where(MemberQualification.kind_id == kind.id)
    )
    if q is not None:
        db.session.rollback()
        return api_error("DUPLICATE", "You have this one already.", 409)
    own = db.session.scalar(
        select(db.func.count())
        .select_from(MemberQualification)
        .join(QualificationKind, QualificationKind.id == MemberQualification.kind_id)
        .where(MemberQualification.member_id == member.id)
        .where(QualificationKind.self_service.is_(True))
    )
    if own >= MAX_OWN:
        db.session.rollback()
        return _bad(ValueError(f"at most {MAX_OWN} entries per member"))
    q = MemberQualification(
        member_id=member.id,
        kind_id=kind.id,
        obtained_on=date.today(),
        note=note,
        created_by=member.id,
        updated_at=_now(),
    )
    db.session.add(q)
    db.session.commit()
    return jsonify(_out(q, kind, member.name)), 201


def _own(qid: int):
    """The signed-in member's own entry of a self-service kind."""
    q = db.session.get(MemberQualification, qid)
    member = get_current_member()
    if q is None or q.member_id != member.id:
        return None, None, api_error("NOT_FOUND", "No such qualification.", 404)
    kind = db.session.get(QualificationKind, q.kind_id)
    if not kind.self_service:
        return None, None, api_error(
            "FORBIDDEN", "The club manages this qualification.", 403
        )
    return q, kind, None


@guides_bp.patch("/qualifications/mine/<int:qid>")
@require_member
def update_mine(qid: int):
    q, kind, err = _own(qid)
    if err:
        return err
    try:
        q.note = _note(request.get_json(silent=True) or {})
    except ValueError as exc:
        return _bad(exc)
    q.updated_at = _now()
    db.session.commit()
    return jsonify(_out(q, kind, get_current_member().name))


@guides_bp.delete("/qualifications/mine/<int:qid>")
@require_member
def delete_mine(qid: int):
    q, _kind, err = _own(qid)
    if err:
        return err
    db.session.delete(q)
    db.session.commit()
    return "", 204


@guides_bp.get("/qualifications/directory")
@require_member
def directory():
    """Who can do what: every active member's self-service entries."""
    me = get_current_member()
    query = (
        select(MemberQualification, QualificationKind, Member)
        .join(QualificationKind, QualificationKind.id == MemberQualification.kind_id)
        .join(Member, Member.id == MemberQualification.member_id)
        .where(QualificationKind.self_service.is_(True))
        .where(Member.status == "active")
        .where(Member.archived_at.is_(None))
        .where(Member.deleted_at.is_(None))
        .order_by(db.func.lower(QualificationKind.name), MemberQualification.id)
    )
    kind_id = request.args.get("kindId", type=int)
    if kind_id:
        query = query.where(MemberQualification.kind_id == kind_id)
    text = (request.args.get("q") or "").strip()[:80]
    if text:
        like = f"%{text.lower()}%"
        query = query.where(
            db.or_(
                db.func.lower(QualificationKind.name).like(like),
                db.func.lower(db.func.coalesce(MemberQualification.note, "")).like(
                    like
                ),
            )
        )
    rows = db.session.execute(query.limit(1000)).all()
    rows.sort(key=lambda r: (r[1].name.casefold(), (r[2].name or "").casefold()))
    return jsonify(
        [
            {
                "id": q.id,
                "memberId": m.id,
                "memberName": m.name,
                "kindId": k.id,
                "kindName": k.name,
                "note": q.note,
                "mine": m.id == me.id,
            }
            for q, k, m in rows
        ]
    )


# ── Reminders ────────────────────────────────────────────────────────────────


def _managers() -> list[Member]:
    from hubra.core.permissions import member_has_permission

    return [
        m
        for m in db.session.scalars(select(Member).where(Member.archived_at.is_(None)))
        if member_has_permission(m, MANAGE)
    ]


def remind(today: date | None = None) -> int:
    """Tells holders and managers once about each qualification that
    expires within its kind's reminder days. Returns how many."""
    from hubra.core.notifications.services import create_notification

    today = today or date.today()
    due = []
    for q, kind, member in db.session.execute(
        select(MemberQualification, QualificationKind, Member)
        .join(QualificationKind, QualificationKind.id == MemberQualification.kind_id)
        .join(Member, Member.id == MemberQualification.member_id)
        .where(MemberQualification.expires_on.is_not(None))
        .where(MemberQualification.reminded_at.is_(None))
        .where(Member.archived_at.is_(None))
        .where(Member.deleted_at.is_(None))
    ).all():
        if q.expires_on <= today + timedelta(days=kind.remind_days):
            due.append((q, kind, member))
    if not due:
        return 0
    managers = _managers()
    for q, kind, member in due:
        when = q.expires_on.strftime("%d.%m.%Y")
        expired = q.expires_on < today
        create_notification(
            member.id,
            kind="warning",
            title=f"{kind.name}: {'expired' if expired else 'expires'} {when}",
            msg="Renew it in time; the club needs to know when you have.",
            link="/app/dashboard/me",
        )
        for m in managers:
            if m.id == member.id:
                continue
            create_notification(
                m.id,
                kind="warning",
                title=f"{member.name}: {kind.name} {'expired' if expired else 'expires'} {when}",
                msg="",
                link="/app/inventory/qualifications",
            )
        q.reminded_at = _now()
    db.session.flush()
    return len(due)
