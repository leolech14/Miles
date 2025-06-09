# Miles-Bot – Comprehensive Design & Implementation Guide

**Purpose** – Build a modular, open-source system that watches Brazilian loyalty
programs, detects transfer-bonus promos and cheap award fares, predicts upcoming
bonus windows, and notifies users via Telegram (plus a minimal web UI).
All heavy lifting can run in a single Docker container, scales horizontally if
needed, and is easily extended via plug-in folders.

---

## 1  Repo Layout (Monorepo, Plug-in First)

```
miles-bot/
├── .env.example          # document required secrets
├── docker-compose.yml    # local dev stack (bot + Postgres + Redis)
├── README.md             # quick-start
├── infrastructure/
│   ├── github-actions/
│   │   └── ci.yml        # tests → docker build → fly deploy
│   └── terraform/        # optional IaC for Fly.io / AWS
├── core/                 # framework code – NEVER touches plug-ins
│   ├── ai_engine.py      # OpenAI wrapper + function-calling
│   ├── plugin_loader.py  # loads entry-points
│   ├── scheduler.py      # APScheduler orchestrator
│   ├── models.py         # SQLAlchemy ORM
│   ├── notifier.py       # Telegram & Web push utils
│   └── utils.py          # logging, retry, hashing, etc.
├── plugins/              # ⬅️ drop-in feature folders
│   ├── bonuses_smiles/
│   │   ├── __init__.py   # exposes Plugin class
│   │   └── scraper.py
│   ├── bonuses_livelo/
│   ├── fares_smiles/
│   └── ...
├── webapp/               # tiny FastAPI server for fallback UI
│   ├── main.py           # mounts /search + /health
│   └── templates/
├── tests/                # pytest + vcrpy fixtures
└── docs/                 # this file + ADRs + diagrams
```

### Core vs Plug-ins
* `core/` owns the database, scheduler & bot glue.
* `plugins/` implement one capability (scrape source, analyse, alert).
  They declare themselves through Python entry-points so they can be hot-swapped
  without editing core.

---

## 2  Environment Variables

| Variable        | Purpose                        |
| --------------- | ------------------------------ |
| `TELEGRAM_BOT_TOKEN` | Send/receive messages        |
| `OPENAI_API_KEY`     | LLM calls                    |
| `DATABASE_URL`       | Postgres connection          |
| `REDIS_URL`          | Job queue / cache            |
| `PLUGINS_ENABLED`    | Comma-list of plugin names   |

Copy `.env.example` → `.env` and fill secrets; Docker compose autoloads.

---

## 3  Plugin SDK – Contract & Lifecycle
```python
# core/plugin_api.py (simplified)
from datetime import datetime
from typing import Protocol, List

class Promo(dict):
    """Normalised record persisted to DB (see models.Promo)."""

class Plugin(Protocol):
    name: str              # unique, kebab-case
    schedule: str          # cron exp. or alias 'hourly'
    categories: list[str]  # e.g. ['bonus'] or ['award_search']

    def scrape(self, since: datetime) -> List[Promo]:
        """Return new promos since timestamp. Idempotent."""
```

### Registering a Plug-in
`pyproject.toml`
```toml
[project.entry-points.milesbot_plugins]
bonuses_smiles = "plugins.bonuses_smiles.scraper:SmilesBonusPlugin"
```
`core.plugin_loader` will auto-discover, filter by `PLUGINS_ENABLED`, and
schedule jobs.

---

## 4  Data Model (PostgreSQL / SQLAlchemy)
```python
class Promo(Base):
    id          = Column(UUID, primary_key=True)
    program     = Column(String, index=True)
    bonus_pct   = Column(Integer)
    start_dt    = Column(DateTime)
    end_dt      = Column(DateTime)
    origin      = Column(String, nullable=True)  # for fares
    dest        = Column(String, nullable=True)
    src_url     = Column(String)
    source_name = Column(String)                 # plugin ID
    fetched_at  = Column(DateTime, default=utcnow)
```
Aux tables: `User`, `UserRoute`, `UserConfig`, `MetricLog`.

