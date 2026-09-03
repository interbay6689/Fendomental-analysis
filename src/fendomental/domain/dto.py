import dataclasses
import datetime


@dataclasses.dataclass(slots=True)
class EconomicEventDTO:
    """SPEC.md section 1.4 — one row of the FMP economic calendar."""

    event_date: datetime.date
    country: str
    event_name: str
    week_of: datetime.date
    event_time_utc: datetime.datetime | None = None
    importance: str | None = None  # domain.enums.Importance value, or None if FMP didn't classify it
    actual_value: str | None = None
    forecast_value: str | None = None
    previous_value: str | None = None
    source: str = "FMP"


@dataclasses.dataclass(slots=True)
class EarningsEventDTO:
    """SPEC.md section 1.4 — one row of the Finnhub earnings calendar (Mag7 + leading tech)."""

    report_date: datetime.date
    symbol: str
    week_of: datetime.date
    company_name: str | None = None
    session: str | None = None  # domain.enums.EarningsSession value
    eps_estimate: float | None = None
    revenue_estimate: float | None = None
    source: str = "Finnhub"


@dataclasses.dataclass(slots=True)
class JobResult:
    """Return value of the three scheduled-job orchestration functions (SPEC.md section 3)."""

    job_name: str
    status: str  # domain.enums.JobStatus value
    started_at_utc: datetime.datetime
    finished_at_utc: datetime.datetime
    detail: dict = dataclasses.field(default_factory=dict)
    error_message: str | None = None
