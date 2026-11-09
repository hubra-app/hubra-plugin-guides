"""Guides: how-tos for machines, tools and everything else the club does,
in Markdown or as a link to a manual or video.

A guide may belong to an inventory item (shown on the item) and name the
qualification it takes. Items and qualifications come from the Inventory
and Qualifications plugins' contracts; Guides needs neither.

Until 1.x Guides also kept qualifications, under the module code
``inventory.guides``. Those moved to their own plugin (Qualifications);
both modules list the old code under ``renamed_from``, so clubs that had
Guides on keep it on and get Qualifications on too.
"""

from hubra.core.modules import Blueprint, Module, NavItem

module = Module(
    code="guides",
    renamed_from=("inventory.guides",),
    name="Guides",
    description=(
        "How-tos for machines, tools and everything else the club does, "
        "in Markdown or as a link to a manual or video"
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
        NavItem(
            "/app/guides",
            "shell.nav.guides",
            "book",
            section="operations",
            order=6,
            perms=("guides.guides.read",),
        ),
    ),
    # item_guides: the 1.x guides, copied into guides; dropped in a later release.
    tables=("guides", "item_guides"),
    # Items and qualifications come from the other plugins' contracts, never
    # their tables or code; without them a guide has neither.
    consumes={
        "inventory.items.get": ">=1,<2",
        "inventory.items.list": ">=1,<2",
        "inventory.item.deleted": ">=1,<2",
        "qualifications.kinds.list": ">=1,<2",
        "qualifications.member.holds": ">=1,<2",
    },
    events={"inventory.item.deleted": "hubra_guides.hooks:on_item_deleted"},
)
