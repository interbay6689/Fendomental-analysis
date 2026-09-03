"""Initialize the local database: run Alembic migrations to head, then seed
app_config with the default calibratable parameters from SPEC.md section 1.4.

Usage: python scripts/init_db.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))  # for the top-level `config` package

from sqlalchemy import select  # noqa: E402

from fendomental.storage.db import SessionLocal  # noqa: E402
from fendomental.storage.orm_models import AppConfig  # noqa: E402

SEED_CONFIG = [
    ("sideways_threshold_pct", "0.4", "float", "סף % סימטרי מהמחיר הייחוס המסווג כ-Sideways"),
    ("confidence_high_cutoff", "0.7", "float", "confidence_score מעל ערך זה -> confidence_level='High'"),
    ("confidence_low_cutoff", "0.4", "float", "confidence_score מתחת לערך זה -> confidence_level='Low'"),
    ("min_sample_size", "15", "int", 'N מינימלי לפני הצגת תא סטטיסטי כ"מגמה"'),
]


def run_migrations() -> None:
    subprocess.run(["alembic", "upgrade", "head"], cwd=REPO_ROOT, check=True)


def seed_app_config() -> None:
    with SessionLocal() as session:
        existing_keys = set(session.scalars(select(AppConfig.key)).all())
        added = []
        for key, value, value_type, description in SEED_CONFIG:
            if key in existing_keys:
                continue
            session.add(AppConfig(key=key, value=value, value_type=value_type, description=description))
            added.append(key)
        session.commit()
    if added:
        print(f"Seeded app_config: {', '.join(added)}")
    else:
        print("app_config already seeded, nothing to add.")


if __name__ == "__main__":
    run_migrations()
    seed_app_config()
    print("Database initialized.")
