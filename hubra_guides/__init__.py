"""Guides: a how-to per machine or tool, in Markdown or as a Drive link."""

from hubra.core.modules import Blueprint, Module

module = Module(
    code="inventory.guides",
    name="Guides",
    description="Usage guides for machines and tools (Markdown or a Google Drive link)",
    default_enabled=False,
    depends_on=("inventory",),
    blueprints=(
        Blueprint(
            "hubra_guides.routes",
            "guides_bp",
            "/api/v1/guides",
        ),
    ),
    # Shown in the inventory item panel; no nav entry.
    tables=("item_guides",),
    # Items come from Inventory's contracts, never its tables or code.
    consumes={"inventory.items.get": ">=1,<2", "inventory.item.deleted": ">=1,<2"},
    events={"inventory.item.deleted": "hubra_guides.hooks:on_item_deleted"},
)
