"""Qualifications: licences, first aid, inductions with their expiry and
reminders, and who can do what (self-service entries other members confirm).

Up to 1.5 this plugin was "Guides", an add-on of Inventory with a usage
guide per item. The guides moved into Inventory (2.4); this plugin no
longer needs Inventory. Its module was ``inventory.guides`` and is
``qualifications`` now (``renamed_from`` keeps each club's switch); the
blueprint keeps its name, so the permission keys stay ``guides.*``.
Inventory asks which qualification a member holds through the queries in
contracts.py.
"""

from hubra.core.contracts import query_contract
from hubra.core.modules import Blueprint, Module, NavItem, Schedule

_C = "hubra_guides.contracts"

module = Module(
    code="qualifications",
    renamed_from=("inventory.guides",),
    name="Qualifications",
    description=(
        "Licences, first aid and inductions with expiry and reminders, "
        "and who can do what"
    ),
    default_enabled=False,
    blueprints=(
        Blueprint(
            "hubra_guides.routes",
            "guides_bp",
            "/api/v1/guides",
        ),
    ),
    nav=(
        # Who can do what: every member, next to the other member pages.
        NavItem(
            "/app/skills",
            "shell.nav.canDo",
            "tools",
            section="more",
            order=30,
        ),
        NavItem(
            "/app/qualifications",
            "shell.nav.qualifications",
            "certificate",
            order=34,
            perms=("guides.qualifications.manage",),
        ),
    ),
    tasks=("hubra_guides.tasks",),
    schedule=(
        Schedule(
            "guides-remind-qualifications",
            "hubra_guides.tasks.remind_qualifications",
            86400.0,
        ),
    ),
    # item_guides is the guides' old table: Inventory 2.4 copies it and it
    # is dropped in a later release (a rollback to 1.5 still needs it).
    tables=("item_guides", "qualification_kinds", "member_qualifications"),
    provides=(
        query_contract(
            "qualifications.kinds.list",
            f"{_C}:list_kinds",
            input=f"{_C}:KindsIn",
            output=f"{_C}:Kind",
            description="The club's own qualification kinds (not self-service ones)",
        ),
        query_contract(
            "qualifications.member.holds",
            f"{_C}:member_holds",
            input=f"{_C}:HoldsIn",
            output=f"{_C}:Held",
            description="Whether a member holds these qualifications, and until when",
        ),
    ),
)
