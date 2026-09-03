# מסמך איפיון: מערכת ניתוח פונדמנטלי יומי ל-NQ

## הקשר (Context)

הבריף `fundamentalanalysisbrief.pdf` מגדיר מערכת standalone (ללא קשר ל-AgentMarket הקיים)
שמייצרת יומית תחזית כיוון (Bias) ל-NQ על בסיס אירועי קלנדר כלכלי, דוחות רבעוניים וסנטימנט
חדשות — ובודקת את עצמה מול המחיר בפועל בסוף כל יום, כולל סטטיסטיקת הצלחה שקופה
(עם N לכל תא). הבריף עצמו מבקש **מסמך איפיון בלבד, ללא קוד**, שיכסה שישה נושאים: סכמת
DB, מבנה קבצים, ממשקים פנימיים, נוסח פרומפט ה-Synthesis Engine, לוגיקת סף הסיווג
Bullish/Bearish/Sideways, ותזמון ה-jobs (כולל שעון ישראל ומעבר קיץ/חורף).

הריפו כרגע ריק (README בלבד) — זהו פרויקט חדש לגמרי. המסמך הזה הוא תוצר סופי לאישור,
לא רק תוכנית לביצוע פנימי — לכן הוא כתוב ברמת פירוט שמאפשרת להתחיל לממש ישירות ממנו.

לפני הכתיבה נבדקו שתי החלטות עיצוב פתוחות מול המשתמש:
1. **הגדרת "מחיר סגירה"** — הבריף הגדיר את חלון הסשן הפעיל כ-16:30–00:00 שעון ישראל
   (09:30–17:00 ET), כלומר עד תום חלון המסחר הרציף בחוזי NQ (לפני הפסקת התחזוקה של
   CME), לא עד סגירת ה-cash market של NYSE (16:00 ET). **הוחלט: לשמור על ההגדרה
   המקורית של הבריף — לעגן את `closing_price`/הבדיקה ל-00:00 ישראל / ~17:00 ET**,
   כלומר תנועת NQ עד תום חלון הסשן הרציף שהבריף הגדיר במפורש. גרסה קודמת של מסמך
   זה עגנה בטעות לסגירת ה-cash market (16:00 ET) — תוקן.
2. **מקור סנטימנט חדשות** — Finnhub News Sentiment API הייעודי כנראה דורש תוכנית בתשלום.
   **הוחלט: Alpha Vantage NEWS_SENTIMENT כמקור ראשי** (ציון סנטימנט מספרי אמיתי,
   free tier, ניתן לסינון לפי טופיק/טיקר) **+ כותרות גולמיות מ-Finnhub/RSS כגיבוי/תוספת**
   שמוזנות ישירות ל-Claude בפרומפט — ראו פירוט בסעיף "מקורות נתונים" ובסעיף 4.

---

## תובנות וביקורת על הבריף (לפני הכניסה לפרטים הטכניים)

הבריף בנוי היטב מבחינה מתודולוגית — הפרדת שכבות ברורה, שקיפות סטטיסטית עם N, הגבלת
Phase A לפונדמנטלי טהור (בלי לערבב עם טכני/מיקרוסטרוקטורה), ומודעות מפורשת לסיכון
overfitting. הפערים העיקריים שזיהיתי, ואיך הם נפתרו במפרט הזה:

1. **"מחיר ייחוס" ו"מחיר סגירה" לא הוגדרו במדויק** — NQ נסחר כמעט 24/5, אז "סגירה"
   יכולה להתפרש בכמה דרכים שונות שכל אחת נותנת סטטיסטיקה שונה. **נפתר** — עוגן ל-00:00
   ישראל / ~17:00 ET, תום חלון הסשן הרציף כפי שהבריף הגדיר במפורש (16:30–00:00 ישראל),
   לא סגירת ה-cash market של NYSE.
2. **פער שעון ישראל–ניו יורק** — ה"16:30" בבריף נכון רוב השנה כי ההפרש בין השעונים נשאר
   7 שעות כששניהם באותו מצב עונתי (קיץ/חורף), אבל יש 2–4 שבועות בשנה (מרץ-אפריל,
   אוקטובר-נובמבר) שבהם ישראל וארה"ב עוברות שעון בתאריכים שונים, וה-cron הקבוע היה
   "מפספס" את פתיחת/סגירת ניו יורק בדיוק בחלונות האלה. **נפתר** — ה-jobs המסחריים
   מתוזמנים לפי `America/New_York`, לא לפי שעון ישראל (סעיף 6).
3. **סיכוני API של free tier** — Finnhub News Sentiment כנראה דורש תשלום; FMP ו-Finnhub
   עשויים להגביל endpoints ספציפיים ב-free tier. **נפתר חלקית** — Alpha Vantage כמקור
   סנטימנט ראשי; שאר הסיכונים מתועדים כ"לוודא לפני התחלת המימוש" (סעיף 7).
4. **חסר Versioning** — כיול עתידי של הפרומפט או של סף ה-Sideways היה "מזהם" השוואה
   היסטורית. **נפתר** — `prompt_version` ו-`model_id` נשמרים בכל שורת תחזית,
   וה-threshold נשמר בפועל (`threshold_pct_used`) בכל שורת תוצאה.
5. **חסרה טבלת run-log** — מה קורה אם API נופל ב-16:00? **נפתר** — `job_run_log`
   + `status` על `daily_forecast` (`SUCCESS`/`FAILED`/`SKIPPED`), כך שיום כושל מתועד
   ולא נעלם בשקט ולא נספר כטעות בסטטיסטיקה.
6. **חגים/ימי מסחר מקוצרים** — הבריף לא התייחס לכך שהבורסה סגורה בחגים אמריקאיים.
   **נפתר** — בדיקת `is_nyse_trading_day` (לוח שנה רשמי) לפני כל job מסחרי; ימים
   חסומים מסומנים `SKIPPED` ולא נכנסים למכנה הסטטיסטי.
