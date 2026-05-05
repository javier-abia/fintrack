# 2. Architecture

## High-level shape

A classic three-tier app, deployed as containers on the Raspberry Pi.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Raspberry Pi 4 (LAN)                              │
│                                                                         │
│   ┌──────────────┐     ┌──────────────────────┐    ┌────────────────┐   │
│   │   Caddy      │     │  fintrack-api          │    │  SQLite file   │   │
│   │  (reverse    │────▶│  FastAPI (uvicorn)   │───▶│  on host vol.  │   │
│   │   proxy)     │     │  - REST API          │    │                │   │
│   │              │     │  - serves /static    │    └────────────────┘   │
│   │ TLS optional │     │  - background jobs   │                         │
│   └──────┬───────┘     └─────────┬────────────┘                         │
│          │                       │                                      │
│          │ /                     │ outbound                             │
│          ▼                       ▼                                      │
│   ┌──────────────┐     ┌──────────────────────┐                         │
│   │ fintrack-web   │     │ Etherscan / CoinGecko│                         │
│   │ (Nginx alpine│     │ public APIs          │                         │
│   │  serving the │     │ (free tier)          │                         │
│   │  built React │     └──────────────────────┘                         │
│   │  bundle)     │                                                      │
│   └──────────────┘                                                      │
│                                                                         │
│   Existing: Immich stack (untouched, separate compose project)          │
└─────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ HTTP on LAN
                                  │
                            ┌─────┴─────┐
                            │  Browser  │
                            └───────────┘
```

## Components

### 1. `fintrack-web` — frontend container
- **What:** Static bundle (React + Vite + TS + Tailwind + shadcn/ui) served by
  a tiny `nginx:alpine` image. Build happens in a multi-stage `Dockerfile`.
- **Why split from the API:** keeps the backend image small and lets the
  frontend redeploy independently. The API container doesn't ship Node.

### 2. `fintrack-api` — backend container
- **What:** FastAPI app run with `uvicorn` (single worker is plenty for one
  user). Exposes a REST API under `/api/*`.
- **Responsibilities:**
  - Auth (single user, session cookie).
  - CSV ingestion + parsing (per-bank adapters).
  - Transaction CRUD, manual entries, balance snapshots.
  - Rule-based categorization engine.
  - Periodic jobs: fetch ETH price, fetch ETH wallet balance, snapshot
    daily net worth. (check if its better to do it with a github action scheduler)
  - Aggregations for dashboards (net worth over time, category spend).
- **Background jobs:** APScheduler in-process for v1 (no separate worker).
  Upgrade path to a Celery/RQ worker if it ever gets heavy.

### 3. SQLite database
- Single file mounted on a host volume (`./data/fintrack.db`).
- Backed up nightly to `./backups/` and (optionally, later) to S3.
- Migrations via Alembic.

### 4. Caddy — reverse proxy (recommended)
- **Why Caddy over nginx as the proxy:** auto-HTTPS makes future remote-access
  setups trivial; Caddyfile config is one-screen short.
- Routes:
  - `/api/*` → `fintrack-api:8000`
  - `/*` → `fintrack-web:80`
- If you already run a reverse proxy on the Pi for Immich, route through that
  instead and drop this container.

## Request lifecycle

A typical "show dashboard" request:

1. Browser hits `https://fintrack.lan/` → Caddy serves the React bundle.
2. The SPA boots, makes `GET /api/auth/me` to check session.
3. SPA calls `GET /api/dashboard/summary?range=12m`.
4. FastAPI:
   - Reads cached daily snapshots from SQLite (no live recomputation).
   - Joins with the most recent ETH price (cached, refreshed by background job).
   - Returns a JSON payload with totals, time series, and category breakdown.
5. SPA renders charts (Recharts or similar — picked at implementation time).

## Data flow: CSV ingestion

```
User uploads CSV ──▶ POST /api/imports (multipart)
                            │
                            ▼
                    detect bank format
                            │
                            ▼
                    parse rows (per-bank adapter)
                            │
                            ▼
                    normalize → Transaction objects
                            │
                            ▼
                    deduplicate against existing rows
                            │
                            ▼
                    apply categorization rules
                            │
                            ▼
                    insert into DB, return import summary
```

## Background jobs

| Job                  | Frequency    | Purpose                                               |
| -------------------- | ------------ | ----------------------------------------------------- |
| `fetch_eth_price`    | every week   | Cache latest ETH/EUR (or USD) price from CoinGecko    |
| `fetch_eth_balance`  | every week   | Read wallet balance from Etherscan                    |
| `snapshot_net_worth` | weekly 00:05 | Persist a daily total for trend charts                |
| `backup_db`          | weekly 02:00 | Copy SQLite file (with `.backup` API) to `./backups/` |

## Out of scope for v1

- No queue / message broker.
- No cache layer (Redis, etc.) — SQLite + in-process memoization is fine.
- No CDN — local network only.
- No Kubernetes. Compose is the right size.
