"""qualification_kinds.self_service; copy Community's "can do" entries

Members may add a self-service qualification to themselves ("Elektriker",
"Grafik"), and every member can search who has one. What members can do
used to be the "Kann" entries of the Community plugin's skills directory;
those become self-service qualifications here. The copy reads the old
table only if it is there and imports nothing: Guides does not need
Community, and Community keeps its table.

Revision ID: 4d7b2f9c1a63
Revises: 9a1c4e7b2d58
Create Date: 2026-11-09 10:00:00

"""

from datetime import date, datetime, timezone

from alembic import op
import sqlalchemy as sa

from hubra.core.plugins.ops import columns, has_table


revision = "4d7b2f9c1a63"
down_revision = "9a1c4e7b2d58"
branch_labels = None
depends_on = None


def upgrade():
    if "self_service" not in columns("qualification_kinds"):
        with op.batch_alter_table("qualification_kinds", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "self_service",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
    _copy_community_skills()


def _copy_community_skills() -> None:
    if not has_table("community_skills"):
        return
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT member_id, title, description, created_at FROM community_skills"
            " WHERE kind = 'skill' ORDER BY id"
        )
    ).all()
    if not rows:
        return
    now = datetime.now(timezone.utc)
    kinds = {
        name.strip().casefold(): (kid, self_service)
        for kid, name, self_service in bind.execute(
            sa.text("SELECT id, name, self_service FROM qualification_kinds")
        ).all()
    }
    held = {
        (m, k)
        for m, k in bind.execute(
            sa.text("SELECT member_id, kind_id FROM member_qualifications")
        ).all()
    }
    for member_id, title, description, created_at in rows:
        name = (title or "").strip()[:120]
        if not name:
            continue
        found = kinds.get(name.casefold())
        if found is None:
            bind.execute(
                sa.text(
                    "INSERT INTO qualification_kinds"
                    " (name, remind_days, self_service, created_at)"
                    " VALUES (:name, 30, :yes, :now)"
                ),
                {"name": name, "yes": True, "now": now},
            )
            kid = bind.execute(
                sa.text("SELECT id FROM qualification_kinds WHERE name = :name"),
                {"name": name},
            ).scalar()
            found = kinds[name.casefold()] = (kid, True)
        kid, self_service = found
        # A kind the club manages ("Nothelfer") is not one members may
        # claim for themselves; leave such entries to the managers.
        if not self_service or (member_id, kid) in held:
            continue
        held.add((member_id, kid))
        obtained = _day(created_at)
        bind.execute(
            sa.text(
                "INSERT INTO member_qualifications"
                " (member_id, kind_id, obtained_on, note, created_by, updated_at)"
                " VALUES (:m, :k, :on, :note, :m, :now)"
            ),
            {
                "m": member_id,
                "k": kid,
                "on": obtained or date.today(),
                "note": ((description or "").strip()[:500]) or None,
                "now": now,
            },
        )


def _day(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    try:  # SQLite hands back text
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def downgrade():
    with op.batch_alter_table("qualification_kinds", schema=None) as batch_op:
        batch_op.drop_column("self_service")