7. **שדה `rationale`** — הוספתי שדה טקסט קצר (1-3 משפטים) לפלט ה-JSON, מעבר לארבעת
   השדות שהבריף ביקש (`bias`, `confidence`, `uncertainty_source`, `key_catalysts`) —
   כדי שיהיה משהו קריא-לאדם להציג בטאב היומי ולסייע בדיבוג תחזיות חלשות. ניתן להוריד
   בקלות אם לא רצוי.
8. **מסגרת overfitting** — בשלב הזה אין למידה/כיול אוטומטי על נתונים היסטוריים, אז
   סיכון ה-overfitting נמוך; הוא הופך רלוונטי רק כשמתחילים לכייל ידנית את הסף או את
   הפרומפט לפי ביצועים שנצפו. ה-versioning (סעיף 4) הוא בדיוק התשתית שמאפשרת בעתיד
   לחתוך "לפני/אחרי שינוי" ולא לטשטש רגימים שונים.

---

## 1. סכמת DB

מוסכמות: `DateTime` עם timezone (UTC) לזמנים; `Date` לתאריכי מסחר; enum ממומש כ-`TEXT + CHECK`
(פורטבילי בין SQLite ל-Postgres). מומלץ SQLAlchemy ORM + Alembic migrations כדי שה-DDL
בפועל ייווצר נכון לכל דיאלקט (לא לכתוב `CREATE TABLE` ידני בקוד).

### 1.1 `daily_forecast` — ליבת המערכת, שורה אחת ליום מסחר

```sql
CREATE TABLE daily_forecast (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date         DATE NOT NULL UNIQUE,          -- תאריך המסחר הקנוני (NY), ראו 7.7
    run_started_at_utc    TIMESTAMP NOT NULL,
    run_finished_at_utc   TIMESTAMP,
    status                TEXT NOT NULL CHECK (status IN ('SUCCESS','PARTIAL','FAILED')),
    bias                  TEXT CHECK (bias IN ('Bullish','Bearish','Sideways')),  -- NULL אם FAILED
    confidence_score      REAL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    confidence_level      TEXT CHECK (confidence_level IN ('Low','Medium','High')),
    uncertainty_source    TEXT,
    key_catalysts_json    TEXT NOT NULL DEFAULT '[]',     -- JSON array; Postgres: JSONB
    rationale             TEXT,
    reference_price       REAL,
    reference_price_ts_utc TIMESTAMP,
    reference_price_source TEXT DEFAULT 'yfinance',
    reference_ticker      TEXT DEFAULT 'NQ=F',
    model_id              TEXT NOT NULL,                  -- למשל 'claude-sonnet-5', מוגדר ב-config
    prompt_version        TEXT NOT NULL,                  -- למשל 'synthesis_v1'
    market_snapshot_id    INTEGER REFERENCES market_data_snapshot(id),
    news_snapshot_id      INTEGER REFERENCES news_snapshot(id),
    raw_llm_response_json TEXT,                           -- audit trail מלא
    error_message         TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX ix_daily_forecast_date ON daily_forecast(forecast_date);
```

### 1.2 `daily_result` — יחס 1:1 מול `daily_forecast`, נכתב ע"י Closing Check

```sql
CREATE TABLE daily_result (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_id           INTEGER NOT NULL UNIQUE REFERENCES daily_forecast(id) ON DELETE CASCADE,
    result_date           DATE NOT NULL,                  -- מראה forecast_date, דנורמליזציה לביצועי שאילתה
    closing_price         REAL,
    closing_price_ts_utc  TIMESTAMP,
    closing_price_source  TEXT DEFAULT 'yfinance',
    spread_points         REAL,                           -- closing_price - reference_price
    spread_pct            REAL,                           -- (closing-reference)/reference * 100
    threshold_pct_used    REAL NOT NULL,                  -- ערך app_config בזמן החישוב (audit)
    actual_direction      TEXT CHECK (actual_direction IN ('Bullish','Bearish','Sideways','UNKNOWN')),
    is_success            INTEGER,                        -- 0/1, NULL אם UNKNOWN (Postgres: BOOLEAN)
    evaluated_at_utc      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_message         TEXT
);
CREATE INDEX ix_daily_result_date ON daily_result(result_date);
```

`day_of_week` **לא** נשמר כעמודה — נגזר ב-query מ-`result_date`
(`strftime('%w', result_date)` / Postgres `EXTRACT(DOW FROM result_date)`), בדיוק כפי
שהבריף ציין ("ללא צורך בשינוי מבני ב-ingestion").

### 1.3 `rollup_stats` — ממומש כ-Views, לא כטבלה מסונכרנת

בנפח נתונים כזה (כמה מאות שורות בשנה) עדיף views חיים על פני טבלת cache שעלולה
להתיישן:

```sql
CREATE VIEW v_success_by_weekday AS
SELECT CAST(strftime('%w', r.result_date) AS INTEGER) AS weekday,
       COUNT(*) AS n, SUM(r.is_success) AS n_success,
       ROUND(100.0 * SUM(r.is_success) / COUNT(*), 1) AS success_pct
FROM daily_result r WHERE r.is_success IS NOT NULL GROUP BY weekday;

CREATE VIEW v_success_by_confidence AS
SELECT f.confidence_level, COUNT(*) AS n, SUM(r.is_success) AS n_success,
       ROUND(100.0 * SUM(r.is_success) / COUNT(*), 1) AS success_pct
FROM daily_result r JOIN daily_forecast f ON f.id = r.forecast_id
WHERE r.is_success IS NOT NULL GROUP BY f.confidence_level;

CREATE VIEW v_success_by_weekday_confidence AS   -- קומבינציה אופציונלית
SELECT CAST(strftime('%w', r.result_date) AS INTEGER) AS weekday,
       f.confidence_level, COUNT(*) AS n, SUM(r.is_success) AS n_success,
       ROUND(100.0 * SUM(r.is_success) / COUNT(*), 1) AS success_pct
FROM daily_result r JOIN daily_forecast f ON f.id = r.forecast_id
WHERE r.is_success IS NOT NULL GROUP BY weekday, f.confidence_level;
```

