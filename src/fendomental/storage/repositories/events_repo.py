"""SPEC.md section 3 — Ingestion -> Storage write side (economic_events, earnings_events).

Upserts are implemented against SQLite's ON CONFLICT DO UPDATE (the
project's default dialect, per config.settings.db_url). Porting to
Postgres later needs sqlalchemy.dialects.postgresql.insert instead —
same shape, different import — not done here since this targets the
SQLite default (see SPEC.md section 1.6).
"""

import dataclasses

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from fendomental.domain.dto import EarningsEventDTO, EconomicEventDTO
from fendomental.storage.db import get_session
from fendomental.storage.orm_models import EarningsEvent, EconomicEvent


def upsert_economic_events(events: list[EconomicEventDTO]) -> int:
    if not events:
        return 0
    rows = [dataclasses.asdict(e) for e in events]
    update_cols = [c.name for c in EconomicEvent.__table__.columns if c.name not in ("id", "event_date", "country", "event_name")]
    with get_session() as session:
        stmt = sqlite_insert(EconomicEvent).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["event_date", "country", "event_name"],
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
        session.commit()
    return len(rows)


def upsert_earnings_events(events: list[EarningsEventDTO]) -> int:
    if not events:
        return 0
    rows = [dataclasses.asdict(e) for e in events]
    update_cols = [c.name for c in EarningsEvent.__table__.columns if c.name not in ("id", "report_date", "symbol")]
    with get_session() as session:
        stmt = sqlite_insert(EarningsEvent).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["report_date", "symbol"],
            set_={col: getattr(stmt.excluded, col) for col in update_cols},
        )
        session.execute(stmt)
        session.commit()
    return len(rows)
