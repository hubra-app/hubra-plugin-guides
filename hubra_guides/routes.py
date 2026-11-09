"""Qualifications blueprint: /api/v1/guides/qualifications/...

The blueprint keeps the name it had when this plugin was Guides, so the
permission keys stay ``guides.qualifications.*`` and roles keep their rights.
The usage guides per item moved into Inventory (2.4).
"""

from __future__ import annotations

from flask import Blueprint

guides_bp = Blueprint("guides_bp", __name__)

from . import qualifications  # noqa: E402,F401  (registers its routes)