רולאפים תקופתיים (יומי/שבועי/חודשי) הם אגרגציה מסוננת-לפי-טווח-תאריכים על אותה
צורה — פונקציה אחת מפורמטת `get_success_rate(period, start, end)`, לא views נפרדים.
כל תוצאה שה-UI מציג נושאת `n` לצד `success_pct`; שכבת ה-UI (לא ה-DB) מיישמת את כלל
ההשתקה (`n < min_sample_size` ⇒ מוצג כ"אין מספיק נתונים" אך ה-N האמיתי תמיד גלוי).

### 1.4 טבלאות תומכות (כל אחת מוצדקת בנפרד)

**`economic_events`** — קלנדר מאקרו גולמי מ-FMP. נחוץ כי Synthesis קורא "אירועי השבוע/היום"
בלי תלות בזמן ריצת ה-ingestion, וכי הרצה חוזרת של ingestion חייבת להיות idempotent.
```sql
CREATE TABLE economic_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date DATE NOT NULL,
    event_time_utc TIMESTAMP,
    country TEXT NOT NULL,
    event_name TEXT NOT NULL,
    importance TEXT CHECK (importance IN ('Low','Medium','High')),
    actual_value TEXT, forecast_value TEXT, previous_value TEXT,
    week_of DATE NOT NULL,                      -- יום שני של השבוע ה-ISO, לחיפוש שבועי מהיר
    source TEXT NOT NULL DEFAULT 'FMP',
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_date, country, event_name)
);
CREATE INDEX ix_econ_events_date ON economic_events(event_date);
CREATE INDEX ix_econ_events_week ON economic_events(week_of);
```

**`earnings_events`** — קלנדר דוחות רבעוניים (Finnhub), Mag7 + טכנולוגיה מובילה.
```sql
CREATE TABLE earnings_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE NOT NULL, symbol TEXT NOT NULL, company_name TEXT,
    session TEXT CHECK (session IN ('BMO','AMC','DMH','UNKNOWN')),
    eps_estimate REAL, revenue_estimate REAL, week_of DATE NOT NULL,
    source TEXT NOT NULL DEFAULT 'Finnhub',
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_date, symbol)
);
CREATE INDEX ix_earnings_date ON earnings_events(report_date);
```

**`news_snapshot`** — תיעוד יומי של הסנטימנט/כותרות ששימשו את ה-Synthesis, לצורך audit
ודיבוג לאחור. עודכן לשקף את החלטת המקור (Alpha Vantage + גיבוי כותרות גולמיות):
```sql
CREATE TABLE news_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date DATE NOT NULL,
    topic TEXT NOT NULL DEFAULT 'macro',        -- 'macro' / 'financial_markets' / טיקר בודד
    sentiment_score REAL,                        -- ממוצע משוקלל-רלוונטיות מ-Alpha Vantage (-1..1)
    relevance_avg REAL,                          -- ציון רלוונטיות ממוצע (Alpha Vantage)
    headline_count INTEGER,
    primary_source TEXT NOT NULL DEFAULT 'alpha_vantage',
    supplementary_headlines_json TEXT,           -- כותרות גולמיות מ-Finnhub/RSS, לעיבוד הקשרי ע"י Claude
    raw_payload_json TEXT NOT NULL,              -- payload מלא, audit
    fetched_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(snapshot_date, topic)
);
CREATE INDEX ix_news_snapshot_date ON news_snapshot(snapshot_date);
```

**`market_data_snapshot`** — DXY/US10Y/VIX/NQ בכל ריצה; גם המקור ל-`reference_price`.
```sql
CREATE TABLE market_data_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date DATE NOT NULL,
    snapshot_type TEXT NOT NULL CHECK (snapshot_type IN ('pre_open','close')),
    dxy REAL, us10y_yield REAL, vix REAL, nq_price REAL,
    nq_prior_close REAL,                        -- לחישוב שינוי יום-על-יום שמוצג ל-LLM
    captured_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL DEFAULT 'yfinance',
    UNIQUE(snapshot_date, snapshot_type)
);
CREATE INDEX ix_market_snapshot_date ON market_data_snapshot(snapshot_date);
```

**`job_run_log`** — מנגנון ה"בדיקה עצמית" ותיעוד כשלים.
```sql
CREATE TABLE job_run_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name TEXT NOT NULL CHECK (job_name IN
        ('weekly_ingestion','daily_news_synthesis','closing_check')),
    scheduled_for_utc TIMESTAMP NOT NULL,
    started_at_utc TIMESTAMP, finished_at_utc TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('SUCCESS','PARTIAL','FAILED','SKIPPED','RUNNING')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata_json TEXT   -- למשל {"fmp":"ok","alpha_vantage":"failed","fallback_used":true}
);
CREATE INDEX ix_job_log_name_time ON job_run_log(job_name, started_at_utc);
```

**`app_config`** — כדי שסף ה-Sideways (ופרמטרים נוספים) יהיה ניתן לכיול בלי redeploy.
```sql
CREATE TABLE app_config (
    key TEXT PRIMARY KEY, value TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK (value_type IN ('float','int','str','bool')),
    description TEXT, updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- שורות זרע:
-- ('sideways_threshold_pct', '0.4', 'float', 'סף % סימטרי מהמחיר הייחוס המסווג כ-Sideways')
-- ('confidence_high_cutoff', '0.7', 'float', '...')
-- ('confidence_low_cutoff',  '0.4', 'float', '...')
-- ('min_sample_size',        '15',  'int',   'N מינימלי לפני הצגת תא סטטיסטי כ"מגמה"')
```

### 1.5 מה לא נבנה (במפורש, למניעת over-engineering)
- אין טבלת `catalysts` נפרדת — מערך JSON מספיק, הקטליזטורים הם תצוגתיים בלבד.
- אין טבלאות `users`/הרשאות — כלי פנימי למשתמש יחיד.
- אין `rollup_stats` פיזי — ראו 1.3.
- אין עמודות סף א-סימטרי לשור/דוב — מתועד כהרחבה עתידית אפשרית, לא נבנה כעת.

