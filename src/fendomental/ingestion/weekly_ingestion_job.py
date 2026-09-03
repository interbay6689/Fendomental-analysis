"""SPEC.md section 3 — Ingestion Layer orchestration, run weekly (Sun primary + Mon backfill)."""

import datetime

from config.settings import EARNINGS_WATCHLIST_SYMBOLS
from fendomental.domain.dto import JobResult
from fendomental.domain.enums import JobName, JobStatus
from fendomental.ingestion.finnhub_client import get_earnings_calendar
from fendomental.ingestion.fmp_client import get_economic_calendar
from fendomental.storage.repositories.events_repo import upsert_earnings_events, upsert_economic_events
from fendomental.storage.repositories.job_log_repo import finish_job, start_job


def run_weekly_ingestion(week_start: datetime.date) -> JobResult:
    week_end = week_start + datetime.timedelta(days=6)
    started_at = datetime.datetime.now(datetime.timezone.utc)
    job_id = start_job(JobName.WEEKLY_INGESTION.value, started_at)

    detail: dict = {}
    try:
        econ_events = get_economic_calendar(week_start, week_end)
        detail["economic_events_upserted"] = upsert_economic_events(econ_events)

        earnings_events = get_earnings_calendar(week_start, week_end, EARNINGS_WATCHLIST_SYMBOLS)
        detail["earnings_events_upserted"] = upsert_earnings_events(earnings_events)
    except Exception as exc:  # noqa: BLE001 — any ingestion failure must be captured in job_run_log, not raised
        finished_at = datetime.datetime.now(datetime.timezone.utc)
        finish_job(job_id, JobStatus.FAILED.value, error_message=str(exc), metadata=detail)
        return JobResult(
            job_name=JobName.WEEKLY_INGESTION.value,
            status=JobStatus.FAILED.value,
            started_at_utc=started_at,
            finished_at_utc=finished_at,
            detail=detail,
            error_message=str(exc),
        )

    finished_at = datetime.datetime.now(datetime.timezone.utc)
    finish_job(job_id, JobStatus.SUCCESS.value, metadata=detail)
    return JobResult(
        job_name=JobName.WEEKLY_INGESTION.value,
        status=JobStatus.SUCCESS.value,
        started_at_utc=started_at,
        finished_at_utc=finished_at,
        detail=detail,
    )
