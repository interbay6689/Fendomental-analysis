"""Finnhub earnings calendar client (SPEC.md sections 1.4 and 4, data source "מקורות נתונים").

Endpoint: https://finnhub.io/api/v1/calendar/earnings
Finnhub's free tier does not offer a multi-symbol filter on this
endpoint, so this client calls it once per symbol in the fixed
watchlist (config.settings.EARNINGS_WATCHLIST_SYMBOLS) — well under
the free tier's 60 calls/minute limit for a ~10-symbol watchlist.
Free-tier availability is UNVERIFIED as of writing this client — see
SPEC.md section 7, risk #2.
"""

import datetime

import requests

from config.settings import settings
from fendomental.common.redact import redact_secrets
from fendomental.common.time_utils import monday_of_week
from fendomental.domain.dto import EarningsEventDTO
from fendomental.domain.enums import EarningsSession

BASE_URL = "https://finnhub.io/api/v1/calendar/earnings"

_SESSION_MAP = {"bmo": EarningsSession.BMO.value, "amc": EarningsSession.AMC.value, "dmh": EarningsSession.DMH.value}


class FinnhubApiError(RuntimeError):
    """Raised on a non-2xx response or a response shape we don't recognize."""


def get_earnings_calendar(
    start_date: datetime.date, end_date: datetime.date, symbols: tuple[str, ...]
) -> list[EarningsEventDTO]:
    if not settings.finnhub_api_key:
        raise FinnhubApiError("FINNHUB_API_KEY is not set — see .env.example")

    events: list[EarningsEventDTO] = []
    for symbol in symbols:
        events.extend(_get_earnings_for_symbol(symbol, start_date, end_date))
    return events


def _get_earnings_for_symbol(
    symbol: str, start_date: datetime.date, end_date: datetime.date
) -> list[EarningsEventDTO]:
    params = {
        "from": start_date.isoformat(),
        "to": end_date.isoformat(),
        "symbol": symbol,
        "token": settings.finnhub_api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
    except requests.exceptions.RequestException as exc:
        # str(exc) on a connection-level failure (proxy/DNS/TLS) embeds the full
        # request URL including token=... — never let that reach job_run_log raw.
        raise FinnhubApiError(redact_secrets(str(exc))) from None

    if response.status_code != 200:
        raise FinnhubApiError(
            f"Finnhub calendar/earnings ({symbol}) returned HTTP {response.status_code}: {response.text[:500]}"
        )

    payload = response.json()
    if not isinstance(payload, dict) or "earningsCalendar" not in payload:
        raise FinnhubApiError(f"Unexpected Finnhub calendar/earnings response shape for {symbol}: {payload}")

    events: list[EarningsEventDTO] = []
    for item in payload["earningsCalendar"]:
        report_date = _parse_date(item.get("date"))
        if report_date is None:
            continue
        events.append(
            EarningsEventDTO(
                report_date=report_date,
                symbol=str(item.get("symbol", symbol)).upper(),
                week_of=monday_of_week(report_date),
                session=_SESSION_MAP.get(str(item.get("hour", "")).strip().lower(), EarningsSession.UNKNOWN.value),
                eps_estimate=item.get("epsEstimate"),
                revenue_estimate=item.get("revenueEstimate"),
            )
        )
    return events


def _parse_date(raw: str | None) -> datetime.date | None:
    if not raw:
        return None
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        return None