### 1.6 הערות SQLite מול Postgres
Boolean כ-`Boolean` ORM (לא raw SQL); JSON כ-`JSON` ORM type (Postgres מקבל JSONB
אוטומטית); PK דרך `Integer, primary_key=True` (לא DDL ידני); `CURRENT_TIMESTAMP`
לא לשמש לזמנים קריטיים — לאכוף UTC מפורש בקוד האפליקציה.

---

## 2. מבנה קבצים/מודולים

Python 3.11+, תהליך scheduler ארוך-חיים יחיד (לא OS cron גולמי — כדי לתמוך ב-timezone-aware
triggers, סעיף 6). DB: SQLAlchemy + Alembic, SQLite כברירת מחדל (מוכן ל-Postgres).
UI: **Streamlit** (multipage) — הבחירה המהירה והמתאימה ביותר לכלי אנליטי חד-משתמש עם שני
טאבים של טבלאות/גרפים; אם בעתיד AgentMarket או צרכן חיצוני יצטרכו לקרוא את הנתונים
פרוגרמטית, מוסיפים שכבת FastAPI קריאה-בלבד מעל `storage/` בלי לגעת ב-ingestion/synthesis.

```
fendomental_analysis/
├── README.md
├── pyproject.toml
├── .env.example                     # FMP_API_KEY, FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY, ANTHROPIC_API_KEY, DB_URL
├── alembic.ini
├── alembic/versions/
├── config/settings.py               # pydantic-settings: מפתחות API, DB URL, קבועי tz, שעות jobs
├── src/fendomental/
│   ├── domain/                      # לוגיקה טהורה, בלי I/O, ניתן לבדיקת יחידה מלאה
│   │   ├── enums.py                 # Bias, ConfidenceLevel, JobStatus, ActualDirection
│   │   ├── dto.py                   # EconomicEventDTO, EarningsEventDTO, NewsSnapshotDTO, MarketSnapshotDTO
│   │   ├── classification.py        # classify_actual_direction(), evaluate_success()  (סעיף 5)
│   │   └── stats.py                 # bucket_confidence(), השתקת דגימת-מיעוט
│   ├── ingestion/
│   │   ├── fmp_client.py            # get_economic_calendar(start, end)
│   │   ├── finnhub_client.py        # get_earnings_calendar(start, end, symbols)
│   │   └── weekly_ingestion_job.py
│   ├── market_data/
│   │   └── yfinance_client.py       # get_market_snapshot(), get_closing_price()
│   ├── news/
│   │   ├── alpha_vantage_client.py  # get_news_sentiment(topics, tickers) — מקור ראשי
│   │   ├── finnhub_news_client.py   # get_company_news(symbols) — כותרות גיבוי/תוספת
│   │   └── daily_news_job.py
│   ├── synthesis/
│   │   ├── prompt_builder.py        # build_prompt(events, earnings, news, market) -> (system, user)
│   │   ├── schema.py                # JSON schema / pydantic model לפלט Claude (סעיף 4)
│   │   ├── claude_client.py         # get_structured_forecast(system, user, schema)
│   │   └── synthesis_job.py         # אורכסטרציה של ה-pipeline סביב 16:00
│   ├── verification/
│   │   └── closing_check_job.py
│   ├── storage/
│   │   ├── db.py                    # engine/session factory (SQLite/Postgres דרך DB_URL)
│   │   ├── orm_models.py            # מודלי SQLAlchemy תואמי סעיף 1
│   │   ├── repositories/
│   │   │   ├── forecast_repo.py
│   │   │   ├── result_repo.py
│   │   │   ├── events_repo.py
│   │   │   ├── news_repo.py
│   │   │   ├── market_data_repo.py
│   │   │   ├── job_log_repo.py
│   │   │   └── config_repo.py
│   │   └── queries/stats_queries.py # views/שאילתות מסעיף 1.3
│   ├── scheduler/
│   │   ├── calendar_utils.py        # get_trading_day_type: רגיל/מקוצר/חג, לוח CME futures (pandas_market_calendars)
│   │   ├── jobs.py                  # רישום jobs + cron triggers (סעיף 6)
│   │   └── runner.py                # entrypoint: `python -m fendomental.scheduler.runner`
│   ├── ui/
│   │   ├── streamlit_app.py
│   │   ├── pages/
│   │   │   ├── 1_Daily.py
│   │   │   └── 2_Stats_History.py
│   │   └── components/charts.py
│   └── common/
│       ├── time_utils.py            # המרות tz, UTC normalization
│       ├── retry.py                 # decorator backoff אקספוננציאלי לקריאות API חיצוניות
│       └── exceptions.py
├── scripts/
│   ├── init_db.py
│   ├── run_ingestion_now.py         # הרצה ידנית/backfill, עוקף את ה-scheduler לבדיקות
│   ├── run_synthesis_now.py
│   └── run_closing_check_now.py
└── tests/
    ├── unit/                        # domain/, classification, prompt_builder (LLM מדומה)
    └── integration/                 # repos + orchestration מול קובץ SQLite חד-פעמי
```

---

## 3. ממשקים פנימיים בין הרכיבים

תהליך יחיד — אלו חוזי פונקציה (DTOs ב-`domain/dto.py`), לא API רשתי.

