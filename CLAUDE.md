# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Fintrack is a financial tracker application with a FastAPI backend (`apps/api/`) and a frontend placeholder (`apps/web/`). Infrastructure lives in `infra/`.

## Design documents

Extended documentation lives outside this repo at:

```
/home/jabia/Documents/Obsidian/Projects/Financial-tracker/docs/
```

**This path may not exist on all machines.** If present, consult these files before writing or reviewing non-trivial code:

- `02-architecture.md` — system diagram, component responsibilities, CSV ingestion flow, Etherscan/CoinGecko integration points.
- `04-data-model.md` — all 7 DB tables with field types, constraints, currency handling, crypto wallet validation, and soft-delete semantics.
- `05-features.md` — MVP features F1–F8 with acceptance criteria; use as the definition of done when implementing or reviewing feature work.
- `09-developer-roadmap.md` — step-by-step implementation guide per phase; consult to understand what to build next and in what order.

The remaining files (`01-goals.md`, `03-tech-stack.md`, `06-deployment.md`, `07-roadmap.md`, `08-dev-tooling.md`) cover goals, tech-stack rationale, deployment, and tooling — useful for project-level decisions but not needed during routine coding sessions.

## Commands

All Python tooling uses `uv`. Run commands from the repo root unless noted.

```bash
# Install dependencies
uv sync

# Run the API dev server
uv run uvicorn apps.api.main:app --reload

# Lint
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy apps/

# Run tests
uv run pytest

# Run a single test file
uv run pytest apps/api/tests/path/to/test_file.py

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Architecture

**Monorepo** managed as a `uv` workspace (root `pyproject.toml` lists `apps/api` as a member). Python ≥ 3.14 required.

**Backend (`apps/api/`)** — FastAPI + SQLAlchemy (async) + aiosqlite + Alembic. Pydantic (with email) handles validation; pydantic-settings manages config. Uvicorn serves the ASGI app.

**Frontend (`apps/web/`)** — not yet scaffolded.

**Infrastructure (`infra/`)** — docker-compose and Caddyfile are placeholder files, not yet configured.

## Code style

- Ruff enforces rules E, F, I, UP, B, SIM at line length 88 (E501 ignored).
- MyPy runs in strict mode targeting Python 3.14.
- Tests use pytest with `asyncio_mode = "auto"` — all async tests work without explicit decorators.
