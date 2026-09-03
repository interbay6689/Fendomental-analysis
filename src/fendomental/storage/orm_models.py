import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fendomental.domain.enums import (
    ActualDirection,
    Bias,
    ConfidenceLevel,
    EarningsSession,
    ForecastStatus,
    Importance,
    JobName,
    JobStatus,
)


class Base(DeclarativeBase):
    pass


def _sql_in_list(enum_cls) -> str:
    """Render an enum's values as a SQL IN (...) literal list, e.g. "('A', 'B')"."""
    return "(" + ", ".join(f"'{member.value}'" for member in enum_cls) + ")"


class DailyForecast(Base):
    """SPEC.md section 1.1 — core entity, one row per trading day's Synthesis run."""

    __tablename__ = "daily_forecast"
    __table_args__ = (
        CheckConstraint(f"status IN {_sql_in_list(ForecastStatus)}", name="ck_daily_forecast_status"),
        CheckConstraint(f"bias IN {_sql_in_list(Bias)}", name="ck_daily_forecast_bias"),
        CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0.0 AND 1.0",
            name="ck_daily_forecast_confidence_score",
        ),
        CheckConstraint(
            f"confidence_level IN {_sql_in_list(ConfidenceLevel)}", name="ck_daily_forecast_confidence_level"
        ),
        Index("ix_daily_forecast_date", "forecast_date", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, unique=True)
    run_started_at_utc: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    run_finished_at_utc: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    bias: Mapped[str | None] = mapped_column(String(16))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    confidence_level: Mapped[str | None] = mapped_column(String(16))
    uncertainty_source: Mapped[str | None] = mapped_column(Text)
    key_catalysts_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default=text("'[]'"))
    rationale: Mapped[str | None] = mapped_column(Text)
    reference_price: Mapped[float | None] = mapped_column(Float)
    reference_price_ts_utc: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    reference_price_source: Mapped[str] = mapped_column(String(32), server_default=text("'yfinance'"))
    reference_ticker: Mapped[str] = mapped_column(String(16), server_default=text("'NQ=F'"))
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    market_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("market_data_snapshot.id"))
    news_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("news_snapshot.id"))
    raw_llm_response_json: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DailyResult(Base):
    """SPEC.md section 1.2 — 1:1 with DailyForecast, written by the Closing Check job."""

    __tablename__ = "daily_result"
    __table_args__ = (
        CheckConstraint(f"actual_direction IN {_sql_in_list(ActualDirection)}", name="ck_daily_result_direction"),
        Index("ix_daily_result_date", "result_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_id: Mapped[int] = mapped_column(
        ForeignKey("daily_forecast.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    result_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    closing_price: Mapped[float | None] = mapped_column(Float)
    closing_price_ts_utc: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    closing_price_source: Mapped[str] = mapped_column(String(32), server_default=text("'yfinance'"))
    spread_points: Mapped[float | None] = mapped_column(Float)
    spread_pct: Mapped[float | None] = mapped_column(Float)
    threshold_pct_used: Mapped[float] = mapped_column(Float, nullable=False)
    actual_direction: Mapped[str | None] = mapped_column(String(16))
    is_success: Mapped[bool | None] = mapped_column()
    evaluated_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    error_message: Mapped[str | None] = mapped_column(Text)


class EconomicEvent(Base):
    """SPEC.md section 1.4 — raw ingested weekly macro calendar (FMP)."""

    __tablename__ = "economic_events"
    __table_args__ = (
        CheckConstraint(f"importance IN {_sql_in_list(Importance)}", name="ck_economic_events_importance"),
        UniqueConstraint("event_date", "country", "event_name", name="uq_economic_events_date_country_name"),
        Index("ix_econ_events_date", "event_date"),
        Index("ix_econ_events_week", "week_of"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    event_time_utc: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    importance: Mapped[str | None] = mapped_column(String(16))
    actual_value: Mapped[str | None] = mapped_column(Text)
    forecast_value: Mapped[str | None] = mapped_column(Text)
    previous_value: Mapped[str | None] = mapped_column(Text)
    week_of: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'FMP'"))
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EarningsEvent(Base):
    """SPEC.md section 1.4 — quarterly earnings calendar (Finnhub), Mag7 + leading tech."""

    __tablename__ = "earnings_events"
    __table_args__ = (
        CheckConstraint(f"session IN {_sql_in_list(EarningsSession)}", name="ck_earnings_events_session"),
        UniqueConstraint("report_date", "symbol", name="uq_earnings_events_date_symbol"),
        Index("ix_earnings_date", "report_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255))
    session: Mapped[str | None] = mapped_column(String(16))
    eps_estimate: Mapped[float | None] = mapped_column(Float)
    revenue_estimate: Mapped[float | None] = mapped_column(Float)
    week_of: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'Finnhub'"))
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NewsSnapshot(Base):
    """SPEC.md section 1.4 — daily news/sentiment snapshot (Alpha Vantage primary + Finnhub/RSS fallback)."""

    __tablename__ = "news_snapshot"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "topic", name="uq_news_snapshot_date_topic"),
        Index("ix_news_snapshot_date", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    topic: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'macro'"))
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    relevance_avg: Mapped[float | None] = mapped_column(Float)
    headline_count: Mapped[int | None] = mapped_column(Integer)
    primary_source: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'alpha_vantage'"))
    supplementary_headlines_json: Mapped[list[dict] | None] = mapped_column(JSON)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    fetched_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MarketDataSnapshot(Base):
    """SPEC.md section 1.4 — DXY/US10Y/VIX/NQ captured at each job run."""

    __tablename__ = "market_data_snapshot"
    __table_args__ = (
        CheckConstraint("snapshot_type IN ('pre_open', 'close')", name="ck_market_snapshot_type"),
        UniqueConstraint("snapshot_date", "snapshot_type", name="uq_market_snapshot_date_type"),
        Index("ix_market_snapshot_date", "snapshot_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(16), nullable=False)
    dxy: Mapped[float | None] = mapped_column(Float)
    us10y_yield: Mapped[float | None] = mapped_column(Float)
    vix: Mapped[float | None] = mapped_column(Float)
    nq_price: Mapped[float | None] = mapped_column(Float)
    nq_prior_close: Mapped[float | None] = mapped_column(Float)
    captured_at_utc: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'yfinance'"))


class JobRunLog(Base):
    """SPEC.md section 1.4 — self-check / failure-tracking log for the three scheduled jobs."""

    __tablename__ = "job_run_log"
    __table_args__ = (
        CheckConstraint(f"job_name IN {_sql_in_list(JobName)}", name="ck_job_run_log_name"),
        CheckConstraint(f"status IN {_sql_in_list(JobStatus)}", name="ck_job_run_log_status"),
        Index("ix_job_log_name_time", "job_name", "started_at_utc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_for_utc: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at_utc: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at_utc: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)


class AppConfig(Base):
    """SPEC.md section 1.4 — calibratable runtime parameters (e.g. sideways_threshold_pct)."""

    __tablename__ = "app_config"
    __table_args__ = (CheckConstraint("value_type IN ('float', 'int', 'str', 'bool')", name="ck_app_config_type"),)

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(8), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