```python
# Ingestion -> Storage -> Synthesis
def get_economic_calendar(start_date: date, end_date: date) -> list[EconomicEventDTO]
def get_earnings_calendar(start_date: date, end_date: date, symbols: list[str]) -> list[EarningsEventDTO]
def run_weekly_ingestion(week_start: date) -> JobResult
def upsert_economic_events(events: list[EconomicEventDTO]) -> int
def upsert_earnings_events(events: list[EarningsEventDTO]) -> int
def get_events_for_date(d: date) -> list[EconomicEvent]
def get_events_for_week(week_start: date) -> list[EconomicEvent]
def get_earnings_for_date(d: date) -> list[EarningsEvent]
def get_current_week_events() -> list[EconomicEvent]          # לטאב היומי ב-UI

# News + Market data -> Synthesis
def fetch_daily_news_sentiment(as_of: date) -> NewsSnapshotDTO   # Alpha Vantage + Finnhub headlines
def save_snapshot(snap: NewsSnapshotDTO) -> int                  # news_repo, מחזיר news_snapshot.id
def get_market_snapshot(as_of_utc: datetime, kind: Literal['pre_open','close']) -> MarketSnapshotDTO
def get_closing_price(ticker: str, as_of_date: date, as_of_time: time | None = None) -> PriceQuote
# as_of_time: שעת הסגירה הרשמית בפועל של היום (מ-get_trading_day_type); None = ברירת המחדל (~17:00 ET)
def save_snapshot(snap: MarketSnapshotDTO) -> int                # market_data_repo

# Synthesis Engine
def build_prompt(events_today, events_week, earnings_today, news, market) -> tuple[str, str]
def get_structured_forecast(system_prompt: str, user_prompt: str) -> ForecastLLMOutput
def run_daily_synthesis(run_date: date) -> DailyForecastRecord

# מה ש-Synthesis כותב ו-Closing Check קורא: כל שורת daily_forecast
def create_forecast(...) -> DailyForecastRecord
def get_forecast_by_date(d: date) -> DailyForecastRecord | None
def get_today_forecast() -> DailyForecastRecord | None          # לטאב היומי

# Verification (Closing Check) — פונקציות טהורות, ראו סעיף 5
def classify_actual_direction(reference_price: float, closing_price: float, threshold_pct: float) -> ActualDirection
def evaluate_success(forecast_bias: Bias, actual_direction: ActualDirection) -> bool | None
def run_closing_check(check_date: date) -> DailyResultRecord
def create_result(forecast_id, closing_price, closing_price_ts_utc, threshold_pct_used,
                   actual_direction, is_success, spread_points, spread_pct) -> DailyResultRecord

# Storage -> UI
def get_success_rate(period: Literal['daily','weekly','monthly'], start: date, end: date) -> StatRow
def get_success_rate_by_confidence() -> list[StatRow]
def get_success_rate_by_weekday() -> list[StatRow]
def get_success_rate_by_weekday_and_confidence() -> list[StatRow]
# StatRow = { label, n, n_success, success_pct, trend_shown }
# trend_shown = (n >= app_config['min_sample_size'])  -- מחושב כאן, לא מסונן מה-n עצמו
```

`config_repo.py` חושף `get_float(key)` / `set_value(key, value)` — משמש גם את Closing
Check (קריאת `sideways_threshold_pct`) וגם קטע "הגדרות" קטן בטאב הסטטיסטיקה, כדי לאפשר
כיול הסף בלי redeploy.

---

## 4. Synthesis Engine — פרומפט מדויק וסכמת פלט

### 4.1 System prompt (סטטי, מגרסה `prompt_version = 'synthesis_v1'`)

```
You are a macroeconomic and fundamental market analyst producing a daily directional
bias forecast for Nasdaq-100 E-mini futures (NQ), for use ahead of the New York trading
session. Your analysis is STRICTLY LIMITED to fundamental and macro factors: economic
data releases, Federal Reserve policy expectations, corporate earnings, news sentiment,
and cross-asset signals (US Dollar Index, US 10-Year Treasury yield, VIX). You must NOT
reference or infer anything from price charts, technical indicators, support/resistance
levels, or market microstructure — none of that data is provided to you, and it is out
of scope for this analysis.

You will be given: today's and this week's scheduled economic-calendar events, today's
scheduled corporate earnings, a structured news-sentiment summary plus supplementary raw
headlines, and a snapshot of current DXY, US10Y yield, VIX, and NQ price levels.

Weigh event importance as follows: High-importance releases (CPI, NFP, FOMC decisions,
PMI, Retail Sales, Jobless Claims flagged High) dominate the bias unless contradicted by
strong, broad-based news sentiment. Earnings from mega-cap technology names (the "Mag7"
and other large tech constituents) can materially move NQ specifically, more than the
broader market, given NQ's sector concentration.

You must produce your answer ONLY by calling the `emit_forecast` tool with a single JSON
object matching its schema. Do not include any prose outside the tool call. If evidence
is mixed or an input category was unavailable, reflect that honestly via the
`confidence_score` and `uncertainty_source` fields rather than defaulting to false
certainty.
```

### 4.2 User prompt (נבנה ע"י `prompt_builder.build_prompt` בכל ריצה)

```
# Analysis date: {forecast_date} (NY trading day)
# Run time: {run_timestamp_israel} (Asia/Jerusalem) / {run_timestamp_ny} (America/New_York)

## Today's scheduled economic events
{לכל אירוע ב-events_today, ממוין לפי importance יורד:}
- [{importance}] {event_time_ny or "time TBD"} — {country}: {event_name}
  (forecast: {forecast_value or "n/a"}, previous: {previous_value or "n/a"})
{אם אין: "- No scheduled high/medium-importance releases today."}

## This week's remaining events (context)
{לכל אירוע ב-events_week כאשר event_date > forecast_date:}
- {event_date} [{importance}] {country}: {event_name}

## Today's scheduled earnings
{לכל earning ב-earnings_today:}
- {symbol} ({company_name}), reporting {session}
  (EPS est: {eps_estimate or "n/a"}, Revenue est: {revenue_estimate or "n/a"})
{אם אין: "- No major earnings scheduled today."}

## News sentiment summary (last 24h, macro + mega-cap tech)
- Structured sentiment score (Alpha Vantage, -1 to +1, relevance-weighted): {sentiment_score}
- Relevance average: {relevance_avg}
- Headline volume considered: {headline_count}
- Supplementary raw headlines (unscored, for contextual reading):
{עד 5 כותרות נוספות מ-Finnhub/RSS:}
  - "{headline_text}" ({source}, {published_at_ny})
{אם אין נתוני סנטימנט מובנה: "- WARNING: structured sentiment unavailable for this run; base your read only on the raw headlines below."}

## Market data snapshot (captured {captured_at_ny})
- NQ reference price: {nq_price}  (prior close: {nq_prior_close}, change: {nq_change_pct}%)
- US Dollar Index (DXY): {dxy}
- US 10-Year Treasury yield: {us10y_yield}%
- VIX: {vix}

## Task
Based only on the above, determine today's directional bias for NQ into the New York
session. Call `emit_forecast` with your structured answer.
```

