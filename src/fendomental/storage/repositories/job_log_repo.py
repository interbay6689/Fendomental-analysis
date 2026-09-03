"""Minimal job_run_log read/write helpers (SPEC.md section 1.4 — self-check/failure tracking)."""

import datetime

from fendomental.storage.db import get_session
from fendomental.storage.orm_models import JobRunLog


def start_job(job_name: str, scheduled_for_utc: datetime.datetime) -> int:
    with get_session() as session:
        row = JobRunLog(
            job_name=job_name,
            scheduled_for_utc=scheduled_for_utc,
            status="RUNNING",
            started_at_utc=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def finish_job(job_id: int, status: str, error_message: str | None = None, metadata: dict | None = None) -> None:
    with get_session() as session:
        row = session.get(JobRunLog, job_id)
        row.status = status
        row.finished_at_utc = datetime.datetime.now(datetime.timezone.utc)
        row.error_message = error_message
        row.metadata_json = metadata
        session.commit()
