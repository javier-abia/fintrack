# 3. Tech stack

Each choice below lists **what**, **why**, and a realistic **alternative** so you
can revisit decisions later.

## Backend

### Language & runtime: Python 3.12+
- **Why:** Owner is Python-focused; richest ecosystem for the data-shaped parts
  (CSV parsing, pandas if needed, finance libraries).
- **Alt:** Node/TS (would unify with frontend) or Go (great for Pi performance).
  Not chosen because learning Python web stack is the priority.

### Web framework: FastAPI
- **Why:** modern, async-first, auto-generates OpenAPI docs (great for learning
  API design), Pydantic v2 integration is excellent.
- **Alt:** Django (heavier, batteries-included), Flask (older, less typed).

### ORM / DB toolkit: SQLAlchemy 2.x + Alembic
- **Why:** the de-facto standard. SQLAlchemy 2.0 syntax is much cleaner than 1.x
  and worth learning. Alembic for migrations from day one — never edit schemas
  by hand.
- **Alt:** SQLModel (built on SQLAlchemy + Pydantic; nice but thinner docs),
  Tortoise ORM, raw SQL via `databases` package.

### Validation: Pydantic v2
- Already comes with FastAPI. Use it for request/response models *and*
  for parsing CSV row dicts before persisting (catches schema drift early).

### Scheduler: APScheduler (in-process)
- **Why:** dead-simple cron-like jobs running in the same process as the API.
  Sufficient for a 4-job workload.
- **Alt:** Celery + Redis (way overkill for v1), or system cron calling
  CLI scripts.

### Auth
- **v1:** simple session cookie auth, single hard-coded user, password hashed
  with `passlib[bcrypt]`. No registration flow.
- **Why:** zero external deps, no JWT pitfalls, perfectly fine for one user
  behind a LAN.
- **Future:** if remote access is enabled, add 2FA via `pyotp` (TOTP) before
  exposing publicly.

### Testing: pytest + httpx + pytest-asyncio
- Use FastAPI's `TestClient` and a temporary SQLite file per test session.

### Tooling: `uv` for env + lockfile, `ruff` for lint+format, `mypy --strict`
- **Why uv over pip/poetry:** dramatically faster, single tool, lockfile baked
  in. Modern best-practice for new Python projects.
- See [`08-dev-tooling.md`](08-dev-tooling.md) for configs, daily commands,
  and the recommended learning order.

## Frontend

### Framework: React 18 + Vite + TypeScript
- **Why:** the AI-coding tools (Claude, v0.dev, Cursor) generate React+TS more
  reliably than any other stack — directly leverages your "AI-driven design"
  workflow. TypeScript catches enough that you don't have to learn deep React
  patterns up front.
- **Alt 1: HTMX + Jinja templates.** Pure-Python feel, no build step. Genuinely
  considered — rejected because it limits what AI design tools can output and
  you said you want "control" plus a *bit* of frontend learning.
- **Alt 2: Next.js.** Overkill for a SPA hitting a separate API. Adds SSR
  complexity you don't need. Reach for it only if you start needing SEO or
  edge-rendered marketing pages (you won't).

### Styling: Tailwind CSS
- **Why:** zero context-switch between markup and styles; AI tools produce
  excellent Tailwind output; no CSS-modules or styled-components ceremony.

### Component library: shadcn/ui
- **Why:** copy-paste components built on Radix + Tailwind. You own the source,
  so you can customize freely. AI tools know shadcn idioms cold.
- **Alt:** Mantine, Chakra UI, MUI. All fine — shadcn wins on AI-friendliness
  and "no runtime dependency" hygiene.

### Charts: Recharts (decide at impl time)
- Defer the final pick — likely Recharts for ergonomics, or Visx if you want
  more control.

### State / data fetching: TanStack Query (React Query)
- **Why:** standard for talking to a REST API; gives you caching, optimistic
  updates, and refetch logic for free.

### Forms: react-hook-form + Zod
- Validation schemas in Zod can mirror your Pydantic schemas on the backend.

## Database

### v1: SQLite
- **Why:** single user, low write volume, embedded, trivial backups (just copy
  the file), excellent on a Pi.
- **Limit:** if you ever want concurrent writers or remote DB access, migrate
  to Postgres. The SQLAlchemy code is portable.

### Migration path: PostgreSQL 16
- Add a `postgres` service to `docker-compose.yml`, change the SQLAlchemy URL,
  run Alembic. Defer until you have a concrete reason.

## Infrastructure

### Containerization: Docker + Docker Compose
- One `docker-compose.yml` per *project*, distinct from the Immich one. Don't
  merge them — keep their lifecycles independent.
- Use named volumes for the DB and bind mounts only for `./backups`.

### Reverse proxy: Caddy
- **Why:** auto-HTTPS, one-line config, handles the TLS story when you later
  expose the app remotely. Already covered in [architecture](02-architecture.md).
- **Alt:** Traefik (more powerful, more config). Nginx (manual cert renewal).

### Image registry / build
- Build images locally on the Pi (or build on your dev machine for `linux/arm64`
  with `docker buildx`). No external registry required for v1.

### Backups
- **v1:** `litestream`-style or plain `sqlite3 .backup` to `./backups/`, rotated
  with a small bash script + cron.
- **v2 (AWS learning hook):** push encrypted backups to S3 with lifecycle rules
  to Glacier. Good excuse to learn IAM, S3, and `aws-cli`.

### Observability (light)
- App logs to stdout → Docker captures them.
- Add `loguru` for nicer Python logging. No Prometheus/Grafana for v1.

## External APIs

| Service | Purpose | Tier |
|---|---|---|
| **CoinGecko** | ETH spot price in your fiat | Free, no key needed (rate-limited) |
| **Etherscan** | ETH wallet balance for one address | Free with API key |

Both are wrapped behind a `services/crypto.py` module so they can be swapped
(e.g. for Alchemy or a self-hosted node) without touching the rest of the app.

## Dev environment

- **Editor:** whatever you prefer; the repo will ship a `.editorconfig` and a
  recommended VS Code workspace settings file.
- **Pre-commit hooks:** `ruff`, `mypy`, `prettier`, `eslint` via `pre-commit`.
- **CI:** GitHub Actions running lint + tests + a Docker build for `arm64`.
  (Nice-to-have, not blocking v1.)
- Full configs and the daily dev loop: [`08-dev-tooling.md`](08-dev-tooling.md).

## Summary table

| Layer | Choice | Why in one line |
|---|---|---|
| Backend lang | Python 3.12 | Owner's strongest language |
| Backend framework | FastAPI | Modern, typed, OpenAPI-native |
| ORM | SQLAlchemy 2 + Alembic | Industry standard, real migrations |
| DB | SQLite → Postgres later | Right-sized for one user |
| Scheduler | APScheduler | Cron jobs without extra services |
| Frontend | React + Vite + TS | Best AI-tool ergonomics |
| Styling | Tailwind + shadcn/ui | Component ownership, AI-friendly |
| Data fetching | TanStack Query | Standard, batteries-included |
| Container | Docker Compose | Right size for a Pi |
| Proxy | Caddy | Auto-HTTPS, tiny config |
| Backups | sqlite `.backup` + cron, optional S3 | Simple, testable |