טיפול בקלט חסר: כל סעיף שהמידע שלו נכשל בשליפה מוצג כשורת `WARNING: ... unavailable`
מפורשת (לא מושמט בשקט), כך שהמודל יכול להוריד confidence / לצטט זאת כ-`uncertainty_source`.

### 4.3 סכמת פלט — Claude tool-use מאולץ ל-JSON

```python
FORECAST_TOOL_SCHEMA = {
    "name": "emit_forecast",
    "description": "Emit the structured daily NQ bias forecast.",
    "input_schema": {
        "type": "object",
        "properties": {
            "bias": {
                "type": "string", "enum": ["Bullish", "Bearish", "Sideways"],
                "description": "Directional bias for NQ for today's NY session."
            },
            "confidence_score": {
                "type": "number", "minimum": 0.0, "maximum": 1.0,
                "description": "Model's confidence in the bias call, 0.0 to 1.0."
            },
            "uncertainty_source": {
                "type": ["string", "null"],
                "description": "Primary source of uncertainty or conflicting signal, if any; null if none."
            },
            "key_catalysts": {
                "type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5,
                "description": "1-5 short bullet strings naming the specific events/news/data driving the bias."
            },
            "rationale": {
                "type": "string",
                "description": "1-3 sentence plain-language explanation, for display in the UI."
            }
        },
        "required": ["bias", "confidence_score", "key_catalysts", "rationale"]
    }
}
```

קריאה: `tools=[FORECAST_TOOL_SCHEMA], tool_choice={"type": "tool", "name": "emit_forecast"}`,
`model_id` נקרא מ-`settings`/`app_config` (לא hardcoded) כדי לאפשר שדרוג מודל בלי שינוי קוד.
`claude_client.get_structured_forecast` מוודא את הפלט מול מודל pydantic מקביל לפני החזרה;
כשל ולידציה = כשל job (ניסיון חוזר אחד, ואז `status='FAILED'`).

---

## 5. לוגיקת סיווג Bullish / Bearish / Sideways

פונקציות טהורות, דטרמיניסטיות לחלוטין, ניתנות לבדיקת יחידה מלאה:

```python
def classify_actual_direction(reference_price: float, closing_price: float, threshold_pct: float) -> ActualDirection:
    """
    threshold_pct: לדוגמה 0.4 פירושו 0.4%, לא 0.004. סימטרי סביב אפס.
    בסיס: אחוז שינוי יחסית ל-reference_price (לא נקודות מוחלטות).
    """
    if reference_price is None or closing_price is None or reference_price == 0:
        return ActualDirection.UNKNOWN
    pct_change = (closing_price - reference_price) / reference_price * 100.0
    if pct_change > threshold_pct:
        return ActualDirection.BULLISH
    elif pct_change < -threshold_pct:
        return ActualDirection.BEARISH
    else:
        return ActualDirection.SIDEWAYS   # כולל בדיוק +threshold_pct/-threshold_pct

def evaluate_success(forecast_bias: Bias, actual_direction: ActualDirection) -> bool | None:
    if actual_direction == ActualDirection.UNKNOWN:
        return None    # לא נספר במכנה הסטטיסטי, לא נחשב ככישלון
    return forecast_bias.value == actual_direction.value
```

מקרי קצה שהוכרעו במפורש:
- **בסיס החישוב**: אחוז יחסית ל-`reference_price` (נלכד ~09:00 ET, לפני פתיחת NY) מול
  `closing_price` הנלכד בתום חלון הסשן הרציף (~17:00 ET / 00:00 ישראל, ראו החלטה למעלה)
  — לא נקודות מוחלטות.
- **גבול הסף**: `>`/`<` חדים — תזוזה שנוחתת **בדיוק** על +threshold או -threshold מסווגת
  **Sideways** (מוסכמה שמרנית). לא הוגדר בבריף המקורי, לכן מתועד כאן במפורש.
- **סימטריה**: הסף סימטרי בשלב א'. סף א-סימטרי (שור/דוב) הוא הרחבה עתידית אפשרית —
  שינוי של שתי שורות ב-`app_config` ו-`if` אחד, בלי שינוי סכמה.
- **ערך ברירת מחדל**: `app_config.sideways_threshold_pct = 0.4` (אמצע טווח 0.3%-0.5%
  שהבריף הציע), ניתן לשינוי דרך ה-UI. כל שורת `daily_result` שומרת את הסף שבו נעשה
  שימוש בפועל (`threshold_pct_used`) — כך שינוי עתידי לא "מזהם" סטטיסטיקה היסטורית.
- **נתוני מחיר חסרים**: `actual_direction='UNKNOWN'`, `is_success=NULL`, מוחרג מכל
  חישובי `success_pct`/`n` (`WHERE is_success IS NOT NULL`) — תקלת נתונים לעולם לא
  נספרת בשקט כהפסד או כהצלחה.
- **בלי ניקוד חלקי**: תחזית Sideways שהתבררה כ-Bullish בקושי (למשל +0.9% מול סף 0.4%)
  היא כישלון מלא, בדיוק כמו תחזית הפוכה לגמרי. ניקוד יחסי-למרחק מחוץ לתחום שלב א'.

---

## 6. תזמון Jobs