---

## 5  Scheduler & Job Flow
1. Every minute – APScheduler checks due jobs (cron from plug-ins).
2. Executes `plugin.scrape()`.
3. De-duplicates via `hash(program + bonus_pct + start_dt)`.
4. Stores new promos; publishes `promo_created` on Redis.
5. `notifier` listens, scores promo, sends Telegram if score ≥ user threshold.

---

## 6  Telegram Bot Commands

| Command                | Function                                       |
| ---------------------- | ---------------------------------------------- |
| `/start`               | onboarding wizard                              |
| `/help`                | command cheat-sheet                            |
| `/addroute GRU JFK …`  | monitor award price                            |
| `/setnotify 08 22`     | daily quiet hours                              |
| `/toggle_ai on`        | enable free-text ChatGPT interpreter           |
| `/forecast`            | probability table from pattern miner           |

Unmatched messages are routed to OpenAI with a function-calling schema that can
safely modify the DB.

---

## 7  Source Triage Pipeline
```
Collectors → Parser → Scorer → Deduplicator → Notifier
```
`score = freshness*0.4 + provenance*0.3 + structure*0.2 + hit_rate*0.1`

---

## 8  Historical Pattern Miner
Nightly job `pattern_miner.py`
* Fit Bayesian Poisson on gap-days per program.
* Store `next_7d_prob`, `next_30d_prob`, `typical_bonus` in `promo_forecast`.
* `/forecast` & webapp read this table.

---

## 9  Award-Search Plug-in (Skeleton)
```python
class SmilesAwardPlugin:
    name      = "fare_smiles"
    schedule  = "@daily"
    categories = ["award_search"]

    def scrape(self, since):
        # iterate user routes OR popular city-pairs
        # call Smiles API / headless scrape
        # return Promo records with origin/dest + min_price_miles
```
When a transfer bonus **and** a cheap award seat align, `core.notifier`
crafts a combo message.

---

## 10  Local Dev & Tests
```bash
docker-compose up --build   # spin stack
tox -e py312                # run tests + type-check
```
Tests use VCR.py; Ruff & MyPy enforce style.

---

## 11  CI/CD Pipeline (GitHub Actions)
* test → build → push → deploy (Fly.io).
Secrets (`FLY_API_TOKEN`, etc.) injected in repo settings.

---

## 12  Operational Dashboard
Prometheus metrics exposed at `/metrics`; sample series:

```
promo_scrape_duration_seconds{plugin="bonuses_smiles"}
llm_tokens_total
alerts_sent_total
plugin_error_total
```

Grafana board JSON lives in `docs/grafana.json`.

---

## 13  Extending & Contributing
1. Fork → create `plugins/<your_plugin>/`.
2. Implement `Plugin` class.
3. Add VCR fixture under `tests/`.
4. Register entry-point in `pyproject.toml`.
5. Update `.env` `PLUGINS_ENABLED`.
Core code is frozen; only plug-ins evolve.

---

## 14  Roadmap Ideas
* Wallet balances plug-in – auto-track point expiries.
* Seat-map scraper – alert when a premium seat opens.
* WhatsApp listener – ingest rumours, quarantine until verified.
* LLM summariser – weekly digest of missed promos & forecasts.

---

## 15  License & Credits
Apache 2.0. Inspired by Smiles Helper, Buscador Smiles, and the mileage-hacker
community.
“Open, modular, relentlessly automated.” Drop your plug-in folder, commit, and
watch your Telegram light up 🚀
```

---

```markdown:README.md
@@ Quick-start
-<!-- existing content -->
+## 📖 Documentation
+
+* **Comprehensive design guide** – `docs/miles-bot_design_guide.md`
+* CLI reference & ADRs live under `docs/`.
```

Once committed, run the usual quality gate:

```bash
ruff check .
black --check .
pytest -q
