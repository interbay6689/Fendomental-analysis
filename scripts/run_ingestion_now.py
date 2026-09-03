"""Manually trigger the weekly Ingestion Layer job against the real FMP/Finnhub APIs,
bypassing the scheduler. Requires FMP_API_KEY and FINNHUB_API_KEY to be set (via .env
or the environment) — this script does NOT fall back to mock/dummy data.

Usage: python scripts/run_ingestion_now.py [--week-start YYYY-MM-DD]
"""

import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from fendomental.common.time_utils import monday_of_week  # noqa: E402
from fendomental.ingestion.weekly_ingestion_job import run_weekly_ingestion  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--week-start",
        type=datetime.date.fromisoformat,
        default=None,
        help="Monday of the target week (YYYY-MM-DD). Defaults to the current week.",
    )
    args = parser.parse_args()

    week_start = args.week_start or monday_of_week(datetime.date.today())
    print(f"Running weekly ingestion for week starting {week_start.isoformat()} ...")

    result = run_weekly_ingestion(week_start)

    print(f"status: {result.status}")
    print(f"detail: {result.detail}")
    if result.error_message:
        print(f"error_message: {result.error_message}")

    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