Scheduler: APScheduler בתוך תהליך `scheduler/runner.py` ארוך-חיים (לא OS cron גולמי),
עם `CronTrigger` מודע-timezone. `misfire_grace_time` + `coalesce=True` בכל ה-jobs כדי
שהפעלה מחדש קצרה של התהליך לא תגרום להרצות כפולות/מצטברות.

**ההחלטה שפותרת את בעיית חוסר-ההתאמה בין שעון ישראל לשעון ארה"ב**: שני ה-jobs
המסחריים (Synthesis, Closing Check) מתוזמנים לפי אזור הזמן **`America/New_York`**,
לא `Asia/Jerusalem`. כיוון ש-`CronTrigger(timezone='America/New_York')` מוערך מול שעון
הקיר המקומי של ניו יורק (כולל מעבר הקיץ/חורף שלה עצמה), ה-job תמיד יורה באותו היסט
קבוע מהסשן האמיתי של ניו יורק, בלי קשר למה שהשעון בישראל עושה. תאריכי מעבר השעון
בישראל (בד"כ יום שישי שלפני יום ראשון האחרון של מרץ, ויום ראשון האחרון של אוקטובר —
לא תואמים לכלל האמריקאי) רק משפיעים על **איך** הרגע הזה ייראה על שעון קיר ישראלי —
ב-2 עד 4 שבועות בכל אביב וסתיו הוא "יזוז" שעה על השעון הישראלי (15:00 או 17:00 במקום
16:00), אבל ה-job ימשיך לפעול נכון כי המטרה היא "30 דקות לפני פתיחת NY", לא "16:00
שעון ישראל". ה-ingestion השבועי, שאין לו תלות בסשן מסחר, מתוזמן לפי `Asia/Jerusalem`
כי האילוץ היחיד שלו הוא "מתישהו בסוף השבוע לפני יום שני".

```python
# scheduler/jobs.py

# 1. Ingestion שבועי — הרצה עיקרית מוצ"ש/יום ראשון בערב שעון ישראל
scheduler.add_job(run_weekly_ingestion, trigger=CronTrigger(
    day_of_week='sun', hour=20, minute=0, timezone='Asia/Jerusalem'),
    id='weekly_ingestion_primary', misfire_grace_time=3600, coalesce=True)

# 1b. הרצה חוזרת/backfill ביום שני בבוקר (upsert אידמפוטנטי — מכסה נתונים ש-FMP/Finnhub
#     עדיין לא פרסמו בסוף השבוע)
scheduler.add_job(run_weekly_ingestion, trigger=CronTrigger(
    day_of_week='mon', hour=6, minute=30, timezone='Asia/Jerusalem'),
    id='weekly_ingestion_backfill', misfire_grace_time=3600, coalesce=True)

# 2. Daily News + Synthesis — 30 דקות לפני פתיחת NY (09:30 ET), א'-ה' (Mon-Fri)
#    בשעון קיר ישראלי זה ~16:00 ברוב השנה, חוץ משבועות חוסר-ההתאמה.
scheduler.add_job(run_daily_synthesis_pipeline, trigger=CronTrigger(
    day_of_week='mon-fri', hour=9, minute=0, timezone='America/New_York'),
    id='daily_news_synthesis', misfire_grace_time=900, coalesce=True)

# 3. Closing Check — תום חלון הסשן הרציף כפי שהבריף הגדיר (17:00 ET = 00:00 ישראל)
#    + 15 דק' buffer לזמינות נתונים. שעת השליפה בפועל של מחיר הסגירה מותאמת ליום
#    מקוצר על ידי get_trading_day_type (ראו בהמשך) — ה-trigger הקבוע הוא רק "מתי
#    ה-job מתעורר", לא בהכרח השעה שממנה נשלף המחיר.
scheduler.add_job(run_closing_check_pipeline, trigger=CronTrigger(
    day_of_week='mon-fri', hour=17, minute=15, timezone='America/New_York'),
    id='closing_check', misfire_grace_time=1800, coalesce=True)
```

שני ה-jobs המסחריים בודקים בתחילתם `scheduler/calendar_utils.py::get_trading_day_type(date)`
— פונקציה שמבחינה בין `'regular'` / `'early_close'` / `'holiday'`, מבוססת על
`pandas_market_calendars.get_calendar('CME_Equity').schedule()` (לוח חוזי CME, לא NYSE
cash — כי המערכת עוקבת אחר NQ עצמו, וללוחות שונים יש שעות חג/קיצור שונות; יש לוודא את
שם ה-calendar המדויק הזמין בספרייה בזמן המימוש). ביום `'holiday'` — `status='SKIPPED'`
ב-`job_run_log`, בלי שורת forecast/result, כלומר לא נכנס למכנה הסטטיסטי. ביום
`'early_close'` (כמו יום אחרי חג ההודיה) — **בניגוד להנחה מוקדמת ושגויה**, חוזי NQ
ממשיכים להיסחר בערב גם בימים כאלה, בנפח נמוך יותר, ולא "קופאים"; לכן ה-Closing Check
לא יכול להסתמך על שעת ברירת המחדל (17:00 ET) אלא שולף מ-`get_trading_day_type`/
`schedule()` את שעת הסגירה הרשמית **בפועל** של אותו יום (שיכולה להיות מוקדמת יותר,
למשל ~13:15 ET) ומעביר אותה כפרמטר ל-`get_closing_price(ticker, as_of_date,
as_of_time=actual_close_time)` — כך שהמחיר שנלכד הוא אכן מחיר הסגירה הרשמי של אותו
יום מקוצר, לא מחיר מאמצע הסשן הרגיל שכבר חלף.

---

## 7. פערים, אי-בהירויות וסיכונים לוודא לפני/תוך כדי הבנייה

1. **קלנדר כלכלי FMP** — יש לוודא שה-endpoint הספציפי לקלנדר כלכלי כלול ב-free tier
   (יש היסטוריה של הגבלת endpoints מסוימים לתוכניות בתשלום ב-FMP).
