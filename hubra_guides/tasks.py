"""Celery task: remind before qualifications expire."""

from __future__ import annotations

from hubra.core.modules import per_tenant_job
from hubra.core.tasks import celery_app


@celery_app.task(name="hubra_guides.tasks.remind_qualifications")
@per_tenant_job("qualifications")
def remind_qualifications() -> int:
    from hubra.core.extensions import db

    from .qualifications import remind

    done = remind()
    db.session.commit()
    return done
