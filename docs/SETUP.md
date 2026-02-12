# Setup Guide

This guide is intentionally implementation-oriented. Follow in order to stand up a local development instance quickly.

## 1) Runtime prerequisites

- Python `3.11+`
- `uv` (preferred) or `pip`
- Docker + Docker Compose (for local Postgres/Redis)
- FFmpeg (for video render pipeline)

## 2) Required environment variables

Create `.env.local` in the repository root.

```bash
# ---------- Core runtime ----------
APP_ENV=local
LOG_LEVEL=INFO
TIMEZONE=UTC

# ---------- Storage ----------
DATABASE_URL=postgresql+psycopg://content_user:content_pass@localhost:5432/content_automation
REDIS_URL=redis://localhost:6379/0

# ---------- LLM + media generation ----------
OPENAI_API_KEY=sk-...
OPENAI_MODEL_PLANNER=gpt-4.1
OPENAI_MODEL_CREATIVE=gpt-4.1
IMAGE_MODEL=gpt-image-1

# ---------- Instagram integration ----------
INSTAGRAM_APP_ID=...
INSTAGRAM_APP_SECRET=...
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...

# ---------- Trend intelligence ----------
SERPAPI_API_KEY=...
YOUTUBE_API_KEY=...

# ---------- Observability ----------
SENTRY_DSN=...
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

### Variable notes

- `DATABASE_URL` and `REDIS_URL` are mandatory even in local mode.
- `INSTAGRAM_*` values should point to a non-production sandbox account for development.
- `OPENAI_MODEL_*` variables let you tune cost/perf independently for planning vs generation.

## 3) Local secrets handling

Rules for engineers:

1. Never commit `.env.local`, `.env.*`, raw API keys, or service account files.
2. Keep a committed template in `.env.example` (create and maintain as env vars evolve).
3. In shared environments (staging/prod), inject secrets via secret manager (AWS Secrets Manager, Doppler, Vault, etc.), not via committed files.
4. Rotate keys every 90 days or immediately after accidental exposure.
5. Restrict Instagram and model provider keys to least privileges needed.

## 4) Start local dependencies

```bash
docker compose up -d postgres redis
```

Expected outcome:

- Postgres on `localhost:5432`
- Redis on `localhost:6379`

## 5) Install project dependencies

Using `uv`:

```bash
uv sync
```

Fallback with `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 6) Run database migrations

```bash
uv run alembic upgrade head
```

If no migration framework exists yet, initialize schema manually from bootstrap SQL and add Alembic in the first implementation sprint.

## 7) Run the automation loop locally

Single-loop dry run:

```bash
uv run python -m src.main --mode dry-run --once
```

Continuous local scheduler mode:

```bash
uv run python -m src.main --mode local --interval-seconds 900
```

## 8) Recommended first verification checks

```bash
uv run python -m src.main --mode dry-run --once --topic "ai productivity"
uv run pytest -q
uv run ruff check .
```

Success criteria:

- planner creates a content plan record
- creative step emits at least one candidate post payload
- no publish call is made during dry run

## 9) Security and compliance guardrails

Before enabling real publishing:

- Add brand safety validation for banned terms and legal claims.
- Require approval mode for new prompts/templates.
- Enable redaction in logs for tokens/secrets and PII.
- Store audit trail for generated assets and publish decisions.