2. **קלנדר דוחות רבעוניים Finnhub** — לוודא זמינות ב-free tier למגבלת הקריאות (60/דקה),
   ושרשימת Mag7+טכנולוגיה מובילה מוגדרת כרשימת סימבולים קבועה ב-config (לא נגזרת דינמית).
3. **Alpha Vantage NEWS_SENTIMENT** — free tier נדיב מספיק לקריאה אחת ביום, אבל מדיניות
   ה-rate limit של Alpha Vantage השתנתה כמה פעמים בעבר — לוודא את המגבלה הנוכחית לפני
   סמיכה עליה כמקור יחיד; ה-fallback לכותרות Finnhub/RSS גולמיות (סעיף 4) הוא בדיוק
   הביטוח מפני זה.
4. **yfinance הוא מקור לא רשמי** (scraping, בלי SLA) — יכול לשנות פורמט תגובה או להיחסם
   ברמת IP בלי אזהרה. `reference_price`/`closing_price` הם "המחיר האחרון ש-yfinance
   החזיר בזמן השליפה", לא ציטוט בורסה מוסמך — יש לתעד את זה גם ב-UI, לא רק כאן.
5. **NQ=F הוא חוזה כמעט-רציף** — העיגון ל-09:00 ET (לפני פתיחת NY, `reference_price`)
   ול-~17:00 ET (תום חלון הסשן הרציף שהבריף הגדיר, `closing_price`) הוא מוסכמה מכוונת
   שתועדה ואושרה, ולא סגירת ה-cash market של NYSE — לא ברירת מחדל שנבחרה בטעות.
6. **מדיניות קלט חלקי** — אם FMP מצליח אבל Alpha Vantage/Finnhub נכשלים, Synthesis
   ממשיך עם אזהרה מוטמעת בפרומפט (לא מבטל את הריצה). מדיניות מחמירה יותר (לבטל אם
   קלט קריטי חסר ביום עם FOMC/CPI מתוכנן) היא החלטת מוצר עתידית אפשרית, לא ברירת מחדל.
7. **כשל Synthesis** — נוצרת שורת `daily_forecast` עם `status='FAILED'`, `bias=NULL`
   (לא שורה חסרה לגמרי), כך שהיום מופיע בהיסטוריה כ"נוסה, בלי תוצאה". Closing Check
   בודק `status=='SUCCESS'` לפני הערכה; יום כושל לא מייצר שורת `daily_result` כלל.
8. **תאריך מסחר קנוני** — `forecast_date`/`result_date` הם התאריך הקלנדרי בניו יורק
   בזמן ריצת ה-09:00 ET, לא התאריך הישראלי — מונע off-by-one בפילוח לפי יום בשבוע.
9. **מסגרת overfitting** — נבנתה רק שכבת ההגנה בתצוגה (השתקת תא עם `n < min_sample_size`,
   ברירת מחדל 15). בקצב של תחזית אחת ליום, תא בודד של יום-בשבוע מגיע ל-n≥15 אחרי כ-3
   חודשי הפעלה חיה; קומבינציה של יום×confidence לוקחת הרבה יותר. ה-UI צריך להראות את
   הציפייה הזו, לא טבלה ריקה מבלבלת. מסגרת Train/Validation/Test מלאה (חלוקה כרונולוגית,
   לא אקראית) רלוונטית ל-Phase B, כשיהיה מספיק היסטוריה — הסכמה כבר תומכת בכך בחינם כי
   `model_id`/`prompt_version` נשמרים לכל תחזית.
10. **אידמפוטנטיות ingestion** — ה-job השבועי רץ פעמיים (א'+ב') בכוונה; אילוצי `UNIQUE`
    + upsert (`INSERT ... ON CONFLICT DO UPDATE`) נדרשים כדי שהרצה חוזרת לא תשכפל שורות
    כשה-forecast value מתעדכן בין הריצות.
11. **סודות** — `ANTHROPIC_API_KEY`/`FMP_API_KEY`/`FINNHUB_API_KEY`/`ALPHA_VANTAGE_API_KEY`
    ב-environment variables בלבד (`.env` ב-gitignore), לעולם לא ב-`app_config` או
    ב-`job_run_log.metadata_json`/`raw_llm_response_json` — עמודות ה-audit האלה נועדו
    לתעד הכל, ובקלות אפשר בטעות ללכוד שם מפתח.

---

## אימות (Verification)

לאחר המימוש:
1. `pytest tests/unit` — בדיקות יחידה ל-`classification.py` (כל מקרי הקצה בסעיף 5),
   `prompt_builder.py` (עם קלטים חסרים/מלאים), ו-`stats.py`.
2. `python scripts/init_db.py` ואז `python scripts/run_ingestion_now.py` — לוודא
   שקריאות FMP/Finnhub אמיתיות עובדות ומוכנסות ל-DB בלי שגיאת schema.
3. `python scripts/run_synthesis_now.py --date <יום מסחר קרוב>` — הרצה ידנית מול Claude
   API אמיתי, בדיקה ידנית שה-JSON חוזר תקין ומתאים לסכמה.
4. `python scripts/run_closing_check_now.py --date <אותו יום>` (בדימוי, אחרי סגירה) —
   לוודא חישוב סיווג נכון מול מחיר סגירה אמיתי.
5. `streamlit run src/fendomental/ui/streamlit_app.py` — לוודא שני הטאבים מציגים נתונים
   אמיתיים מה-DB, כולל N לצד כל אחוז הצלחה.
6. הרצת המערכת "בחי" למשך כמה ימי מסחר ובדיקה ש-`job_run_log` מתעד הצלחה/כשל נכון,
   ושה-scheduler לא מפספס/מכפיל הרצות סביב שינוי שעון (אם רלוונטי בטווח הבדיקה) וסביב
   יום מסחר מקוצר (יש לוודא ש-`get_trading_day_type` מזהה נכון ושמחיר הסגירה נשלף
   מהשעה הרשמית בפועל של אותו יום, לא מ-17:00 ET הקבוע).
