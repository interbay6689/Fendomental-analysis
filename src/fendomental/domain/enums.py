import enum


class Bias(str, enum.Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    SIDEWAYS = "Sideways"


class ActualDirection(str, enum.Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    SIDEWAYS = "Sideways"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ForecastStatus(str, enum.Enum):
    """Valid daily_forecast.status values (SPEC.md 1.1) — a subset of JobStatus."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class JobStatus(str, enum.Enum):
    """Valid job_run_log.status values (SPEC.md 1.4)."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RUNNING = "RUNNING"


class Importance(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class EarningsSession(str, enum.Enum):
    BMO = "BMO"
    AMC = "AMC"
    DMH = "DMH"
    UNKNOWN = "UNKNOWN"


class TradingDayType(str, enum.Enum):
    """Return type of scheduler.calendar_utils.get_trading_day_type (SPEC.md section 6)."""

    REGULAR = "regular"
    EARLY_CLOSE = "early_close"
    HOLIDAY = "holiday"


class JobName(str, enum.Enum):
    WEEKLY_INGESTION = "weekly_ingestion"
    DAILY_NEWS_SYNTHESIS = "daily_news_synthesis"
    CLOSING_CHECK = "closing_check"
