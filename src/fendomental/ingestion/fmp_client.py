"""FMP economic calendar client (SPEC.md sections 1.4 and 4, data source "מקורות נתונים").

Endpoint: https://financialmodelingprep.com/api/v3/economic_calendar
Free-tier availability is UNVERIFIED as of writing this client — see
SPEC.md section 7, risk #1. run_ingestion_now.py surfaces the real
response/status so that can be confirmed against a live key.
"""

import datetime

import requests

from config.settings import settings
from fendomental.common.time_utils import monday_of_week
from fendomental.domain.dto import EconomicEventDTO

BASE_URL = "https://financialmodelingprep.com/api/v3/economic_calendar"

# FMP's "impact" field values, normalized to SPEC.md's Importance enum (Low/Medium/High).
_IMPACT_MAP = {"low": "Low", "medium": "Medium", "high": "High"}


class FmpApiError(RuntimeError):
    """Raised on a non-2xx response or a response shape we don't recognize."""


def get_economic_calendar(start_date: datetime.date, end_date: datetime.date) -> list[EconomicEventDTO]:
    if not settings.fmp_api_key:
        raise FmpApiError("FMP_API_KEY is not set — see .env.example")

    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "apikey": settings.fmp_api_key,
    }
    response = requests.get(BASE_URL, params=params, timeout=30)
    if response.status_code != 200:
        raise FmpApiError(f"FMP economic_calendar returned HTTP {response.status_code}: {response.text[:500]}")

    payload = response.json()
    if isinstance(payload, dict) and ("Error Message" in payload or "error" in payload):
        raise FmpApiError(f"FMP economic_calendar returned an error payload: {payload}")
    if not isinstance(payload, list):
        raise FmpApiError(f"Unexpected FMP economic_calendar response shape: {type(payload).__name__}")

    events: list[EconomicEventDTO] = []
    for item in payload:
        event_dt = _parse_event_datetime(item.get("date"))
        if event_dt is None:
            continue
        event_date = event_dt.date()
        events.append(
            EconomicEventDTO(
                event_date=event_date,
                event_time_utc=event_dt,
                country=str(item.get("country", "")).upper() or "??",
                event_name=str(item.get("event", "")).strip(),
                importance=_IMPACT_MAP.get(str(item.get("impact", "")).strip().lower()),
                actual_value=_stringify(item.get("actual")),
                forecast_value=_stringify(item.get("estimate")),
                previous_value=_stringify(item.get("previous")),
                week_of=monday_of_week(event_date),
            )
        )
    return events


def _parse_event_datetime(raw: str | None) -> datetime.datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    return None


def _stringify(value) -> str | None:
    return None if value is None else str(value)
