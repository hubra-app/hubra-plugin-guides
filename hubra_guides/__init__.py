"""Guides: a how-to per machine or tool, in Markdown or as a Drive link,
and qualifications (licences, first aid, inductions) with their expiry."""

from hubra.core.modules import Blueprint, Module, NavItem, Schedule

module = Module(
    code="inventory.guides",
    # Access the standard roles get when a club first switches it on
    # (docs/roles.md in hubra-app/hubra).
    role_defaults={"member": "view", "board": "edit"},
    name="Guides",
    description=(
        "Usage guides for machines and tools (Markdown or a Google Drive link), "
        "qualifications with expiry and reminders, and who can do what"
    ),
    default_enabled=False,
    depends_on=("inventory",),
    blueprints=(
        Blueprint(
            "hubra_guides.routes",
            "guides_bp",
            "/api/v1/guides",
        ),
    ),
    # Guides show in the inventory item panel; qualifications have a page.
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
            "/app/inventory/qualifications",
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
    tables=("item_guides", "qualification_kinds", "member_qualifications"),
    # Items come from Inventory's contracts, never its tables or code.
    consumes={"inventory.items.get": ">=1,<2", "inventory.item.deleted": ">=1,<2"},
    events={"inventory.item.deleted": "hubra_guides.hooks:on_item_deleted"},
)
