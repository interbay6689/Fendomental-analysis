from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    fmp_api_key: str = ""
    finnhub_api_key: str = ""
    alpha_vantage_api_key: str = ""
    db_url: str = "sqlite:///./fendomental.db"

    # SPEC.md section 4.3 — model configurable, never hardcoded in the prompt/client code.
    synthesis_model_id: str = "claude-sonnet-5"
    synthesis_prompt_version: str = "synthesis_v1"

    israel_tz: str = "Asia/Jerusalem"
    ny_tz: str = "America/New_York"
    reference_ticker: str = "NQ=F"


settings = Settings()

# SPEC.md section 7, risk #2: fixed symbol list for the earnings calendar
# (Mag7 + leading tech names materially relevant to NQ), deliberately NOT
# derived dynamically from an index-membership API.
EARNINGS_WATCHLIST_SYMBOLS: tuple[str, ...] = (
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "AVGO",
    "AMD",
    "NFLX",
)

